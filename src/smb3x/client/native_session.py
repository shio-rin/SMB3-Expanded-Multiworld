# SPDX-License-Identifier: MPL-2.0
"""Native mailbox transport/coordinator adapted to the existing AP watcher."""
from __future__ import annotations
import asyncio
import json
from copy import deepcopy
import logging
from pathlib import Path
from .transport import BridgeUnavailable, LuaBridge
from .persistence.world_journal import NativeJournal
from ..shared import location_signals
from ..shared.items import ITEMS

class NativeBridge(LuaBridge):

    def __init__(self, build: dict, state_dir: Path, *, port=43210, fatal=lambda: None, run, token):
        super().__init__(build, port=port, run=run, token=token)
        self.build, self.state_dir, self.fatal = (build, Path(state_dir), fatal)
        self.journal = None
        self.action = None
        self.authorized = False
        self.failure = None
        self.instance = None

    async def poll(self, session, pending, **kwargs):
        if self.failure:
            raise ValueError(self.failure)
        try:
            return await self._poll(session, pending, **kwargs)
        except BridgeUnavailable:
            raise
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.failure = str(exc)
            self.authorized = False
            self.fatal()
            await self.close()
            raise ValueError('Native integration stopped: ' + self.failure) from exc

    async def _poll(self, session, pending, **kwargs):
        if kwargs.get('hazards') != self.build['hazards']:
            raise ValueError('AP hazard assignments differ from the generated ROM')
        if kwargs.get('audiovisual') != self.build['audiovisual']:
            raise ValueError('AP song/palette assignments differ from the generated ROM')
        if kwargs.get('level_shuffle') != self.build['level_shuffle']:
            raise ValueError('AP stage assignments differ from the generated ROM')
        if kwargs.get('cosmetics') != self.build['cosmetics']:
            raise ValueError('AP cosmetic assignments differ from the generated ROM')
        if kwargs.get('progression_config') != self.build['progression']:
            raise ValueError('AP progression settings differ from the generated ROM')
        if kwargs.get('goal') != self.build['goal'] or session != self.build['session'] or kwargs.get('protocol') != 35:
            raise ValueError('AP session/protocol does not match generated ROM')
        if kwargs.get('location_ids') != sorted((int(r['id'], 16) for r in location_signals.profile_rows('m242', self.build['progression']))):
            raise ValueError('requires the eight-world profile')
        binding = location_signals.state_binding({'location_registry_sha256': kwargs['location_hash'], 'item_registry_sha256': kwargs['item_hash'], 'location_profile': 'm242', 'location_ids': kwargs['location_ids'], 'goal': kwargs['goal'], 'progression': self.build['progression'], 'level_shuffle': self.build['level_shuffle'], 'audiovisual': self.build['audiovisual'], 'hazards': self.build['hazards'], 'world_pass_placement': self.build.get('world_pass_placement'), 'placement_policy': self.build.get('placement_policy')})
        if self.journal is None:
            self.journal = NativeJournal(self.state_dir, session, self.build['output']['sha256'], binding, hammer_mode=self.build['progression']['hammer_mode'])
        elif self.journal.binding['registry'] != binding:
            raise ValueError('Native registry changed')
        request = {'type': 'SYNC', 'protocol': 36, 'session': session, 'goal': kwargs['goal'], 'commands': pending, 'handled': {str(k): v for k, v in kwargs['handled'].items()}, 'unlock_mask': kwargs['unlock_mask'], 'item_signature': kwargs['item_signature'], 'location_signature': kwargs['location_signature'], 'location_ids': kwargs['location_ids'], 'rom_sha256': self.build['output']['sha256'], 'patch_version': self.build['patch_version'], 'assignment_sha256': self.build['level_shuffle']['sha256'], 'audiovisual_sha256': self.build['audiovisual']['sha256'], 'hazard_sha256': self.build['hazards']['sha256'], 'native_authorized': self.authorized, 'bridge_instance': self.instance or self.journal.state.get('bridge_instance'), 'developer_connected': bool(kwargs.get('developer_connected', False)), 'native_action': self.action, 'notifications': kwargs.get('notifications', []) if self.authorized else []}
        view = kwargs.get('presentation')
        if view is not None:
            if view.get('session') != session or view.get('binding') != binding:
                raise ValueError('Presentation snapshot binding mismatch')
            request['presentation'] = {**view, 'rom': self.build['output']['sha256']} if self.authorized else None
        request['progression_config'] = self.build['progression']
        request['progression'] = kwargs['progression']
        response = await self.exchange(request)
        if response.get('rom_sha256') != self.build['output']['sha256'] or response.get('patch_version') != self.build['patch_version']:
            raise ValueError('Emulator ROM/patch identity mismatch')
        instance = response.get('bridge_instance')
        if not isinstance(instance, str) or not 1 <= len(instance) <= 128:
            raise ValueError('Missing Lua lifetime identity')
        old_instance = self.journal.state.get('bridge_instance')
        if old_instance is not None and instance != old_instance and any((ITEMS[c['item']]['kind'] != 'permanent' for c in pending)):
            raise ValueError('Lua restarted with pending consumables: RAM effects may be uncertain; preserve history, no automatic retry')
        previous_stage = (self.journal.state.get('pending') or {}).get('stage')
        previous_ending = self.journal.state['ending']['phase']
        self.action = self.journal.reconcile(response['native'])
        for phase, message in enumerate(('BOWSER DEFEATED', 'PEACH RESCUE ENTERED', 'ENDING TRANSITION CONFIRMED'), 1):
            if previous_ending < phase <= self.journal.state['ending']['phase']:
                logging.getLogger('SMB3').info('%s: native receipt v1, session %s', message, session[:12])
        self.authorized = response['native']['phase'] in (2, 3, 4, 5, 6, 7) and response['native']['bound'] == 1
        if self.authorized and response.get('inventory') is not None:
            from .inventory import reconcile as inventory_reconcile
            record = inventory_reconcile(self.journal.state.get('inventory'), response['inventory'], self.build['progression']['inventory_mode'], regional=self.build['progression']['hammer_mode'] == 'regional')
            if record != self.journal.state.get('inventory'):
                state = deepcopy(self.journal.state)
                state['inventory'] = record
                self.journal.save(state)
        if self.authorized and instance != old_instance:
            state = deepcopy(self.journal.state)
            state['bridge_instance'] = instance
            self.journal.save(state)
        self.instance = instance
        stage = (self.journal.state.get('pending') or {}).get('stage')
        if stage != previous_stage:
            logging.getLogger('SMB3').info('NATIVE journal %s; confirmed World %d, transaction %d', stage or 'released', self.journal.state['active'] + 1, self.journal.state['committed'])
        if not self.authorized:
            response['checks'], response['acks'] = ([], [])
        if self.authorized:
            from .persistence.snapshots import unseal
            checks = set(response.get('checks', []))
            if self.journal.state['ending']['phase'] >= 1:
                checks.update((i for i, r in location_signals.BY_ID.items() if r['kind'] == 'bowser'))
            for world, record in self.journal.state['worlds'].items():
                checks.update(location_signals.snapshot_checks(int(world), unseal(record)))
            pending_tx = self.journal.state.get('pending')
            if pending_tx:
                checks.update(location_signals.snapshot_checks(pending_tx['source'], unseal(pending_tx['source_state'])))
            response['checks'] = sorted(checks & set(kwargs['location_ids']))
        response['protocol'] = 35
        return response

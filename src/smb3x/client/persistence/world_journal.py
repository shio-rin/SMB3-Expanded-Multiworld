# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from ...shared.world_geometry import SUPPORTED, world_descriptor, validate_world_snapshot, map_section
from .snapshots import checksum, validate_snapshot, occupied, destination_snapshot, seal, unseal, MAX_SEQUENCE, ADDRESSES

class NativeJournal:

    def __init__(self, directory: Path, session: str, rom_sha256: str, registry: str, *, hammer_mode='regional'):
        if any((not isinstance(x, str) or len(x) != 64 or any((c not in '0123456789abcdef' for c in x)) for x in (session, rom_sha256, registry))):
            raise ValueError('Native journal requires full identity hashes')
        if hammer_mode not in ('legacy', 'regional'):
            raise ValueError('Unknown Hammer mode')
        self.hammer_mode = hammer_mode
        self.path = Path(directory) / (session + '.json')
        self.binding = {'schema': 9, 'session': session, 'rom_sha256': rom_sha256, 'registry': registry, 'hammer_mode': hammer_mode}
        self.existed = self.path.exists()
        if self.existed:
            state = json.loads(self.path.read_text(encoding='utf-8'))
            self.validate(state)
            self.state = state
        else:
            self.state = {**self.binding, 'active': 0, 'sequence': 0, 'committed': 0, 'worlds': {}, 'pending': None, 'ending': {'version': 1, 'phase': 0}}

    def validate(self, state):
        if any((state.get(k) != v for k, v in self.binding.items())):
            raise ValueError('Native journal identity/version/ROM/registry mismatch')
        inventory = state.get('inventory')
        if inventory is not None:
            from ..inventory import reconcile
            reconcile(inventory, inventory['snapshot'], inventory['snapshot']['mode'])
        ending = state.get('ending')
        if not isinstance(ending, dict) or set(ending) != {'version', 'phase'} or ending['version'] != 1 or (type(ending['phase']) is not int) or (ending['phase'] not in range(4)):
            raise ValueError('Invalid native ending receipt')
        instance = state.get('bridge_instance')
        if instance is not None and (not isinstance(instance, str) or not 1 <= len(instance) <= 128):
            raise ValueError('Invalid Lua lifetime identity')
        if state.get('active') not in SUPPORTED or any((type(state.get(k)) is not int or not 0 <= state[k] <= MAX_SEQUENCE for k in ('sequence', 'committed'))):
            raise ValueError('Invalid journal counter/world')
        worlds = state.get('worlds')
        if not isinstance(worlds, dict) or set(worlds) - {str(w) for w in SUPPORTED}:
            raise ValueError('Invalid world map')
        for world, record in worlds.items():
            validate_world_snapshot(int(world), unseal(record))
        pending = state.get('pending')
        if pending is not None:
            if not isinstance(pending, dict) or pending.get('source') not in SUPPORTED or pending.get('destination') not in SUPPORTED or (type(pending.get('tx')) is not int) or (not 1 <= pending['tx'] <= MAX_SEQUENCE) or (pending.get('stage') not in ('prepared', 'restoring', 'commit_saved')):
                raise ValueError('Invalid pending transaction')
            source = unseal(pending['source_state'])
            validate_world_snapshot(pending['source'], source)
            reason = pending.get('reason', 0)
            if reason not in (0, 1, 2) or (pending['source'] == pending['destination']) != (reason in (1, 2)):
                raise ValueError('Invalid airship transaction reason')
            if reason == 2 and (pending['source'] != 7 or ending['phase'] != 3):
                raise ValueError('Post-ending continuation requires confirmed W8 ending')
            if reason == 1 and (not source['data'][-1] & 1):
                raise ValueError('Airship return lacks native completion receipt')
            if pending.get('target') is not None:
                validate_world_snapshot(pending['destination'], unseal(pending['target']))

    def save(self, state):
        self.validate(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        from .atomic import save_json
        save_json(self.path, state)
        self.state = deepcopy(state)
        self.existed = True

    def reconcile(self, status):
        """Persist before returning a command authorizing any destructive step."""
        if status.get('session') != self.binding['session']:
            raise ValueError('Native status session mismatch')
        for key in ('seen', 'sequence', 'transaction'):
            if type(status.get(key)) is not int or not 0 <= status[key] <= MAX_SEQUENCE:
                raise ValueError('Malformed native counter')
        for key in ('phase', 'world', 'active', 'bound', 'error'):
            if type(status.get(key)) is not int or not 0 <= status[key] <= 255:
                raise ValueError('Malformed native status')
        phase, seq = (status['phase'], status['seen'])
        if phase == 255 or status['error']:
            raise ValueError(f"ROM requires recovery: error {status['error']}; preserve journal")
        if phase not in (0, 1, 2, 3, 4, 5, 6, 7) or status['world'] not in SUPPORTED:
            raise ValueError('Unsupported ROM lifecycle/world')
        if seq < self.state['sequence']:
            raise ValueError('ROM sequence rollback/reset; no automatic recovery')
        if phase in (0, 1) and self.existed:
            raise ValueError('Fresh ROM/reset cannot attach to existing native history')
        if phase == 0:
            return None
        if status['sequence'] != seq:
            return None
        state = deepcopy(self.state)
        state['sequence'] = seq
        ep, ev = (status.get('ending_phase'), status.get('ending_version'))
        if type(ep) is not int or ep not in range(4) or type(ev) is not int or (ev != (1 if ep else 0)):
            raise ValueError('Native ending receipt version/phase mismatch')
        if ep < state['ending']['phase']:
            raise ValueError('Native ending receipt rollback')
        if ep and (not status['bound']):
            raise ValueError('Unbound ending receipt')
        state['ending']['phase'] = ep
        pending = state['pending']
        action = None
        if phase == 1:
            return {'op': 1, 'sequence': seq + 1, 'phase': phase, 'transaction': status['transaction'], 'session': self.binding['session']} if not status['bound'] else None
        if not status['bound']:
            raise ValueError('Game not bound to the expected session')
        if phase == 2:
            if status['world'] != state['active'] or status['active'] != state['active']:
                raise ValueError('Committed world differs from native journal')
            if pending:
                if pending['stage'] != 'commit_saved' or status['transaction'] != pending['tx']:
                    raise ValueError('Uncommitted transaction cannot resume control')
                state['pending'] = None
            elif status['transaction'] != state['committed']:
                raise ValueError('Native completed transaction differs from journal')
            if status.get('snapshot') is not None:
                snapshot = validate_snapshot(status['snapshot'])
                if not occupied(snapshot['data'], snapshot['point']):
                    state['worlds'][str(state['active'])] = seal(snapshot)
        elif phase == 3:
            tx, world, dest = (status['transaction'], status['world'], status.get('destination'))
            reason = status.get('reason', 0)
            if world != state['active'] or dest not in SUPPORTED or (dest == world and reason not in (1, 2)):
                raise ValueError('Invalid source/destination handoff')
            if reason == 2 and (dest != world or world != 7 or ep != 3):
                raise ValueError('Invalid post-ending continuation')
            if pending is None:
                if tx != seq or tx <= state['committed']:
                    raise ValueError('Stale or mismatched native transaction')
                source = validate_snapshot(status['snapshot'])
                validate_world_snapshot(world, source)
                if dest == world and reason == 1 and (not source['data'][-1] & 1):
                    raise ValueError('Airship return lacks native completion receipt')
                if seq > MAX_SEQUENCE - 3:
                    raise ValueError('Insufficient command lifetime for transaction')
                if occupied(source['data'], source['point']):
                    raise ValueError('Source position is not safe')
                target = seal(source) if dest == world else state['worlds'].get(str(dest))
                if target:
                    target = seal(destination_snapshot(dest, unseal(target), self.hammer_mode))
                pending = {'reason': reason if dest == world else 0, 'tx': tx, 'source': world, 'destination': dest, 'stage': 'prepared', 'source_state': seal(source), 'target': target}
                state['pending'] = pending
            elif pending['tx'] != tx or pending['stage'] != 'prepared':
                raise ValueError('Conflicting source transaction')
            elif validate_snapshot(status['snapshot']) != unseal(pending['source_state']):
                raise ValueError('Frozen source changed during transaction')
            action = {'op': 4}
        elif phase in (4, 5, 6, 7):
            if pending is None or pending['tx'] != status['transaction']:
                raise ValueError('Transition lacks durable source transaction')
            if phase in (5, 6, 7) and status['world'] != pending['destination']:
                raise ValueError('Unexpected destination world')
            if phase == 6 and pending['stage'] != 'restoring':
                raise ValueError('Native loading without prepared restore')
            if phase == 5:
                if pending['stage'] == 'commit_saved':
                    raise ValueError('Destination rollback after commit')
                if pending['target'] is None:
                    pending['target'] = seal(destination_snapshot(status['world'], status['snapshot'], self.hammer_mode))
                pending['stage'] = 'restoring'
                action = {'op': 5, 'snapshot': unseal(pending['target'])}
            elif phase == 7:
                current = validate_snapshot(status['snapshot'])
                if pending['target'] is None or current != unseal(pending['target']):
                    raise ValueError('Native destination differs from prepared state')
                state['worlds'][str(pending['source'])] = pending['source_state']
                state['worlds'][str(pending['destination'])] = seal(current)
                state['active'] = pending['destination']
                state['committed'] = pending['tx']
                pending['stage'] = 'commit_saved'
                action = {'op': 6}
        if state != self.state or not self.existed:
            self.save(state)
        if action:
            action.update(sequence=seq + 1, phase=phase, transaction=status['transaction'], session=self.binding['session'])
        return action

# SPDX-License-Identifier: MPL-2.0
"""Archipelago connection identity, indexed replay and owned protocol callbacks."""

from __future__ import annotations
from ..shared.resources import RESOURCE_ROOT
import argparse
import asyncio
from hashlib import sha1
import json
import logging
import os
from pathlib import Path
import sys
import time
from .notifications import Notifications
from .presentation import snapshot as presentation_snapshot
from .transport import BridgeUnavailable, LuaBridge
from ..shared.location_signals import TERMINAL_IDS as LOCATION_IDS, REGISTRY_SHA256

ITEM_ID = 0x534D3381
from .persistence.receipts import DeliveryState, Identity, StateStore, new_location_checks
from ..shared import location_signals
from ..shared.items import ITEMS, ITEM_REGISTRY_SHA256, ITEM_SIGNATURE

ROOT = RESOURCE_ROOT
GAME = 'Super Mario Bros. 3: Expanded Multiworld'
ROM_SHA1 = 'BB894D104C796F69BA16587EB66C0275F5C2FC02'
LOG = logging.getLogger('SMB3X')
import Utils
import warnings

warnings.filterwarnings('ignore', message='_speedups not available.*', category=UserWarning)
from CommonClient import CommonContext, server_loop
from NetUtils import ClientStatus


def verify_local_rom(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 16 or data[:4] != b'NES\x1a':
        raise ValueError('Expected an iNES ROM')
    start = 16 + (512 if data[6] & 4 else 0)
    end = start + data[4] * 16384 + data[5] * 8192
    if end > len(data) or sha1(data[start:end]).hexdigest().upper() != ROM_SHA1:
        raise ValueError('Local ROM does not match verified SMB3 USA PRG1 payload')


def validate_connected_identity(ctx: 'SMB3Context', slot_data: dict) -> Identity:
    """Reject foreign owners and plans before loading or mutating delivery history."""
    if ctx.server_seed_name != ctx.expected_seed:
        raise ValueError(f'Wrong seed: expected {ctx.expected_seed}, got {ctx.server_seed_name}')
    if ctx.slot is None or ctx.team is None:
        raise ValueError('Server did not provide team and slot')
    slot = ctx.slot_info[ctx.slot]
    if slot.name != ctx.requested_slot or slot.game != GAME:
        raise ValueError(
            f'Wrong slot: expected {ctx.requested_slot} ({GAME}), got {slot.name} ({slot.game})'
        )
    if (slot_data.get('game'), slot_data.get('namespace'), slot_data.get('identity_contract')) != (
        GAME,
        'smb3x',
        'smb3x-fresh-1',
    ):
        raise ValueError(
            'Not a fresh SMB3X slot; historical SMB3 sessions require their original installation'
        )
    protocol = slot_data.get('bridge_protocol')
    registry_hash = location_signals.REGISTRY_SHA256 if protocol == 35 else REGISTRY_SHA256
    if (
        protocol not in (35,)
        or slot_data.get('rom_payload_sha1') != ROM_SHA1
        or slot_data.get('location_registry_sha256') != registry_hash
    ):
        raise ValueError('Slot data is not the SMB3 protocol/ROM/location registry')
    if protocol in (35,) and slot_data.get('item_registry_sha256') != ITEM_REGISTRY_SHA256:
        raise ValueError('Slot data item registry mismatch')
    if protocol == 35 and slot_data.get('location_ids') != [
        int(row['id'], 16)
        for row in location_signals.profile_rows(
            slot_data.get('location_profile'), slot_data.get('progression')
        )
    ]:
        raise ValueError('enabled location set mismatch')
    if slot_data.get('location_contract') != 'm242-victory-only-1' or slot_data.get(
        'enabled_location_ids'
    ) != slot_data.get('location_ids'):
        raise ValueError('Victory-only location contract mismatch')
    from ..shared.victory import validate_goal
    from ..shared.progression import validate

    if validate(slot_data.get('progression')) != slot_data.get('progression'):
        raise ValueError('Invalid seed-bound progression settings')
    from ..planning.cosmetics import assignments

    plan = slot_data.get('cosmetics')
    if not isinstance(plan, dict) or plan != assignments(
        ctx.server_seed_name, plan.get('settings')
    ):
        raise ValueError('Invalid seed-bound cosmetic assignments')
    from ..planning.stages import validate as validate_shuffle

    validate_shuffle(slot_data.get('level_shuffle'), ctx.server_seed_name)
    from ..planning.audiovisual import validate as validate_av, fingerprint

    av = slot_data.get('audiovisual')
    if (
        not isinstance(av, dict)
        or validate_av(av.get('settings')) != av.get('settings')
        or av.get('sha256') != fingerprint({k: v for k, v in av.items() if k != 'sha256'})
    ):
        raise ValueError('Invalid audiovisual assignment identity')
    # Old player files dispatch to their hash-bound runtime before reaching this client.
    # Every validation below is mandatory for this one accepted slot release.
    release = slot_data.get('release')
    if release != 'm27-1':
        raise ValueError('Unsupported seed-bound release identity; use its matching cached runtime')
    from ..planning.hazards import plan as hazard_plan

    hazard = slot_data.get('hazards')
    if (
        not isinstance(hazard, dict)
        or set(hazard.get('settings', {})) != {'poison_mushrooms', 'angry_sun'}
        or hazard
        != hazard_plan(
            ctx.server_seed_name,
            slot_data['level_shuffle'],
            hazard['settings']['poison_mushrooms'],
            hazard['settings']['angry_sun'],
        )
    ):
        raise ValueError('Invalid seed-bound hazard assignments')
    if (
        slot_data.get('foundation_contract') != 'm25-foundation-ui-audio-1'
        or slot_data.get('sfx_restoration_contract') != 'm244-sfx-resume-1'
    ):
        raise ValueError('Foundation audio contract mismatch')
    if slot_data.get('interface_contract') != 'm245-compact-travel-desk-1':
        raise ValueError('Invalid interface contract')
    if (
        slot_data.get('trap_warning') not in ('show', 'hide')
        or slot_data.get('presentation_contract') != 'm251-presentation-1'
    ):
        raise ValueError('Invalid presentation contract')
    if (
        getattr(ctx, 'expected_trap_warning', slot_data['trap_warning'])
        != slot_data['trap_warning']
    ):
        raise ValueError('Server trap warning differs from prepared file')
    if hasattr(ctx, 'notifications'):
        ctx.notifications.trap_warning = slot_data['trap_warning']
    from ..shared import effects as effect_contract

    effect_contract.validate_settings(slot_data.get('effects'))
    expected = getattr(ctx, 'expected_effects', None)
    if expected is not None and expected != slot_data['effects']:
        raise ValueError('Server effects differ from prepared game')
    validate_goal(slot_data.get('goal'))
    selection = slot_data.get('r3_music', {})
    from ..planning.music import plan as music

    if selection != music(
        ctx.server_seed_name,
        slot_data['level_shuffle'],
        slot_data['cosmetics'],
        selection.get('mode'),
        selection.get('reserves'),
        selection.get('requested_tracks'),
    ):
        raise ValueError('Invalid R3 music assignment identity')
    expected = getattr(ctx, 'expected_r3_music', None)
    if expected is not None and expected != selection:
        raise ValueError('Server private music selection differs from prepared game')
    expected = getattr(ctx, 'expected_special_palettes', None)
    if expected is not None and expected != slot_data.get('special_palette_selection'):
        raise ValueError('Server special palettes differ from prepared game')
    expected_palette = getattr(ctx, 'expected_palette_selection', None)
    if expected_palette is not None:
        expected_release = getattr(ctx, 'expected_release', None)
        if (
            slot_data.get('release') != expected_release
            or slot_data.get('m242_palettes') != expected_palette
        ):
            raise ValueError('Server palette/release identity differs from this player file')
    expected_placement = getattr(ctx, 'expected_placement', None)
    if expected_placement is not None and expected_placement != [
        slot_data.get('world_pass_placement'),
        slot_data.get('placement_policy'),
    ]:
        raise ValueError('Server final placement policy differs from this player file')
    if slot_data.get('ending_receipt_version') != 1:
        raise ValueError('Unsupported native ending receipt')
    return Identity(ctx.server_seed_name, ctx.team, ctx.slot)


class SMB3Context(CommonContext):
    game = GAME
    items_handling = 7
    want_slot_data = True

    def __init__(self, address: str, password: str | None, slot: str, seed: str, store: StateStore):
        install_deathlink_dispatch()
        super().__init__(address, password)
        self.requested_slot = slot
        self.username = slot
        self.expected_seed = seed
        self.store = store
        self.identity: Identity | None = None
        self.delivery: DeliveryState | None = None
        self.validation_error: str | None = None
        self.logged_registered: set[int] = set()
        self.notifications = Notifications()
        self.goal = None
        self.goal_confirmed = False
        self.goal_status_requested = False
        self.bridge_protocol = 35
        self.location_ids = LOCATION_IDS
        self.smb3_location_names = {i: row["name"] for i, row in location_signals.BY_ID.items()}
        self.persistence = None
        self.replay_ready = False
        self.connection_generation = 0
        self.replay_token = None
        self.replay_seen = False
        self.replay_gap = False
        self.received_inbox_prefix = []
        self.death_inbox = []
        self.death_send_key = None

    def on_deathlink(self, data):
        from .deathlink import payload

        now = time.time()
        valid = payload(data, now)
        if not valid or not getattr(self, 'expected_effects', {}).get('death_link', False):
            return
        if self.identity is None or not self.persistence:
            return
        self.death_inbox.append((valid, now, time.monotonic()))

    async def send_msgs(self, msgs):
        # CommonClient replays finished_game inside Connected, before our
        # identity/history callback. Only the validated watcher may send a goal.
        msgs = [m for m in msgs if not (
            m.get('cmd') == 'StatusUpdate' and m.get('status') == ClientStatus.CLIENT_GOAL
        )]
        for message in msgs:
            if message.get('cmd') == 'Bounce' and 'DeathLink' in message.get('tags', []):
                if not self.death_send_key or not getattr(self, 'expected_effects', {}).get(
                    'death_link', False
                ):
                    raise ValueError('DeathLink publication without managed native send intent')
                self.persistence.outgoing_packet(self.death_send_key, message['data'])
        if msgs:
            await super().send_msgs(msgs)

    async def send_goal(self, identity, delivery, generation):
        """Watcher-only transport after durable goal/publication validation."""
        def owned():
            return (self.identity == identity and self.delivery is delivery
                    and self.connection_generation == generation and self.replay_ready
                    and not self.validation_error and self.persistence
                    and not self.persistence.initial and not self.persistence.closed)
        if not owned():
            return False
        await super().send_msgs([{'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_GOAL}])
        return bool(owned())

    def request_replay(self):
        import uuid

        token = uuid.uuid4().hex
        generation = self.connection_generation
        self.replay_token = token
        self.replay_ready = False
        self.replay_seen = False
        self.replay_gap = False

        async def send_barrier():
            if self.connection_generation == generation and self.replay_token == token:
                await self.send_msgs(
                    [
                        {'cmd': 'Sync'},
                        {
                            'cmd': 'Get',
                            'keys': [],
                            'm232_replay_token': token,
                            'm232_connection_generation': generation,
                        },
                    ]
                )

        asyncio.create_task(send_barrier())

    async def server_auth(self, password_requested: bool = False):
        if password_requested and (not self.password):
            self.validation_error = 'Room password required'
            LOG.error(self.validation_error)
            self.exit_event.set()
            return
        self.auth = self.requested_slot
        await self.update_death_link(
            bool(getattr(self, 'expected_effects', {}).get('death_link', False))
        )
        await self.send_connect()

    async def connection_closed(self):
        self.replay_ready = False
        self.replay_token = None
        self.replay_seen = False
        self.replay_gap = False
        await super().connection_closed()

    def on_package(self, cmd: str, args: dict) -> None:
        if cmd == 'RoomInfo' and self.server_seed_name != self.expected_seed:
            self.validation_error = (
                f'Wrong seed: expected {self.expected_seed}, got {self.server_seed_name}'
            )
            self.identity = None
            self.delivery = None
            LOG.error(self.validation_error)
            self.exit_event.set()
        elif cmd == 'Connected':
            self.replay_ready = False
            self.connection_generation += 1
            if self.persistence and self.persistence.busy:
                self.validation_error = (
                    'Connection identity changed during checkpoint; preserved frozen candidate'
                )
                self.exit_event.set()
                return
            try:
                identity = validate_connected_identity(self, args.get('slot_data') or {})
                self.goal = args['slot_data']['goal']
                self.progression_config = args['slot_data']['progression']
                self.cosmetics = args['slot_data']['cosmetics']
                self.level_shuffle = args['slot_data']['level_shuffle']
                self.audiovisual = args['slot_data']['audiovisual']
                self.hazards = args['slot_data']['hazards']
                self.goal_status_requested = False
                self.bridge_protocol = args['slot_data']['bridge_protocol']
                self.location_ids = (
                    frozenset(args['slot_data']['location_ids'])
                    if self.bridge_protocol == 35
                    else LOCATION_IDS
                )
                self.smb3_location_names = (
                    {i: row['name'] for i, row in location_signals.BY_ID.items()}
                    if self.bridge_protocol == 35
                    else {i: row["name"] for i, row in location_signals.BY_ID.items()}
                )
                prior_checks = set(args.get('checked_locations', ())) | set(self.checked_locations)
                if prior_checks and (not self.store.path_for(identity).is_file()):
                    raise ValueError(
                        'This slot already has server checks but its local delivery history is missing. Preserve the original package/runtime; do not reuse this room as fresh.'
                    )
                loaded = self.store.load(identity)
                if self.identity == identity and self.delivery is not None:
                    if loaded.as_dict() != self.delivery.as_dict():
                        raise ValueError('Live delivery history changed during AP reconnect')
                else:
                    self.delivery = loaded
                self.delivery.bind_registry(
                    (
                        location_signals.state_binding(args['slot_data'])
                        if self.bridge_protocol == 35
                        else args['slot_data']['location_registry_sha256']
                    ),
                    require_bound_history=self.bridge_protocol == 35,
                )
                if self.bridge_protocol in (35,) and (
                    not set(self.delivery.pending) | set(self.delivery.handled)
                    <= set(self.delivery.items)
                ):
                    raise ValueError(
                        'Untyped legacy delivery history: use a fresh seed, not an old seed name'
                    )
                self.store.save(self.delivery)
                self.identity = identity
                self.validation_error = None
                # Submission is not confirmation. A fresh connection may
                # reassert a durably authorized goal if its reply was lost.
                if not self.goal_confirmed:
                    self.finished_game = False
                self.logged_registered = set(self.checked_locations)
                self.notifications.connected(
                    self.checked_locations, known_count=len(self.delivery.items)
                )
                LOG.info(
                    'Connected: seed=%s team=%d slot=%d (%s); pending=%d handled=%d',
                    identity.seed,
                    identity.team,
                    identity.slot,
                    self.requested_slot,
                    len(self.delivery.pending),
                    len(self.delivery.handled),
                )
                LOG.info('Items handling: 0b111 (own and other worlds)')
                LOG.info(
                    'Server already checked: %s',
                    sorted(
                        (
                            self.smb3_location_names[location]
                            for location in self.checked_locations
                            if location in self.smb3_location_names
                        )
                    ),
                )
                self.request_replay()
            except (ValueError, OSError) as exc:
                self.validation_error = str(exc)
                self.identity = None
                self.delivery = None
                LOG.error('Identity rejected: %s', exc)
                self.exit_event.set()
        elif cmd == 'ReceivedItems':
            if args.get('index') == 0:
                self.replay_seen = True
                self.replay_gap = False
            elif not self.replay_seen or args.get('index') != len(self.items_received) - len(
                args.get('items', [])
            ):
                self.replay_ready = False
                self.replay_gap = True
                self.request_replay()
            self.cosmetic(
                lambda: self.notifications.items(
                    self.items_received,
                    lambda code: self.item_names.lookup_in_slot(code, self.slot),
                    self.player_name,
                )
            )
            LOG.info(
                'ReceivedItems packet: start=%s count=%d; total cached=%d',
                args.get('index'),
                len(args.get('items', [])),
                len(self.items_received),
            )
            if (
                self.identity
                and self.replay_ready
                and self.replay_seen
                and (not self.replay_gap)
                and getattr(self, 'persistence', None)
            ):
                try:
                    from .persistence.checkpoints import validate_prefix
                    from .persistence.atomic import save_json

                    incoming = [list(item) for item in self.items_received]
                    validate_prefix(self.persistence.known_received, incoming)
                    validate_prefix(self.received_inbox_prefix, incoming)
                    save_json(
                        self.store.directory / 'received-inbox.json',
                        dict(
                            schema=1,
                            identity=self.identity.as_dict(),
                            run=self.persistence.run,
                            received=incoming,
                        ),
                    )
                    self.received_inbox_prefix = incoming
                except (ValueError, OSError) as exc:
                    self.validation_error = 'Received-item inbox failed: ' + str(exc)
                    LOG.error(self.validation_error)
                    self.exit_event.set()
        elif cmd == 'RoomUpdate':
            for location in args.get('checked_locations', []):
                if location in self.smb3_location_names and location not in self.logged_registered:
                    LOG.info(
                        'Server registered %s (%d)', self.smb3_location_names[location], location
                    )
                    self.logged_registered.add(location)
                    self.cosmetic(
                        lambda: self.notifications.confirmed(
                            location, self.smb3_location_names[location]
                        )
                    )
        elif cmd == 'ConnectionRefused':
            self.validation_error = 'Room connection refused: ' + ', '.join(
                map(str, args.get('errors', []))
            )
            LOG.error(self.validation_error)
            self.exit_event.set()
        elif cmd in ('Retrieved', 'SetReply') and self.identity:
            if (
                cmd == 'Retrieved'
                and self.replay_token is not None
                and (args.get('m232_replay_token') == self.replay_token)
                and (args.get('m232_connection_generation') == self.connection_generation)
            ):
                if self.replay_gap:
                    self.request_replay()
                else:
                    if not self.replay_seen:
                        self.items_received = []
                    self.replay_ready = True
                    self.replay_token = None
                    LOG.info(
                        'Authoritative received-history barrier: %d items', len(self.items_received)
                    )
            key = f'_read_client_status_{self.team}_{self.slot}'
            value = (
                args.get('keys', {}).get(key)
                if cmd == 'Retrieved'
                else args.get('value') if args.get('key') == key else None
            )
            if value == ClientStatus.CLIENT_GOAL and (not self.goal_confirmed):
                self.goal_confirmed = True
                LOG.info('AP GOAL CONFIRMED: server client-status record for this team/slot')

    def player_name(self, slot):
        return self.player_names.get(slot, 'Player ' + str(slot))

    def cosmetic(self, fn):
        try:
            return fn()
        except Exception as exc:
            LOG.debug('Cosmetic event skipped: %s', exc)

    def on_print_json(self, args):
        super().on_print_json(args)
        if (
            self.identity
            and args.get('type') == 'Goal'
            and (args.get('team') == self.team)
            and (args.get('slot') == self.slot)
        ):
            self.goal_confirmed = True
            LOG.info('AP GOAL CONFIRMED: server Goal broadcast for this team/slot')
        if self.identity and args.get('type') == 'ItemSend':
            self.cosmetic(
                lambda: self.notifications.send(
                    args['item'],
                    args['receiving'],
                    self.slot,
                    self.item_names.lookup_in_slot,
                    self.player_name,
                )
            )


def install_deathlink_dispatch():
    """Narrowly validate this context's Bounce payload before AP's timestamp hook."""
    import CommonClient

    previous = CommonClient.process_server_cmd
    if getattr(previous, '_smb3x_owner', None) is SMB3Context:
        return

    async def dispatch(ctx, args):
        if isinstance(ctx, SMB3Context) and isinstance(args, dict) and args.get('cmd') == 'Bounced':
            tags = args.get('tags')
            if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
                return
            if 'DeathLink' in tags:
                ctx.on_deathlink(args.get('data'))
                return
        await previous(ctx, args)

    dispatch._smb3x_owner = SMB3Context
    CommonClient.process_server_cmd = dispatch

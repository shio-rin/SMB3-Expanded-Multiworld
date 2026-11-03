# SPDX-License-Identifier: MPL-2.0
"""Terminal authority and storage faults. State payload here is mocked."""
import json
import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
import tests.test_checkpoints as checkpoints
from smb3x.client.persistence.checkpoints import CheckpointStore, read
from smb3x.client.persistence.coordinator import Coordinator
from smb3x.shared.victory import satisfied


class TerminalEndingTests(unittest.TestCase):
    setUp = checkpoints.AutoCheckpointTests.setUp
    candidate = checkpoints.AutoCheckpointTests.candidate
    publish = checkpoints.AutoCheckpointTests.publish

    def ready(self):
        p = self.publish()
        self.store.activate_checkpoint(self.run, p['generation'])
        return dict(session=self.identity.key, phase=2, bound=1, error=0, world=7,
                    ending_phase=3, ending_version=1, sequence=1, seen=1, transaction=0)

    def test_goal_only_record_survives_cold_resume_without_rewriting_native_state(self):
        native = self.ready()
        before = self.store.verify()[2]
        record = self.store.persist_terminal_ending(self.run, native, [], [], [])
        self.assertEqual(self.store.verify()[2], before)
        run, _, _, _, components = self.store.resume()
        self.store.activate(run)
        coordinator = Coordinator(self.store, run, components)
        bridge = SimpleNamespace(journal=SimpleNamespace(state=components['worlds']))
        self.assertIsNone(coordinator.goal_ending(bridge))
        coordinator.initial = False
        self.assertEqual(coordinator.goal_ending(bridge), record['ending'])
        self.assertEqual(components['worlds']['ending'], {'version': 1, 'phase': 0})
        self.assertEqual(coordinator.saved_physical, set())

    def test_room_entry_defeat_peach_wrong_owner_and_write_flight_do_not_qualify(self):
        native = self.ready()
        for key, value in [('ending_phase', 0), ('ending_phase', 1), ('ending_phase', 2),
                           ('ending_version', 0), ('phase', 3), ('world', 0),
                           ('bound', 0), ('session', 'a'*64), ('seen', 0), ('error', 1)]:
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    self.store.persist_terminal_ending(self.run, {**native, key: value}, [], [], [])
                self.assertFalse((self.store.root/'ENDING.json').exists())
        with self.assertRaises(ValueError):
            self.store.persist_terminal_ending('b'*32, native, [], [], [])
        with self.assertRaises(ValueError):
            self.store.persist_terminal_ending(self.run, native, [], [0x534D3301], [])

    def test_failed_or_uncertain_write_never_returns_success(self):
        native = self.ready()
        with patch('smb3x.client.persistence.checkpoints.save_json', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.store.persist_terminal_ending(self.run, native, [], [], [])
        self.assertIsNone(self.store.terminal_ending())
        with patch.object(self.store, 'terminal_ending', side_effect=[None, None]):
            with self.assertRaises(ValueError):
                self.store.persist_terminal_ending(self.run, native, [], [], [])

    def test_corrupt_foreign_and_changed_ancestor_records_reject(self):
        self.store.persist_terminal_ending(self.run, self.ready(), [], [], [])
        path = self.store.root/'ENDING.json'
        original = path.read_bytes()
        for key, value in [('binding','f'*64), ('checkpoint', {}),
                           ('ending', {'version':1,'phase':2}), ('physical',[0x534D3301])]:
            with self.subTest(key=key):
                record = json.loads(original);record[key] = value
                path.write_text(json.dumps(record))
                with self.assertRaises(ValueError):self.store.terminal_ending()
        path.write_bytes(original)
        folder = self.store.verify()[0]
        (folder/'server.json').write_text('{"schema":1,"received":[[1,2,3,4]]}')
        with self.assertRaises(ValueError):self.store.terminal_ending()

    def test_goal_prerequisites_remain_required(self):
        evidence = {'version':1,'phase':3}
        airships = set(range(7));enabled = set(range(10))
        self.assertTrue(satisfied('standard', evidence, set(), enabled, airships))
        self.assertFalse(satisfied('all_koopalings', evidence, set(range(6)), enabled, airships))
        self.assertTrue(satisfied('all_koopalings', evidence, airships, enabled, airships))
        self.assertFalse(satisfied('all_locations', evidence, set(range(9)), enabled, airships))
        self.assertTrue(satisfied('all_locations', evidence, enabled, enabled, airships))
        for phase in (0,1,2):
            self.assertFalse(satisfied('standard', {'version':1,'phase':phase}, enabled, enabled, airships))

    def test_coordinator_requires_authenticated_idle_owner_and_durable_write(self):
        native = self.ready()
        coordinator = Coordinator(self.store, self.run, self.store.verify()[2])
        coordinator.initial = False
        state = SimpleNamespace(physical_checks=[], as_dict=lambda: {})
        ctx = SimpleNamespace(identity=self.identity, delivery=state, items_received=[],
                              checked_locations=set(), connection_generation=1, validation_error=None)
        bridge = SimpleNamespace(authorized=True, action=None, control=AsyncMock(),
                                 journal=SimpleNamespace(state={'ending': {'version':1,'phase':3}, 'pending':None}))
        response = dict(native=native, checkpoint_mode='playing', checkpoint_frozen=False,
                        checkpoint_delivery_flight=False, checkpoint_awaiting_ack=False,
                        checkpoint_batch_count=0, blocked=False)
        for field, value in [('checkpoint_mode','restoring'), ('checkpoint_mode','quiescing'),
                             ('checkpoint_frozen',True), ('checkpoint_delivery_flight',True),
                             ('checkpoint_awaiting_ack',True), ('checkpoint_batch_count',1),
                             ('blocked',True)]:
            with self.subTest(field=field):
                asyncio.run(coordinator.after_poll(ctx, bridge, self.identity, state, {**response,field:value}))
                self.assertIsNone(coordinator.saved_terminal)
                self.assertFalse((self.store.root/'ENDING.json').exists())
        bridge.authorized = False
        asyncio.run(coordinator.after_poll(ctx, bridge, self.identity, state, response))
        self.assertIsNone(coordinator.saved_terminal)
        bridge.authorized = True
        with patch.object(self.store, 'persist_terminal_ending', side_effect=OSError('uncertain disk write')):
            with self.assertRaises(OSError):
                asyncio.run(coordinator.after_poll(ctx, bridge, self.identity, state, response))
        self.assertIsNone(coordinator.saved_terminal)
        asyncio.run(coordinator.after_poll(ctx, bridge, self.identity, state, response))
        self.assertEqual(coordinator.goal_ending(bridge), {'version':1,'phase':3})

    def test_resume_rejects_corrupt_terminal_before_changing_epoch(self):
        self.store.persist_terminal_ending(self.run, self.ready(), [], [], [])
        before = self.store.epochs.read_bytes()
        (self.store.root/'ENDING.json').write_text('{}')
        with self.assertRaises(ValueError):self.store.resume()
        self.assertEqual(self.store.epochs.read_bytes(), before)

    def test_terminal_survives_later_checkpoint_and_rejects_truncated_replay(self):
        self.store.persist_terminal_ending(self.run, self.ready(), [[1,2,3,0]], [], [])
        self.publish()
        coordinator = Coordinator(self.store, self.run, self.store.verify()[2])
        self.assertEqual(coordinator.known_received, [[1,2,3,0]])
        ctx = SimpleNamespace(identity=self.identity, replay_ready=True, items_received=[])
        with self.assertRaisesRegex(ValueError, 'truncated'):
            asyncio.run(coordinator.before_poll(ctx, SimpleNamespace()))

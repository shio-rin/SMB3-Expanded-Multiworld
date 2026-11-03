# SPDX-License-Identifier: MPL-2.0
"""Execute production context methods without the external AP installation."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest


class GoalTransportTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] /
                          'src/smb3x/client/network.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SMB3Context')
        cls.body = [n for n in cls.body if isinstance(n, ast.AsyncFunctionDef)
                    and n.name in ('send_msgs', 'send_goal')]
        packets = self.packets = []

        class Base:
            async def send_msgs(inner, messages):
                packets.extend(messages)
                if getattr(inner, 'reconnect_during_send', False):
                    inner.connection_generation += 1

        scope = dict(CommonContext=Base, ClientStatus=SimpleNamespace(CLIENT_GOAL=30))
        exec(compile(ast.Module(body=[cls], type_ignores=[]), '<production goal transport>', 'exec'), scope)
        self.ctx = scope['SMB3Context']()
        self.ctx.identity = 'same identity'
        self.ctx.delivery = object()
        self.ctx.connection_generation = 4
        self.ctx.replay_ready = True
        self.ctx.validation_error = None
        self.ctx.persistence = SimpleNamespace(initial=False, closed=False)

    def test_inherited_connected_replay_cannot_send_goal_before_validation(self):
        # AP 0.6.8 calls send_msgs(CLIENT_GOAL) BEFORE on_package(Connected).
        # Even stale success/replay fields must not authorize that generic call.
        self.ctx.finished_game = True
        asyncio.run(self.ctx.send_msgs([{'cmd':'StatusUpdate','status':30}, {'cmd':'Sync'}]))
        self.assertEqual(self.packets, [{'cmd':'Sync'}])

    def test_validated_watcher_can_send_and_reassert(self):
        for _ in range(2):
            self.assertTrue(asyncio.run(self.ctx.send_goal('same identity', self.ctx.delivery, 4)))
        self.assertEqual(self.packets, [{'cmd':'StatusUpdate','status':30}]*2)

    def test_incomplete_or_rejected_history_and_changed_owner_never_send(self):
        for key, value in [('replay_ready',False), ('validation_error','truncated server history'),
                           ('identity','foreign'), ('delivery',object()), ('connection_generation',5)]:
            with self.subTest(key=key):
                self.setUp()
                delivery = self.ctx.delivery
                setattr(self.ctx, key, value)
                self.assertFalse(asyncio.run(self.ctx.send_goal('same identity', delivery, 4)))
                self.assertEqual(self.packets, [])

    def test_reconnect_during_send_cannot_latch_old_submission(self):
        self.ctx.reconnect_during_send = True
        self.assertFalse(asyncio.run(self.ctx.send_goal('same identity', self.ctx.delivery, 4)))
        self.assertEqual(len(self.packets), 1)

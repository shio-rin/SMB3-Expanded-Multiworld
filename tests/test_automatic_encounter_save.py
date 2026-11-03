# SPDX-License-Identifier: MPL-2.0
"""Real checkpoint Lua, mocked native transitions; native evidence is separate."""
import unittest
import test_autosave_policy as fixture


class AutomaticEncounterSaveTests(unittest.TestCase):
    def setUp(self):
        fixture.AutosavePolicyTests.setUp(self)
        self.lua.execute('writes=0;joypad.set=function()writes=writes+1 end')

    def enter(self, mode='quiescing', tileset=17):
        self.lua.globals().mode = mode
        self.lua.globals().tileset = tileset
        self.lua.execute('''c.state.mode=mode;c.state.requested=true;c.state.dirty=true
         safe_flag=false;mem[0x70A]=tileset;mem[0x729]=15
         c.tick();input_callback()''')

    def test_uncommitted_request_yields_to_native_bonus_and_retains_save(self):
        for mode in ('playing', 'quiescing'):
            for tileset in (17, 3):  # matching cards and native Hammer Bros. arena
                with self.subTest(mode=mode, tileset=tileset):
                    self.setUp()
                    self.enter(mode, tileset)
                    self.assertEqual(self.lua.eval('writes'), 0)
                    self.assertEqual(self.lua.eval('c.state.mode'), 'playing')
                    self.assertTrue(self.lua.eval('c.state.requested and c.state.dirty'))
                    self.lua.execute('mem[0x70A]=0;mem[0x729]=13;safe_flag=true;c.tick();input_callback()')
                    self.assertEqual(self.lua.eval('c.state.mode'), 'quiescing')
                    self.assertGreater(self.lua.eval('writes'), 0)

    def test_grant_and_stronger_owners_never_yield_input(self):
        for setup in ('c.state.awaiting_ack=true', 'delivery.state.flight={index=0}',
                      'c.state.batch_count=1', 'c.state.saved_signature=nil',
                      'travel.state.authorized=false', 'mem[0x79F3]=1'):
            with self.subTest(setup=setup):
                self.setUp()
                self.lua.execute(setup)
                self.enter()
                self.assertGreater(self.lua.eval('writes'), 0)
        for mode in ('restoring', 'frozen', 'synchronizing', 'suspended', 'closed', 'failed'):
            with self.subTest(mode=mode):
                self.setUp()
                self.enter(mode)
                self.assertGreater(self.lua.eval('writes'), 0)

    def test_unissued_items_remain_pending_through_encounter(self):
        self.lua.execute('delivery.state.pending={{index=4,item=123}}')
        self.enter()
        self.assertEqual(self.lua.eval('writes'), 0)
        self.assertEqual(self.lua.eval('#delivery.state.pending'), 1)
        self.assertEqual(self.lua.eval('delivery.state.pending[1].index'), 4)

    def test_menu_or_unsettled_map_alone_does_not_release_input(self):
        self.lua.execute('c.state.mode="quiescing";c.state.requested=true;safe_flag=false;mem[0x3ED]=1;c.tick();input_callback()')
        self.assertGreater(self.lua.eval('writes'), 0)

    def test_first_input_poll_during_automatic_entry_yields_before_next_tick(self):
        self.lua.execute('''c.state.mode='quiescing';c.state.requested=true
         safe_flag=false;mem[0x70A]=0;mem[0x729]=15;input_callback()''')
        self.assertEqual(self.lua.eval('writes'), 0)
        self.assertTrue(self.lua.eval('c.state.requested and c.state.dirty'))
        self.assertEqual(self.lua.eval('c.state.stable'), 0)

    def test_ordinary_encounter_before_request_or_after_completed_save_stays_playable(self):
        self.lua.execute('mem[0x70A]=9;mem[0x729]=15;safe_flag=false;input_callback();c.tick()')
        self.assertEqual(self.lua.eval('writes'), 0)
        self.assertFalse(self.lua.eval('c.state.requested'))
        self.assertTrue(self.lua.eval('c.state.dirty'))

    def test_deferred_save_cannot_leak_through_connection_hold(self):
        self.enter()
        self.assertEqual(self.lua.eval('writes'), 0)
        self.lua.execute("args.hash=function()return 'unchanged'end;c.control({session='s',run='r',token='t',op='WAIT_SERVER'});input_callback()")
        self.assertGreater(self.lua.eval('writes'), 0)
        self.assertTrue(self.lua.eval('c.state.requested'))


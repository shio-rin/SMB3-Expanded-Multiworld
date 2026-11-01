# SPDX-License-Identifier: MPL-2.0
"""Actual Lua policy with mocked RAM; native lifecycle evidence is separate."""
from pathlib import Path
import unittest
from lupa import LuaRuntime

ROOT=Path(__file__).resolve().parents[1]

class AutosavePolicyTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True)
  self.lua.execute('''
   mem={[0x729]=13,[0x79A2]=2,[0x79AE]=1};safe_flag=true;now=0;frame=100;point=1;data=0
   function r(a)return mem[a]or 0 end
   os.time=function()return now end
   event={oninputpoll=function(f)input_callback=f end};joypad={get=function()return {}end,set=function()end}
   client={ispaused=function()return false end};userdata={};savestate={}
   travel={state={authorized=true},checkpoint_safe=function()return safe_flag end,
    checkpoint_status=function()return {world=0,transaction=0,ending_phase=0,snapshot={data={data},point={point}}}end,
    progression_settled=function()return true end,authorize=function()end}
   delivery={state={pending={},results={},full_index=nil},snapshot=function()return {}end,acks=function()return {}end}
   monitor={checks=function()return {}end}
   args={travel=travel,delivery=delivery,monitor=monitor,build={session='s'},run='r',token='t',
    read=r,frame=function()return frame end,clock=function()return now end,
    log=function()end,pause=function()end,unpause=function()end}
  ''')
  self.lua.globals().module=self.lua.execute((ROOT/'src/smb3x/bizhawk/checkpoints.lua').read_text())
  self.lua.execute('''c=module.new(args);c.state.mode='frozen';c.state.verified=true;c.state.marker='m';c.state.frame=frame
   c.control({session='s',run='r',token='t',op='THAW',marker='m',epoch_token=string.rep('a',32)})''')
 def test_inventory_and_travel_menu_cancel_do_not_request_capture(self):
  for address in (0x3ED,0x79DB):
   self.lua.globals().address=address
   self.lua.execute('mem[address]=1;safe_flag=false;c.tick();mem[address]=0;safe_flag=true;c.tick();input_callback()')
   self.assertEqual(self.lua.eval('c.state.mode'),'playing')
   self.assertFalse(self.lua.eval('c.state.dirty or c.state.exposed or c.state.requested'))
 def test_position_only_after_interval_does_not_request_capture(self):
  self.lua.execute('point=2;now=31;c.contact();c.tick();input_callback()')
  self.assertEqual(self.lua.eval('c.state.mode'),'playing')
  self.assertFalse(self.lua.eval('c.state.requested'))
 def test_inventory_serial_change_while_menu_open_marks_exposed_tail(self):
  self.lua.execute('mem[0x3ED]=1;safe_flag=false;mem[0x7ACC]=1;c.tick()')
  self.assertTrue(self.lua.eval('c.state.dirty and c.state.exposed'))
  self.lua.execute('mem[0x3ED]=0;safe_flag=true;c.tick()')
  self.assertEqual(self.lua.eval('c.state.mode'),'quiescing')
 def test_native_level_activity_still_checkpoints_even_equal_return_snapshot(self):
  self.lua.execute('mem[0x70A]=1;safe_flag=false;c.tick()')
  self.assertTrue(self.lua.eval('c.state.dirty and c.state.exposed'))
  self.lua.execute('mem[0x70A]=0;safe_flag=true;c.tick()')
  self.assertEqual(self.lua.eval('c.state.mode'),'quiescing')
 def test_vanilla_slot_consumption_without_serial_marks_exposed_tail(self):
  self.lua.execute('''mem[0x7D80]=3;c.state.mode='frozen';c.state.verified=true;c.state.marker='m';c.state.frame=frame
   c.control({session='s',run='r',token='t',op='THAW',marker='m',epoch_token=string.rep('b',32)})
   mem[0x3ED]=1;safe_flag=false;mem[0x7D80]=0;c.tick()''')
  self.assertEqual(self.lua.eval('mem[0x7ACC]or 0'),0)
  self.assertTrue(self.lua.eval('c.state.dirty and c.state.exposed'))
 def test_meaningful_world_change_gates_first_safe_input(self):
  self.lua.execute('data=128;input_callback()')
  self.assertTrue(self.lua.eval('c.state.dirty and c.state.requested'))
 def test_explicit_save_quit_remains_a_capture_without_state_change(self):
  self.lua.execute('c.request()')
  self.assertTrue(self.lua.eval('c.state.quit and c.state.requested'))
  self.assertEqual(self.lua.eval('c.state.mode'),'quiescing')
 def test_player_shortcut_and_confirmation_buttons_are_not_intercepted(self):
  self.lua.execute('writes=0;joypad.set=function()writes=writes+1 end;joypad.get=function()return {Start=true,Select=true,A=true,B=true}end;input_callback()')
  self.assertEqual(self.lua.eval('writes'),0)
  self.assertFalse(self.lua.eval('c.state.ui or c.state.quit or c.state.requested'))
 def test_presentation_timestamp_and_unsaved_state_are_not_ui_inference(self):
  self.assertEqual(self.lua.eval('c.presentation().saved'),'none')
  self.lua.execute("c.state.last_checkpoint=1234567890;c.state.saved_notice_until=10;c.state.saved_point='1';point=2")
  self.assertEqual(self.lua.eval('c.presentation().label'),'Last checkpoint')
  self.lua.execute('c.state.dirty=true;c.state.exposed=true')
  self.assertEqual(self.lua.eval('c.presentation().label'),'Unsaved progress')
  self.lua.execute("c.state.mode='frozen';c.control({session='s',run='r',token='t',op='SAVE_FAILED'})")
  self.assertEqual(self.lua.eval('c.presentation().label'),'Save failed')

if __name__=='__main__':unittest.main()

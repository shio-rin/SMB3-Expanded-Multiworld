# SPDX-License-Identifier: MPL-2.0
"""Actual delivery Lua with mocked RAM: native overlap evidence is separate."""
from pathlib import Path
import unittest
from lupa import LuaRuntime


class DeliverySettlementTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''frame=0;safe=true;mem={[0x736]=4};writes=0
         args={read=function(a)return mem[a]or 0 end,
          write=function(a,v)mem[a]=v;writes=writes+1 end,
          frame=function()return frame end,safe=function()return safe end,
          log=function()end,unlock=function()end}
         rows={{id='0x1',name='1-Up',kind='life'}}''')
        path = Path(__file__).resolve().parents[1]/'src/smb3x/bizhawk/delivery.lua'
        self.lua.globals().module = self.lua.execute(path.read_text())
        self.lua.execute('d=module.new(args,rows)')

    def test_previous_map_settlement_cannot_issue_on_chained_return(self):
        self.lua.execute('for i=1,40 do frame=i;d.process()end')
        self.assertEqual(self.lua.eval('d.state.stable'),30)
        # Ordinary playing skips process(). Native bonus frames still advance.
        self.lua.execute('frame=2000;d.sync({{index=0,item=1}},{},1);d.process()')
        self.assertEqual(self.lua.eval('writes'),0)
        self.assertEqual(self.lua.eval('#d.state.pending'),1)
        self.lua.execute('frame=2001;safe=false;d.process()')
        self.assertEqual(self.lua.eval('writes'),0)
        self.lua.execute('safe=true;for i=2002,2030 do frame=i;d.process()end')
        self.assertEqual(self.lua.eval('writes'),0)
        self.lua.execute('frame=2031;d.process()')
        self.assertEqual(self.lua.eval('mem[0x736]'),5)
        self.assertEqual(self.lua.eval('#d.acks()'),1)
        self.lua.execute('for i=2032,2100 do frame=i;d.process()end')
        self.assertEqual(self.lua.eval('writes'),1)

    def test_repeated_poll_of_same_native_frame_does_not_settle(self):
        self.lua.execute('d.sync({{index=0,item=1}},{},1);for i=1,100 do d.process()end')
        self.assertEqual(self.lua.eval('writes'),0)
        self.assertEqual(self.lua.eval('d.state.stable'),1)

    def test_load_and_unsafe_frame_restart_settlement(self):
        self.lua.execute('for i=1,29 do frame=i;d.process()end;d.onload();d.sync({{index=0,item=1}},{},1);frame=30;d.process()')
        self.assertEqual(self.lua.eval('writes'),0)
        self.lua.execute('safe=false;d.process();safe=true;frame=31;d.process()')
        self.assertEqual(self.lua.eval('d.state.stable'),1)

# SPDX-License-Identifier: MPL-2.0
"""Production Lua scheduler with mocked native mechanics, no native claims."""
import json
from pathlib import Path
import unittest
from lupa import LuaRuntime

ROOT=Path(__file__).resolve().parents[1]

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
level=0; playable=true; ended=false; area='room'; held=false; compatible={small=true,walking=true,icy=true,star=true,mushroom=true}; requests={}
native={tick=function()end,state=function()return {}end,can_start=function(k)return playable and compatible[k]end,
gameplay=function()return playable end,area=function()return area end,ended=function()return ended end,
request=function(k)table.insert(requests,k);return true end}
fixture={read=function()return level end,log=function()end,hold=function(v)held=v end,
equal=function(a,b)if type(a)~=type(b)then return false end;if type(a)~='table'then return a==b end
for k,v in pairs(a)do if not fixture.equal(v,b[k])then return false end end
for k,v in pairs(b)do if not fixture.equal(v,a[k])then return false end end;return true end,
native=function(notify)observe=notify;return native end}
''')
        self.q=self.lua.execute((ROOT/'src/smb3x/bizhawk/effects.lua').read_text()).new(self.lua.globals().fixture)
        self.value=dict(contract='m25-effects-1',prefix=[],records={},last_entry=0)
    def push(self,i,kind):
        self.value['records'][str(i)]=dict(receipt=str(i),kind=kind,state='queued',entry=None,token=None,reason='',delay_frames=None)
        self.sync()
    def sync(self,ack=None):self.q.sync(self.lua.table_from(self.value,recursive=True),ack)
    def step(self,**kwargs):
        for k,v in kwargs.items():self.lua.globals()[k]=v
        self.q.tick()
    def select(self):
        self.step(level=1);return self.q.event()
    def schedule(self,event,delay=240):
        self.value['last_entry']=event['entry']
        if event['index'] is not False:self.value['records'][str(event['index'])].update(state='scheduled',entry=event['entry'],delay_frames=delay)
        self.sync(event['sequence'])

    def test_oldest_compatible_snapshot_retains_restricted_head(self):
        for i,k in enumerate(('micro','walking','icy')):self.push(i,k)
        e=self.select();self.assertEqual(e['index'],1);self.assertEqual(list(e['eligible'].values()),[1,2])
        self.schedule(e);self.assertEqual(self.value['records']['0']['state'],'queued')
        self.assertIsNone(self.q.event())

    def test_midlevel_receipt_waits_for_next_entry(self):
        e=self.select();self.assertFalse(e['index']);self.schedule(e)
        self.push(0,'walking')
        for _ in range(50):self.step()
        self.assertIsNone(self.q.event())
        self.step(level=0);e=self.select();self.assertEqual(e['index'],0)

    def test_exact_active_countdown_pause_and_durable_permission(self):
        self.push(0,'walking');self.schedule(self.select())
        for _ in range(239):self.step()
        self.assertIsNone(self.q.event())
        for _ in range(300):self.step(playable=False)
        self.assertIsNone(self.q.event())
        self.step(playable=True);e=self.q.event();self.assertEqual(e['type'],'ready');self.assertTrue(self.lua.globals().held)
        self.assertEqual(len(self.lua.globals().requests),0)
        with self.assertRaises(Exception):self.sync(e['sequence'])
        self.value['records']['0'].update(state='committed',token='a'*64)
        self.sync(e['sequence']);self.assertFalse(self.lua.globals().held);self.assertEqual(list(self.lua.globals().requests.values()),['walking'])
        with self.assertRaises(Exception):self.sync(e['sequence'])

    def test_death_before_commit_requeues_without_native_request(self):
        self.push(0,'walking');self.schedule(self.select());self.step(ended=True)
        e=self.q.event();self.assertEqual(e['state'],'queued');self.assertEqual(len(self.lua.globals().requests),0)
        self.value['records']['0'].update(state='queued',entry=None,reason=e['reason'],delay_frames=None)
        self.sync(e['sequence']);self.step(level=0,ended=False)
        e=self.select();self.assertEqual(e['index'],0);self.assertEqual(e['entry'],2)

    def test_doorway_preserves_scheduled_delay_and_entry_limit(self):
        self.push(0,'walking');self.schedule(self.select())
        for _ in range(100):self.step()
        self.step(area='fortress boss room',playable=False)
        self.assertIsNone(self.q.event())
        for _ in range(300):self.step()
        self.assertIsNone(self.q.event())
        for _ in range(139):self.step(playable=True)
        self.assertIsNone(self.q.event())
        self.step();e=self.q.event()
        self.assertEqual(e['type'],'ready')
        self.assertEqual(e['entry'],1)
        self.assertEqual(e['area'],'fortress boss room')
        self.assertEqual(len(self.lua.globals().requests),0)

    def test_room_change_defers_incompatible_micro_without_consumption(self):
        self.lua.execute('compatible.micro=true')
        self.push(0,'micro');self.push(1,'walking');self.schedule(self.select())
        self.lua.execute('compatible.micro=false')
        for _ in range(400):self.step(area='different graphics')
        self.assertIsNone(self.q.event())
        self.assertEqual(self.value['records']['0']['state'],'scheduled')
        self.assertEqual(self.value['records']['1']['state'],'queued')
        self.lua.execute('compatible.micro=true')
        self.step();self.assertEqual(self.q.event()['type'],'ready')

if __name__=='__main__':unittest.main()

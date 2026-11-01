# SPDX-License-Identifier: MPL-2.0
"""DeathLink custody, original deadlines and Lua dispatch (mocked native API)."""
from copy import deepcopy
from pathlib import Path
import unittest
from lupa import LuaRuntime
from smb3x.client.deathlink import empty, payload, event_id, validate, extends, recovered

ROOT=Path(__file__).resolve().parents[1]

def record(state='queued'):
    return dict(direction='incoming',state=state,received=100000,deadline=120000,network_id='a'*64,run='b'*32,reason='original receipt')

class DeathLinkTests(unittest.TestCase):
    def test_untrusted_payload_and_timestamp_bounds(self):
        good=dict(time=100,source='Peer',cause='native death')
        self.assertIsNotNone(payload(good,100))
        for bad in (None,{},dict(good,time=float('nan')),dict(good,time=True),dict(good,time=79),dict(good,time=106),dict(good,source=''),dict(good,source='x\n'),dict(good,cause='x'*513)):
            self.assertIsNone(payload(bad,100),bad)
        self.assertEqual(event_id(payload(good,100)),event_id(payload(dict(good,time=100.),100)))

    def test_recovery_never_replays_pending_or_uncertain_death(self):
        for state in ('queued','committed','send_intent','applied','expired','published','send_uncertain'):
            value=empty();value['records']['a'*64]=record(state)
            if state in ('send_intent','published','send_uncertain'):
                value['records']['a'*64].update(direction='outgoing',deadline=100000)
            result=recovered(value)
            self.assertEqual(result['records']['a'*64]['state'], 'disposed_interrupted' if state in ('queued','committed','send_intent') else state)
            self.assertEqual(value['records']['a'*64]['state'],state)
            extends(value,result)

    def test_origin_deadline_and_terminal_are_monotonic(self):
        value=empty();value['records']['a'*64]=record('applied')
        for field,val in (('state','queued'),('received',101000),('deadline',119000),('run','c'*32),('network_id','c'*64),('reason','rewrite')):
            bad=deepcopy(value);bad['records']['a'*64][field]=val
            with self.assertRaises(ValueError):extends(value,bad)
        with self.assertRaises(ValueError):extends(value,empty())

    def test_contradictory_direction_or_packet_identity_rejected(self):
        value=empty();value['records']['a'*64]=record()
        for change in (dict(state='published'),dict(network_id='c'*64),dict(run='z'*32),dict(network_id='z'*64)):
            bad=deepcopy(value);bad['records']['a'*64].update(change)
            with self.assertRaises(ValueError):validate(bad)

    def make_lua(self,enabled=True):
        self.lua=LuaRuntime(unpack_returned_tuples=True);self.now=105;self.calls=[];self.allowed=True
        native=self.lua.table_from(dict(can_start=lambda kind:True,remote_death=lambda deadline:self.calls.append(deadline) or True))
        io=self.lua.table_from(dict(read=lambda a:0,clock=lambda:self.now,allowed=lambda:self.allowed,enabled=enabled,native=native))
        self.api=self.lua.execute((ROOT/'src/smb3x/bizhawk/deathlink.lua').read_text()).new(io)
        self.value=empty();self.value['records']['a'*64]=record('committed')
    def command(self,op,**kw):
        return self.api.control(self.lua.table_from(dict(op=op,deathlink=self.value,**kw),recursive=True))
    def apply(self):return self.command('DEATH_APPLY',id='a'*64,received=100000,deadline=120000)

    def test_original_deadline_not_transport_read_time(self):
        self.make_lua();self.now=121
        self.assertFalse(self.apply()['accepted']);self.assertEqual(self.calls,[])
        self.now=99;self.assertFalse(self.apply()['accepted']);self.assertEqual(self.calls,[])
        self.now=119;self.assertTrue(self.apply()['accepted']);self.assertEqual(self.calls,[120.])
        self.assertFalse(self.apply()['accepted']);self.assertEqual(self.calls,[120.])

    def test_off_and_missing_commit_cannot_apply(self):
        self.make_lua(False)
        with self.assertRaises(Exception):self.apply()
        self.make_lua();self.value['records']['a'*64]['state']='queued'
        with self.assertRaises(Exception):self.apply()
        self.assertEqual(self.calls,[])

    def test_remote_observation_retains_origin_until_exact_ack(self):
        self.make_lua();self.apply()
        self.api.observe(self.lua.table_from(dict(kind='remote-death-observed',reason='native producer')))
        e=self.command('DEATH_STATUS')['events'][1]
        self.assertEqual(e['remote_id'],'a'*64);self.assertFalse(self.api.safe())
        with self.assertRaises(Exception):self.command('DEATH_ACK',event_sequence=2)
        self.value['records']['a'*64]['state']='applied'
        self.command('DEATH_ACK',event_sequence=1);self.assertTrue(self.api.safe())

if __name__=='__main__':unittest.main()

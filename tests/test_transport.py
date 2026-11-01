# SPDX-License-Identifier: MPL-2.0
"""Wire40 localhost failure injection; simulated Lua peer, not native proof."""
import asyncio
import json
import unittest
from smb3x.client.native_session import NativeBridge

class EffectTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_lost_commit_reply_recovers_exact_sequence_without_second_activation(self):
        connections=[];applied=[];original={}
        async def peer(reader,writer):
            connections.append(1);q=json.loads(await reader.readline())
            if len(connections)==1:
                original.update(q);applied.append(q['acknowledgement']);writer.close();return
            writer.write(json.dumps(dict(protocol=40,session='seed',bridge_instance='lua',suspension={'challenge':'same-instance'})).encode()+b'\n');await writer.drain()
            retry=json.loads(await reader.readline());self.assertEqual(retry.pop('resume_transport'),'same-instance');self.assertEqual(retry,original)
            writer.write(json.dumps(dict(protocol=40,session='seed',bridge_instance='lua',sequence=q['sequence'],accepted=True)).encode()+b'\n');await writer.drain()
            await reader.read();writer.close()
        server=await asyncio.start_server(peer,'127.0.0.1',0)
        bridge=NativeBridge({'session':'seed','effects':{}},'.',port=server.sockets[0].getsockname()[1],run='run',token='token')
        bridge.response_notice_seconds=.02;bridge.recovery_validator=lambda:dict(run='run',state='active',epoch_token='epoch')
        try:
            result=await asyncio.wait_for(bridge.control('EFFECTS',effects={'committed':'test-token'},acknowledgement=4),2)
            self.assertTrue(result['accepted']);self.assertEqual(applied,[4]);self.assertEqual(len(connections),2)
        finally:
            await bridge.close();server.close();await server.wait_closed()

if __name__=='__main__':unittest.main()

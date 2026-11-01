# SPDX-License-Identifier: MPL-2.0
"""Storage faults/identity/epochs only. Native lifecycle is gate_m232.py."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from fixtures.controlled_checkpoint import CheckpointStore,write_new,read,fingerprint,validate_prefix,validate_components
from smb3x.client.persistence.receipts import Identity,DeliveryState
from smb3x.client.persistence.world_journal import NativeJournal,ADDRESSES
from smb3x.client.inventory import seal

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.identity=Identity('M232-STORAGE-TEST',0,1)
        self.binding=dict(identity=self.identity.as_dict(),rom_sha256='b'*64,registry='c'*64,
            prg_sha256='d'*64,chr_sha256='e'*64,
            progression=dict(inventory_mode='stacked',hammer_mode='regional'),location_ids=[0x534D3301])
        self.store=CheckpointStore(self.root,self.binding);self.run,self.live=self.store.new_run()
    def candidate(self):
        c=self.store.candidate(self.run);path=Path(c['path']);key=self.identity.key
        n=dict(session=key,phase=2,bound=1,error=0,world=0,active=0,sequence=1,seen=1,transaction=0,
            unlock=1,
            ending_phase=0,ending_version=0,snapshot=dict(data=[0]*len(ADDRESSES),point=[80,32,0,0,0]))
        inv=dict(format=1,mode='stacked',quantities=[0]*13,slots=[0]*28,serial=0,ticket=0,item=0,pending=0,receipt_before=0,receipt_after=0,receipt_serial=0)
        journal=NativeJournal(self.live/'worlds',key,'b'*64,'c'*64)
        journal.reconcile(n);worlds=deepcopy(journal.state);worlds['inventory']=seal(inv)
        delivery=DeliveryState(self.identity,registry='c'*64).as_dict()
        controller=dict(schema=1,session=key,delivery=dict(items={},pending=[],handled={}),physical_checks=[],flight=False,unissued=True,
            travel=dict(schema=1,session=key,active=0,want_mask=1,progression=dict(hammers=0,stars=0,pending=0,checks=[0]*8)))
        witness=dict(schema=1,session=key,frame=742,native=n,inventory=inv,ram=['a'*64,'f'*64],prg='d'*64,chr='e'*64,
            frozen=True,publication=dict(mailbox=0,stack=0,pending=0,write=0))
        for name,value in dict(worlds=worlds,deliveries=delivery,controller=controller,witness=witness,server=dict(schema=1,received=[])).items():write_new(path/(name+'.json'),value)
        with ZipFile(path/'native.State','w') as z:
            z.writestr('Core.bin',b'disposable mock core');z.writestr('BizVersion.txt','Version 2.10');z.writestr('UserData.txt',json.dumps({'o':{'smb3.m232.generation':c['marker']}}))
        verification=dict(verified=True,marker=c['marker'],witness_sha256=fingerprint(witness),frame=742)
        return c,verification
    def test_clean_publish_resume_and_one_use_epoch(self):
        c,v=self.candidate();self.store.publish(c,v)
        run,derived,folder,m,parts=self.store.resume()
        self.assertEqual(read(derived/'deliveries'/(self.identity.key+'.json')),parts['deliveries'])
        self.store.activate(run)
        with self.assertRaisesRegex(ValueError,'stale'):self.store.activate(run)
        with self.assertRaisesRegex(ValueError,'clean'):self.store.resume()
        self.assertTrue(folder.exists())
    def test_each_missing_or_corrupt_member_rejected_without_epoch_mutation(self):
        c,v=self.candidate();self.store.publish(c,v);folder,m,_=self.store.verify();epoch=self.store.epochs.read_bytes()
        for name in m['members']:
            p=folder/name;old=p.read_bytes();p.write_bytes(old+b'x')
            with self.assertRaises(ValueError):self.store.resume()
            self.assertEqual(self.store.epochs.read_bytes(),epoch);p.write_bytes(old)
    def test_pointer_failure_does_not_close_epoch_or_destroy_candidate(self):
        c,v=self.candidate()
        with patch('fixtures.controlled_checkpoint.save_json',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.store.publish(c,v)
        self.assertFalse(self.store.pointer.exists());self.assertEqual(self.store.epoch()['state'],'active')
        self.assertTrue((self.root/'checkpoints'/c['generation']/'manifest.json').exists())
    def test_manifest_failure_preserves_staging(self):
        c,v=self.candidate()
        with patch('fixtures.controlled_checkpoint.write_new',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.store.publish(c,v)
        self.assertTrue(Path(c['path']).exists());self.assertFalse(self.store.pointer.exists())
    def test_wrong_verification_and_native_grant_reject(self):
        c,v=self.candidate()
        with self.assertRaises(ValueError):self.store.publish(c,{**v,'frame':743})
        path=Path(c['path']);w=read(path/'witness.json');w['inventory']['pending']=3
        (path/'witness.json').write_text(json.dumps(w))
        with self.assertRaisesRegex(ValueError,'Inventory'):validate_components(path,self.binding)
    def test_prefix_compares_full_tuples_and_rejects_short_authoritative_replay(self):
        saved=[[1,2,3,4],[5,6,7,8]]
        validate_prefix(saved,saved+[[9,10,11,12]])
        for wrong in ([],saved[:1],[[1,99,3,4],saved[1]]):
            with self.assertRaises(ValueError):validate_prefix(saved,wrong)
    def test_pending_partition_and_occupied_point(self):
        c,v=self.candidate();path=Path(c['path']);d=read(path/'deliveries.json');d['pending']=[0]
        (path/'deliveries.json').write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'partition'):validate_components(path,self.binding)
    def test_wrong_binding_and_new_session_reuse(self):
        c,v=self.candidate();self.store.publish(c,v)
        with self.assertRaises(ValueError):self.store.new_run()
        bad=CheckpointStore(self.root,{**self.binding,'rom_sha256':'d'*64})
        with self.assertRaisesRegex(ValueError,'binding'):bad.resume()
    def test_clean_retry_before_player_control_retains_each_attempt(self):
        c,v=self.candidate();self.store.publish(c,v)
        r1,p1,*_=self.store.resume();r2,p2,*_=self.store.resume()
        self.assertNotEqual(r1,r2);self.assertTrue(p1.exists() and p2.exists())
        with self.assertRaises(ValueError):self.store.activate(r1)
        self.store.activate(r2)

if __name__=='__main__':unittest.main()


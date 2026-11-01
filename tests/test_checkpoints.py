# SPDX-License-Identifier: MPL-2.0
"""M233 automatic generations/recovery barriers; State payload is explicitly mocked."""
from pathlib import Path
import json,tempfile,unittest
from copy import deepcopy
from zipfile import ZipFile
from unittest.mock import patch
from tests.test_controlled_checkpoint_fixture import CheckpointTests as Fixture
from smb3x.client.persistence.checkpoints import CheckpointStore,RecoveryConfirmationNeeded,read,save_json,validate_prefix

class AutoCheckpointTests(unittest.TestCase):
 def setUp(self):
  Fixture.setUp(self)
  self.binding['schema']=2
  self.binding['emulator']={'core':'NesHawk','profile':'2.10','revision':'2.10+dd232820493c05296c304b64bf09c57ff1e4812f'}
  self.store=CheckpointStore(self.root/'m233',self.binding);self.run,self.live=self.store.new_run()
 def candidate(self):
  c,v=Fixture.candidate(self)
  with ZipFile(Path(c['path'])/'native.State','w')as z:
   z.writestr('Core.bin',b'explicitly mocked native state');z.writestr('BizVersion.txt','Version 2.10')
   z.writestr('UserData.txt',json.dumps({'o':{'smb3.m233.generation':c['marker']}}))
  return c,v
 def publish(self):
  c,v=self.candidate();p=self.store.publish(c,v);return p
 def test_multiple_automatic_generations_rotate_before_control(self):
  generations=[];tokens=[]
  for _ in range(3):
   p=self.publish();self.assertEqual(self.store.epoch()['state'],'sealed');generations.append(p['generation'])
   tokens.append(self.store.activate_checkpoint(self.run,p['generation']))
  self.assertEqual(len(set(tokens)),3);self.assertEqual(len(list((self.store.root/'checkpoints').iterdir())),3)
  self.assertEqual(self.store.verify()[1]['parent']['generation'],generations[-2])
  with self.assertRaises(ValueError):self.store.activate_checkpoint(self.run,generations[-1])
 def test_unclean_unexposed_tail_restores_fresh_derived_run(self):
  p=self.publish();self.store.activate_checkpoint(self.run,p['generation']);old=self.live
  run,live,folder,m,c=self.store.resume();self.assertNotEqual(run,self.run);self.assertTrue(old.exists())
  self.assertEqual(read(live/'deliveries'/(self.identity.key+'.json')),c['deliveries'])
  self.assertEqual(self.store.recovery['kind'],'automatic');self.store.activate(run)
 def test_known_exposed_tail_requires_confirmation_without_mutation(self):
  p=self.publish();self.store.activate_checkpoint(self.run,p['generation']);self.store.mark_exposed(self.run,'unsaved native stage progress',900)
  before=self.store.epochs.read_bytes()
  with self.assertRaises(RecoveryConfirmationNeeded):self.store.resume()
  self.assertEqual(self.store.epochs.read_bytes(),before)
  run,live,*_=self.store.resume(allow_loss=True);self.assertTrue(self.live.exists());self.assertNotEqual(live,self.live)
 def test_unsaved_check_cannot_be_authorized_for_publication(self):
  p=self.publish();self.store.activate_checkpoint(self.run,p['generation']);before=self.store.epochs.read_bytes()
  with self.assertRaisesRegex(ValueError,'Unsaved'):self.store.authorize_publication(self.run,[0x534D3301])
  self.assertEqual(self.store.epochs.read_bytes(),before)
 def test_published_check_outside_checkpoint_stops_recovery(self):
  self.publish();e=self.store.epoch();save_json(self.store.epochs,{**e,'published':[0x534D3301]})
  with self.assertRaisesRegex(ValueError,'publication'):self.store.resume()
 def test_pointer_committed_epoch_failure_recovers_verified_latest(self):
  c,v=self.candidate();original=save_json
  def fail_epoch(path,data):
   if path==self.store.epochs:raise OSError('injected epoch replacement failure')
   return original(path,data)
  with patch('smb3x.client.persistence.checkpoints.save_json',side_effect=fail_epoch):
   with self.assertRaises(OSError):self.store.publish(c,v)
  self.assertTrue(self.store.pointer.exists());self.assertEqual(self.store.epoch()['state'],'active')
  run,_,_,m,_=self.store.resume();self.assertEqual(m['generation'],c['generation']);self.store.activate(run)
 def test_no_initial_checkpoint_means_no_recovery(self):
  with self.assertRaises(FileNotFoundError):self.store.resume()
 def test_unstarted_restart_preserves_old_run(self):
  old=self.run;run,live=self.store.restart_unstarted()
  self.assertNotEqual(run,old);self.assertTrue(self.live.exists());self.assertTrue(live.exists())
  self.assertEqual(self.store.epoch()['unstarted_predecessor'],old)
 def test_initial_native_evidence_blocks_unstarted_restart(self):
  worlds=self.live/'worlds';worlds.mkdir();(worlds/(self.identity.key+'.json')).write_text('{}')
  before=self.store.epochs.read_bytes()
  with self.assertRaisesRegex(ValueError,'native activity'):self.store.restart_unstarted()
  self.assertEqual(self.store.epochs.read_bytes(),before)
 def test_previous_namespace_is_not_a_migration(self):
  c,v=Fixture.candidate(self)
  with self.assertRaisesRegex(ValueError,'namespaced'):self.store.publish(c,v)
 def test_every_missing_or_corrupt_component_rejects_without_epoch_mutation(self):
  self.publish();folder,m,_=self.store.verify();before=self.store.epochs.read_bytes()
  for name in m['members']:
   path=folder/name;original=path.read_bytes()
   for missing in (False,True):
    with self.subTest(member=name,missing=missing):
     if missing:path.unlink()
     else:path.write_bytes(original+b'corrupt')
     try:
      with self.assertRaises((OSError,ValueError)):self.store.resume()
      self.assertEqual(self.store.epochs.read_bytes(),before)
     finally:path.write_bytes(original)
 def test_wrong_identity_rom_registry_and_core_binding_reject(self):
  self.publish();before=self.store.epochs.read_bytes()
  mutations=[('rom_sha256','a'*64),('prg_sha256','a'*64),('chr_sha256','a'*64),('registry','a'*64),
   ('identity',{**self.binding['identity'],'slot':2}),('emulator',{'core':'QuickNes','version':'2.10'})]
  for field,value in mutations:
   with self.subTest(field=field):
    binding=deepcopy(self.binding);binding[field]=value
    with self.assertRaisesRegex(ValueError,'binding'):CheckpointStore(self.store.root,binding).resume()
    self.assertEqual(self.store.epochs.read_bytes(),before)
 def test_wrong_native_container_version_rejects_before_publication(self):
  c,v=self.candidate()
  with ZipFile(Path(c['path'])/'native.State','w')as z:
   z.writestr('Core.bin',b'mocked core');z.writestr('BizVersion.txt','Version 2.9')
   z.writestr('UserData.txt',json.dumps({'o':{'smb3.m233.generation':c['marker']}}))
  with self.assertRaisesRegex(ValueError,'emulator version'):self.store.publish(c,v)
  self.assertFalse(self.store.pointer.exists());self.assertEqual(self.store.epoch()['state'],'active')
 def test_stale_pointer_older_than_epoch_is_not_a_recovery_candidate(self):
  first=self.publish();old=self.store.pointer.read_bytes();self.store.activate_checkpoint(self.run,first['generation']);self.publish()
  epoch=self.store.epochs.read_bytes();self.store.pointer.write_bytes(old)
  with self.assertRaisesRegex(ValueError,'ancestor'):self.store.resume()
  self.assertEqual(self.store.epochs.read_bytes(),epoch)
 def test_pointer_write_interruption_preserves_previous_generation(self):
  first=self.publish();self.store.activate_checkpoint(self.run,first['generation']);old=self.store.pointer.read_bytes();c,v=self.candidate();original=save_json
  def fail_pointer(path,data):
   if path==self.store.pointer:raise OSError('injected pointer replacement failure')
   return original(path,data)
  with patch('smb3x.client.persistence.checkpoints.save_json',side_effect=fail_pointer):
   with self.assertRaises(OSError):self.store.publish(c,v)
  self.assertEqual(self.store.pointer.read_bytes(),old);self.assertEqual(self.store.verify()[1]['generation'],first['generation'])
  self.assertTrue((self.store.root/'checkpoints'/c['generation']/'manifest.json').exists());self.assertEqual(self.store.epoch()['state'],'active')
 def test_mock_windows_rename_denials_have_bounded_attempts(self):
  first=self.publish();self.store.activate_checkpoint(self.run,first['generation']);old=self.store.pointer.read_bytes()
  for code in (5,32,33):
   with self.subTest(winerror=code):
    c,v=self.candidate();error=OSError('explicitly mocked Windows rename denial');error.winerror=code
    with patch('smb3x.client.persistence.checkpoints.os.rename',side_effect=error)as rename,patch('smb3x.client.persistence.checkpoints.time.sleep')as sleep:
     with self.assertRaises(OSError):self.store.publish(c,v)
    self.assertEqual(rename.call_count,5);self.assertEqual(sleep.call_count,4)
    self.assertEqual(self.store.pointer.read_bytes(),old);self.assertTrue((Path(c['path'])/'manifest.json').exists())
 def test_complete_prefix_empty_truncation_and_tuple_provenance(self):
  validate_prefix([],[]);validate_prefix([],[[1,2,3,4]])
  prefix=[[11,22,33,44]];validate_prefix(prefix,prefix+[[55,66,77,88]])
  for received in ([],[[12,22,33,44]],[[11,23,33,44]],[[11,22,34,44]],[[11,22,33,45]]):
   with self.subTest(received=received):
    with self.assertRaisesRegex(ValueError,'prefix'):validate_prefix(prefix,received)

if __name__=='__main__':unittest.main()

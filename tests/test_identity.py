# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch
import unittest,tempfile,json,hashlib,os,types,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
GAME='Super Mario Bros. 3: Expanded Multiworld'
class IdentityTests(unittest.TestCase):
 def test_managed_namespace(self):
  from smb3x.launcher.paths import home
  with patch.dict(os.environ,{'USERPROFILE':'C:/user','LOCALAPPDATA':'C:/isolated','SMB3_MANAGED_HOME':'C:/old'},clear=True):self.assertEqual(home(),Path('C:/isolated/SMB3XAP'))
  with patch.dict(os.environ,{'USERPROFILE':'C:/user','SMB3X_MANAGED_HOME':'C:/new','SMB3_MANAGED_HOME':'C:/old'},clear=True):self.assertEqual(home(),Path('C:/new'))
 def player(self,old=False):
  r=dict(format='smb3-m233-player-1'if old else'smb3x-player-1',seed_name='M27Test',team=0,slot=1,slot_name='Fresh',resource_id='a'*64,slot_data=dict(game=GAME,namespace='smb3x',identity_contract='smb3x-fresh-1'))
  raw=json.dumps(r).encode();m=dict(game='Super Mario Bros. 3'if old else GAME,patch='m26-native-2',persistence=3,resource_id='a'*64,player=1,player_name='Fresh',session_sha256=hashlib.sha256(raw).hexdigest());m['smb3_container'if old else'smb3x_container']=1
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'player.apsmb3x'
   with ZipFile(p,'w')as z:z.writestr('archipelago.json',json.dumps(m));z.writestr('session.json',raw)
   from smb3x.launcher.player_file import container
   return container(p)
 def test_new_container(self):self.assertEqual(self.player()[0]['game'],GAME)
 def test_old_container_refused_even_renamed(self):
  with self.assertRaises(ValueError):self.player(True)

class CacheTests(unittest.TestCase):
 def exercise(self,failures=0,winerror=32,concurrent=None):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);archive=p/'world.apworld';resources={'world/__init__.py':b'','world/registration.py':b'class SMB3World: pass\ndef register_resources(*args): pass\n'}
   raw=json.dumps({n:hashlib.sha256(b).hexdigest()for n,b in resources.items()},sort_keys=True).encode()
   with ZipFile(archive,'w')as z:
    z.writestr('smb3x/resources.json',raw)
    for n,b in resources.items():z.writestr('smb3x/resources/'+n,b)
   native=Path.rename;calls=[]
   def rename(source,target):
    calls.append((source,target))
    if concurrent:
     native(source,target)
     if concurrent=='corrupt':(target/'world/registration.py').write_text('changed')
     raise FileExistsError('concurrent fixture')
    if len(calls)<=failures:
     e=OSError('transient fixture');e.winerror=winerror;raise e
    return native(source,target)
   name='_m27bootstrap_test';module=types.ModuleType(name);module.__package__=name;module.__loader__=types.SimpleNamespace(archive=str(archive));module.__path__=[]
   oldutils=sys.modules.get('Utils');sys.modules['Utils']=types.SimpleNamespace(version_tuple=(0,6,8));sys.modules[name]=module
   try:
    with patch.dict(os.environ,{'SMB3X_MANAGED_HOME':str(p/'managed')}),patch.object(Path,'rename',rename),patch('time.sleep'):
     try:exec(compile((ROOT/'packaging/apworld_bootstrap.py').read_bytes(),'bootstrap.py','exec'),module.__dict__)
     except Exception as e:return dict(error=type(e).__name__,attempts=len(calls),pending=len(list((p/'managed/cache').glob('pending-*'))))
    return dict(attempts=len(calls),verified=all((module.RESOURCE_ROOT/n).read_bytes()==b for n,b in resources.items()))
   finally:
    if oldutils is None:sys.modules.pop('Utils',None)
    else:sys.modules['Utils']=oldutils
    for n in list(sys.modules):
     if n==name or n.startswith(name+'.'):sys.modules.pop(n)
 def test_transient_same_rename(self):self.assertEqual(self.exercise(3),dict(attempts=4,verified=True))
 def test_bounded_exhaustion_retains_pending(self):self.assertEqual(self.exercise(10),dict(error='OSError',attempts=5,pending=1))
 def test_nontransient_not_retried(self):self.assertEqual(self.exercise(10,87),dict(error='OSError',attempts=1,pending=1))
 def test_complete_concurrent_publisher(self):self.assertEqual(self.exercise(concurrent='valid'),dict(attempts=1,verified=True))
 def test_changed_concurrent_publisher_rejected(self):self.assertEqual(self.exercise(concurrent='corrupt')['error'],'RuntimeError')
if __name__=='__main__':unittest.main(verbosity=2)

# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
from unittest.mock import patch
import unittest,sys,types,tempfile,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from smb3x.launcher import windows as player
EXT='.apsmb3x';PROG='Archipelago.SMB3X.Player';CHOICE=r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.apsmb3x\UserChoice'
class Key:
 def __init__(self,r,path):self.registry,self.path=r,path
 def __enter__(self):return self
 def __exit__(self,*a):pass
class Registry:
 HKEY_CURRENT_USER=1;HKEY_CLASSES_ROOT=2;REG_SZ=1
 def __init__(self):self.values={};self.writes=[];self.deny=False
 def key(self,h,p):return (h,p)if h==1 else(1,'Software\\Classes\\'+p)
 def OpenKey(self,h,p):
  key=self.key(h,p)
  if key not in self.values and not any(k[0]==key[0]and k[1].startswith(key[1]+'\\')for k in self.values):raise FileNotFoundError()
  return Key(self,key)
 def QueryValueEx(self,k,name):
  try:return self.values[k.path][name],1
  except KeyError:raise FileNotFoundError()
 def CreateKey(self,h,p):
  if self.deny:raise PermissionError(13,'Fixture refused optional write')
  key=self.key(h,p);self.values.setdefault(key,{});return Key(self,key)
 def SetValueEx(self,k,name,reserved,kind,v):self.writes.append((k.path,name,v));self.values[k.path][name]=v
 def set(self,h,p,v,name=''):self.values.setdefault(self.key(h,p),{})[name]=v
class AssociationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.launcher=Path(self.temp.name)/'ArchipelagoLauncher.exe';self.launcher.write_bytes(b'test-only fixture');self.other=Path(self.temp.name)/'Other/ArchipelagoLauncher.exe';self.other.parent.mkdir();self.other.write_bytes(b'test-only fixture');self.reg=Registry()
 def run_registration(self,target=None):
  with patch.dict(sys.modules,{'winreg':self.reg}),patch.object(player,'association_executable',return_value=target),patch('ctypes.windll.shell32.SHChangeNotify'):
   return player.optional_association(self.launcher)
 def preserve(self,progid,target,choice=False):
  self.reg.set(1,CHOICE,progid,'ProgId')if choice else self.reg.set(2,EXT,progid)
  before=copy.deepcopy(self.reg.values);result=self.run_registration(target);self.assertEqual(self.reg.values,before);self.assertEqual(self.reg.writes,[]);return result
 def test_absent_registers_extension(self):
  self.assertEqual(self.run_registration(),'registered');self.assertEqual(self.reg.values[(1,'Software\\Classes\\'+EXT)][''],PROG)
 def test_same_launcher_different_progid_is_current(self):self.assertEqual(self.preserve('apsmb3x_auto_file',self.launcher),'already-current')
 def test_same_progid_other_launcher_is_preserved(self):self.assertEqual(self.preserve(PROG,self.other),'preserved')
 def test_unrelated_application_is_preserved(self):self.assertEqual(self.preserve('Unrelated.App',self.other),'preserved')
 def test_stale_target_preserved(self):self.assertEqual(self.preserve('Stale.App',Path(self.temp.name)/'gone.exe'),'preserved')
 def test_unresolved_target_preserved(self):self.assertEqual(self.preserve('Opaque.App',None),'preserved')
 def test_user_choice_without_classes_default_preserved(self):self.assertEqual(self.preserve('Applications\\Other.exe',self.other,True),'preserved')
 def test_user_choice_same_launcher_is_current(self):self.assertEqual(self.preserve('Applications\\ArchipelagoLauncher.exe',self.launcher,True),'already-current')
 def test_class_occupied_without_extension_not_repointed(self):
  self.reg.set(2,PROG,'Another installation');before=copy.deepcopy(self.reg.values);self.assertEqual(self.run_registration(self.other),'preserved');self.assertEqual(self.reg.values,before)
 def test_permission_refusal_is_nonfatal(self):
  self.reg.deny=True;self.assertEqual(self.run_registration(),'unavailable');self.assertFalse(self.reg.writes)
 def test_unrelated_exception_not_suppressed(self):
  with patch.object(player,'register_association',side_effect=ValueError('unrelated fixture failure')):
   with self.assertRaisesRegex(ValueError,'unrelated fixture'):player.optional_association(self.launcher)
if __name__=='__main__':unittest.main(verbosity=2)


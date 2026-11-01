# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
import importlib.util,json,hashlib,sys,types,unittest,tempfile,ast,subprocess
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
O=Path(__file__).parent
spec=importlib.util.spec_from_file_location('m28_loader_fixture',R/'src/smb3x/launcher/runtime.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
def make(root,files):
 for n,b in files.items():
  p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 raw=json.dumps({n:hashlib.sha256(b).hexdigest()for n,b in files.items()},sort_keys=True,separators=(',',':')).encode()
 (root/'resource-manifest.json').write_bytes(raw)
 return hashlib.sha256(raw).hexdigest()
class Namespace(unittest.TestCase):
 def test_minimal_normal_package_preserves_foreign_modules_and_path(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);rid=make(root,{'__init__.py':b"RUNTIME_LAYOUT='smb3x-python-1'\n",'tools/__init__.py':b'','tools/player_m233.py':b'from ..client import value\n','client/__init__.py':b'value=42\n'})
   foreign={n:types.ModuleType(n)for n in ('tools','client','apworld')}
   before=list(sys.path)
   with patch.dict(sys.modules,foreign):
    m=loader.load_player(root,rid);self.assertEqual(m.value,42);self.assertEqual(m.__name__,'smb3x_runtime_'+rid+'.tools.player_m233')
    self.assertTrue(all(sys.modules[n]is v for n,v in foreign.items()));self.assertEqual(before,sys.path)
 def test_wrong_manifest_rejects_before_module_dispatch(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);rid=make(root,{'__init__.py':b"RUNTIME_LAYOUT='smb3x-python-1'\n",'tools/player_m233.py':b'raise AssertionError("must not run")'})
   with self.assertRaisesRegex(ValueError,'identity changed'):loader.load_player(root,'0'*64)
 def test_missing_and_changed_resources_fail_closed(self):
  for mode in('missing','changed'):
   with tempfile.TemporaryDirectory()as d:
    root=Path(d);rid=make(root,{'__init__.py':b"RUNTIME_LAYOUT='smb3x-python-1'\n",'tools/player_m233.py':b'pass\n'})
    p=root/'tools/player_m233.py'
    if mode=='missing':p.unlink()
    else:p.write_bytes(b'print("foreign")')
    with self.assertRaisesRegex(ValueError,'missing/changed'):loader.load_player(root,rid)
 def test_path_escape_refused(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);raw=json.dumps({'../outside.py':'0'*64}).encode();(root/'resource-manifest.json').write_bytes(raw)
   with self.assertRaisesRegex(ValueError,'missing/changed'):loader.verify(root,hashlib.sha256(raw).hexdigest())
 def test_bad_layout_and_scoped_missing_import_do_not_fallback(self):
  for source,expected in [(b"RUNTIME_LAYOUT='foreign'\n",ValueError),(b"RUNTIME_LAYOUT='smb3x-python-1'\n",ModuleNotFoundError)]:
   with tempfile.TemporaryDirectory()as d:
    root=Path(d);rid=make(root,{'__init__.py':source,'tools/__init__.py':b'','tools/player_m233.py':b'from .missing_module import main\n'})
    foreign=types.ModuleType('tools.missing_module');foreign.main=lambda:None
    with patch.dict(sys.modules,{'tools.missing_module':foreign}):
     with self.assertRaises(expected):loader.load_player(root,rid)
     self.assertIs(sys.modules['tools.missing_module'],foreign)
 def test_foreign_private_prefix_and_player_ownership_refused(self):
  for occupied in('package','player'):
   with tempfile.TemporaryDirectory()as d:
    root=Path(d);rid=make(root,{'__init__.py':b"RUNTIME_LAYOUT='smb3x-python-1'\n",'tools/__init__.py':b'','tools/player_m233.py':b'pass\n'})
    name='smb3x_runtime_'+rid+(''if occupied=='package'else'.tools.player_m233');foreign=types.ModuleType(name);foreign.__file__='foreign.py'
    with patch.dict(sys.modules,{name:foreign}):
     with self.assertRaisesRegex(ValueError,'Foreign module|ownership mismatch'):loader.load_player(root,rid)
     self.assertIs(sys.modules[name],foreign)
 def test_historical_worker_never_replaces_foreign_generic_modules(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);rid=make(root,{'tools/player_m233.py':b'raise AssertionError("not selected")'})
   foreign=types.ModuleType('tools');foreign.__file__='foreign.py'
   with patch.dict(sys.modules,{'tools':foreign}):
    with self.assertRaisesRegex(ValueError,'Another world owns'):loader._historical_worker_impl((),root,rid)
    self.assertIs(sys.modules['tools'],foreign)
 def test_historical_worker_uses_exact_original_source(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);rid=make(root,{'tools/player_m233.py':b'def main(args,root,rid):return (args,str(root),rid)\n','client/__init__.py':b''})
   # Dedicated worker process isolation is exercised in real frozen testing;
   # this model must not touch the unit-test process's existing generic modules.
   script="import importlib.util;from pathlib import Path;s=importlib.util.spec_from_file_location('fixture',"+repr(str(R/'src/smb3x/launcher/runtime.py'))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);assert m._historical_worker_impl(('old',),Path("+repr(str(root))+"),"+repr(rid)+")[0]==('old',)"
   p=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
if __name__=='__main__':unittest.main()

# SPDX-License-Identifier: MPL-2.0
"""Public tests use synthetic data, never private catalogue or seed records."""
from pathlib import Path
import ast, hashlib, importlib.util, json, runpy, tempfile, unittest
R=Path(__file__).resolve().parents[1]

def module(path):
 s=importlib.util.spec_from_file_location('boundary_fixture',path)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class Boundaries(unittest.TestCase):
 def test_native_music_does_not_read_private_metadata(self):
  m=vars(__import__('smb3x.planning.music',fromlist=['plan']))
  for mode in ('vanilla','shuffled'):
   p=m['plan']('synthetic-release-test',{}, {},mode)
   self.assertEqual(p['selected'],[]);self.assertIsNone(p['catalogue_id'])
 def test_custom_music_without_provider_refuses(self):
  m=vars(__import__('smb3x.planning.music',fromlist=['plan']))
  # No private build binding is in the public source tree.
  self.assertFalse(m['CATALOGUE'].available())
  for mode in ('custom_mixed','custom_only'):
   with self.assertRaisesRegex(ValueError,'separately versioned private build'):
    m['plan']('synthetic-release-test',{}, {},mode)
 def test_provider_requires_exact_resource_hash(self):
  text=(R/'src/smb3x/planning/music.py').read_text()
  tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='_PrivateCatalogue')
  from collections.abc import Mapping
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);ns=dict(ROOT=root,Mapping=Mapping,json=json,hashlib=hashlib,PRIVATE_PROVIDER_ENABLED=True,PRIVATE_UNAVAILABLE="public build")
   exec(compile(ast.Module(body=[node],type_ignores=[]),'provider-fixture','exec'),ns)
   raw=b'{"tracks":[],"id":"synthetic-provider"}'
   (root/'music_catalogue_m244.json').write_bytes(raw)
   (root/'private_music_provider.json').write_text(json.dumps(dict(format='smb3x-private-music-provider-1',catalogue_sha256='0'*64)))
   with self.assertRaisesRegex(ValueError,'integrity mismatch'):ns['_PrivateCatalogue']()['tracks']
   (root/'private_music_provider.json').write_text(json.dumps(dict(format='smb3x-private-music-provider-1',catalogue_sha256=hashlib.sha256(raw).hexdigest())))
   self.assertEqual(ns['_PrivateCatalogue']()['tracks'],[])
   ns['PRIVATE_PROVIDER_ENABLED']=False
   self.assertFalse(ns['_PrivateCatalogue']().available())
   with self.assertRaisesRegex(ValueError,'public build'):ns['_PrivateCatalogue']()['tracks']
 def test_preparation_has_no_private_seed_policy_dependency(self):
  recipe=json.loads((R/'packaging/resources.json').read_bytes())
  for name,row in recipe['resources'].items():
   self.assertNotIn('historical-seeds',name)
   if name=='launcher/artifacts.py':
    text=(R/row['source']).read_text()
    self.assertNotIn('historical-seeds',text)
    self.assertIn('verify_base',text)
 def test_helpers_keep_existing_output_refusal(self):
  m=module(R/'src/smb3x/launcher/artifact_files.py')
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaisesRegex(ValueError,'already exists'):m.fresh(Path(d))
 def test_package_contains_current_client_and_no_standalone_ancestors(self):
  recipe=json.loads((R/'packaging/resources.json').read_bytes())
  self.assertIn('client/network.py',recipe['resources'])
  self.assertIn('client/service.py',recipe['resources'])
  self.assertFalse(any(n.startswith('client/run_') for n in recipe['resources']))

if __name__=='__main__':unittest.main()

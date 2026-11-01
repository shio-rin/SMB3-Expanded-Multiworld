# SPDX-License-Identifier: MPL-2.0
"""Modern 53-stage graph contracts; no historical shuffle implementation needed."""
from pathlib import Path
from runpy import run_path
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
M=vars(__import__('smb3x.planning.stages',fromlist=['assignments']))
class Shuffle(unittest.TestCase):
 def test_full_pool_retains_all_originally_certified_stages(self):
  rows=M['pool']();self.assertEqual(len(rows),53)
  old=json.loads((R/'src/smb3x/planning/data/contents_m18.json').read_bytes())
  ids={r['content_id']for r in old['contents']if r['certified']}
  self.assertEqual(len(ids),12);self.assertTrue(ids<={r['content_id']for r in rows})
 def test_modes_enforce_technical_graph_and_balanced_distance_only(self):
  distant=0
  for i in range(8):
   for mode in ('vanilla','balanced','compatible'):
    plan=M['assignments']('M31-graph-'+str(i),mode);M['validate'](plan,'M31-graph-'+str(i))
    for row in plan['assignments']:
     source=M['CONTENTS'][row['assigned_content']]
     self.assertIn(row['original_content'],source['technical_destinations'])
     distance=abs(row['source_world']-row['destination_world'])
     if mode=='balanced':self.assertLessEqual(distance,1)
     if mode=='compatible':distant+=distance>1
     if mode=='vanilla':self.assertEqual(row['original_content'],row['assigned_content'])
    self.assertNotIn('shuffle_pool',plan);self.assertNotIn('balanced_policy_selector',plan)
  self.assertGreater(distant,0)
 def test_compatible_graph_ignores_difficulty_annotations(self):
  rows=M['pool']();a=M['allowed_graph'](rows,False)
  altered=[{**r,'difficulty':'arbitrary changed annotation'}for r in rows]
  self.assertEqual(a,M['allowed_graph'](altered,False))
  self.assertEqual(a,{d['content_id']:[c['content_id']for c in rows if d['content_id']in c['technical_destinations']]for d in rows})
 def test_special_and_mixed_contracts_remain_valid(self):
  for mode in ('balanced','compatible'):
   for setting in ('by_type','mixed_fortresses'):
    plan=M['assignments']('M31-special-safety',mode,special_stage_shuffle=setting)
    M['validate'](plan,'M31-special-safety')
    self.assertEqual(plan['special_stage_shuffle']['setting'],setting)
 def test_removed_algorithms_and_policy_are_not_in_recipe(self):
  recipe=json.loads((R/'packaging/resources.json').read_bytes())['resources']
  for version in ('m18','m19','m191','m21','m22','m221'):self.assertNotIn('src/smb3x/planning/data/shuffle_'+version+'.py',recipe)
  self.assertNotIn('src/smb3x/planning/data/balanced_m221.json',recipe)
 def test_data_catalogue_preserves_parent_guard(self):
  cat=__import__('smb3x.planning.catalogue',fromlist=['catalogue']).catalogue
  for version in ('m18','m19','m21','m22'):
   row=cat(version);self.assertEqual(row['REGISTRY_HASH'],hashlib.sha256((R/('src/smb3x/planning/data/contents_'+version+'.json')).read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()

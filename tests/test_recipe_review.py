# SPDX-License-Identifier: MPL-2.0
"""Source review must be explicit and must never approve native certificates."""
from pathlib import Path
from unittest.mock import patch
import json,tempfile,unittest
from tools import update_recipe as recipe

class RecipeReview(unittest.TestCase):
    def fixture(self,root,source):
        p=root/source;p.parent.mkdir(parents=True);p.write_text('changed\n')
        manifest=root/'packaging/resources.json';manifest.parent.mkdir()
        row=dict(source=source,transform='lf',source_lf_sha256='0'*64,output_sha256='0'*64)
        manifest.write_text(json.dumps(dict(resources={'example':row},outer={})))
        return manifest

    def test_proposal_identifies_input_output_and_rejects_stale_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest=self.fixture(root,'src/smb3x/shared/example.py')
            with patch.object(recipe,'ROOT',root),patch.object(recipe,'RECIPE',manifest):
                proposal=recipe.propose();row=proposal['changes'][0]
                self.assertEqual(row['resource'],'example')
                self.assertNotEqual(row['old'],row['new'])
                (root/row['source']).write_text('changed again\n')
                with self.assertRaisesRegex(ValueError,'changed since review'):recipe.apply(proposal)

    def test_certificate_is_reported_but_cannot_be_approved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest=self.fixture(root,'src/smb3x/native/certificates/example.json')
            before=manifest.read_bytes()
            with patch.object(recipe,'ROOT',root),patch.object(recipe,'RECIPE',manifest):
                proposal=recipe.propose()
                self.assertTrue(proposal['changes'][0]['requires_native_verification'])
                with self.assertRaisesRegex(ValueError,'cannot approve'):recipe.apply(proposal)
            self.assertEqual(manifest.read_bytes(),before)

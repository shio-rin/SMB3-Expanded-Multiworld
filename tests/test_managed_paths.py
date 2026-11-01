# SPDX-License-Identifier: MPL-2.0
"""Real Windows filesystem boundaries and failure-preserving atomic writes."""
from pathlib import Path
import json,os,tempfile,unittest
from unittest.mock import patch
from smb3x.client.persistence.atomic import save_json, publish_directory
from smb3x.launcher.paths import preflight_session
from smb3x.shared.path_limits import validate_file_path

class ManagedPaths(unittest.TestCase):
    def test_prepared_directory_retries_same_verified_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'candidate';source.mkdir();(source/'verified').write_text('exact')
            native=Path.rename;calls=[]
            def rename(path,target):
                calls.append((path,target))
                if len(calls)<3:
                    error=PermissionError('sharing fixture');error.winerror=5;raise error
                return native(path,target)
            with patch.object(Path,'rename',rename),patch('smb3x.client.persistence.atomic.time.sleep'):
                publish_directory(source,root/'prepared')
            self.assertEqual(len(calls),3);self.assertEqual(len(set(calls)),1)
            self.assertEqual((root/'prepared/verified').read_text(),'exact')

    def test_prepared_directory_exhaustion_keeps_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'candidate';source.mkdir()
            error=PermissionError('sharing fixture');error.winerror=32
            with patch.object(Path,'rename',side_effect=error)as rename,patch('smb3x.client.persistence.atomic.time.sleep'):
                with self.assertRaisesRegex(OSError,'candidate was retained'):publish_directory(source,root/'prepared')
                self.assertEqual(rename.call_count,5)
            self.assertTrue(source.is_dir());self.assertFalse((root/'prepared').exists())

    def test_prepared_directory_never_replaces_existing_target(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'candidate';source.mkdir();target=root/'prepared';target.mkdir()
            with patch.object(Path,'rename')as rename:
                with self.assertRaises(FileExistsError):publish_directory(source,target)
                rename.assert_not_called()

    def test_short_write_and_replace_preserve_complete_json(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'journal.json'
            save_json(p,{'index':1});save_json(p,{'index':2})
            self.assertEqual(json.loads(p.read_bytes()),{'index':2})
            self.assertFalse(list(p.parent.glob('*.pending')))

    def test_replace_failure_retains_old_data_and_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'journal.json';save_json(p,{'index':1})
            with patch('smb3x.client.persistence.atomic.os.replace',side_effect=OSError('disk fixture')):
                with self.assertRaisesRegex(OSError,'No native operation was retried'):
                    save_json(p,{'index':2})
            self.assertEqual(json.loads(p.read_bytes()),{'index':1})
            pending=list(p.parent.glob('j-*.pending'));self.assertEqual(len(pending),1)
            self.assertEqual(json.loads(pending[0].read_bytes()),{'index':2})

    def test_sharing_retry_is_bounded_and_same_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'journal.json';save_json(p,{'index':1})
            error=OSError('locked');error.winerror=32
            with patch('smb3x.client.persistence.atomic.os.replace',side_effect=error)as replace,patch('smb3x.client.persistence.atomic.time.sleep')as sleep:
                with self.assertRaises(OSError):save_json(p,{'index':2})
            self.assertEqual(replace.call_count,5);self.assertEqual(sleep.call_count,4)
            self.assertEqual(len({str(c.args[0])for c in replace.call_args_list}),1)
            self.assertEqual(json.loads(p.read_bytes()),{'index':1})

    @unittest.skipUnless(os.name=='nt','Windows boundary')
    def test_target_250_succeeds_with_short_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            parent=Path(directory)/('p'*(180-len(directory)-1))
            p=parent/('q'*(250-len(str(parent))-6)+'.json')
            self.assertEqual(len(str(p)),250)
            save_json(p,{'ok':True});self.assertEqual(json.loads(p.read_bytes()),{'ok':True})

    @unittest.skipUnless(os.name=='nt','Windows boundary')
    def test_final_path_and_session_refuse_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            parent=Path(directory)/('p'*100)/('q'*100)
            with self.assertRaisesRegex(ValueError,'too long'):save_json(parent/('r'*64+'.json'),{})
            self.assertFalse(parent.exists())
            with self.assertRaisesRegex(ValueError,'too long'):preflight_session(parent)
            self.assertFalse(parent.exists())

if __name__=='__main__':unittest.main()

# SPDX-License-Identifier: MPL-2.0
"""Known incompatibilities are actionable; unknown failures retain tracebacks."""
import io,logging,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from smb3x.launcher import player,dialogs,emulator,preferences
from smb3x.shared.emulators import EmulatorCompatibilityError

class LauncherErrors(unittest.TestCase):
    def test_frontend_failure_precedes_session_epoch_and_orphan_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game=root/'game';game.mkdir();session=root/'session';session.mkdir()
            (game/emulator.ROM_FILENAME).write_bytes(b'verified fixture')
            for name in ('json.lua','x64/socket-windows-5-1.dll','x64/socket-windows-5-4.dll'):
                path=root/name;path.parent.mkdir(exist_ok=True);path.write_bytes(b'fixture')
            with patch.dict(sys.modules,{'Utils':types.SimpleNamespace(local_path=lambda *a:str(root))}),patch('smb3x.launcher.artifacts.verify_game',return_value=(b'verified fixture',{},{})),patch.object(emulator,'emulator_identity',return_value={'profile':'2.10'}),patch.object(emulator,'managed_configuration',return_value=(root/'config',preferences.configuration())),patch.object(emulator,'verify_frontend',side_effect=EmulatorCompatibilityError('OpenAL mismatch')),patch('smb3x.client.persistence.checkpoints.CheckpointStore') as store,patch.object(emulator,'retire_orphan') as retire:
                with self.assertRaisesRegex(EmulatorCompatibilityError,'OpenAL'):
                    emulator.play(root,'unused',session,game,root/'original',root/'EmuHawk.exe','unused',None)
                store.assert_not_called();retire.assert_not_called()
                self.assertEqual(list(session.iterdir()),[])

    def test_bad_remembered_path_can_select_another_without_losing_reason(self):
        with tempfile.TemporaryDirectory() as d, patch.object(player,'emulator_identity',side_effect=[EmulatorCompatibilityError('Missing critical files: dll/lua54.dll'),{'profile':'2.10'}]), patch.object(player,'require_session_emulator'), patch.object(player,'confirm',return_value=True) as confirm, patch.object(player,'select',return_value=Path('correct.exe')) as select:
            self.assertEqual(player.select_emulator(Path(d),'old.exe'),Path('correct.exe'))
            self.assertIn('dll/lua54.dll',confirm.call_args.args[0]);select.assert_called_once()

    def test_repeated_bad_selection_requires_explicit_retry_and_no_stops(self):
        with tempfile.TemporaryDirectory() as d, patch.object(player,'emulator_identity',side_effect=EmulatorCompatibilityError('modified executable')), patch.object(player,'confirm',side_effect=[True,False]) as confirm, patch.object(player,'select',return_value=Path('bad.exe')) as select:
            self.assertIsNone(player.select_emulator(Path(d),'bad.exe'))
            self.assertEqual(confirm.call_count,2);select.assert_called_once()

    def test_unknown_validation_exception_is_not_masked_as_compatibility(self):
        with tempfile.TemporaryDirectory() as d, patch.object(player,'emulator_identity',side_effect=RuntimeError('unexpected implementation error')), patch.object(player,'confirm') as confirm:
            with self.assertRaisesRegex(RuntimeError,'unexpected'):
                player.select_emulator(Path(d),'bad.exe')
            confirm.assert_not_called()

    def test_expected_main_failure_has_one_dialog_no_escape_and_file_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);log=logging.FileHandler(root/'diagnostic.log');stream=io.StringIO();console=logging.StreamHandler(stream)
            logger=logging.getLogger();old=logger.handlers[:];logger.handlers=[log,console]
            box=Mock()
            try:
                with patch.dict(sys.modules,{'Utils':types.SimpleNamespace(messagebox=box)}),patch.object(player,'home',return_value=root),patch.object(player,'container',side_effect=EmulatorCompatibilityError('critical component differs')):
                    player.main(['test.apsmb3x'],root,'unused')
                box.assert_called_once();log.flush()
                self.assertIn('critical component differs',box.call_args.args[1])
                self.assertIn('Traceback', (root/'diagnostic.log').read_text())
                self.assertNotIn('Traceback',stream.getvalue())
            finally:
                logger.handlers=old;log.close();console.close()

    def test_unknown_main_failure_still_raises(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'Utils':types.SimpleNamespace(messagebox=Mock())}),patch.object(player,'home',return_value=Path(d)),patch.object(player,'container',side_effect=RuntimeError('unexpected')):
            with self.assertRaisesRegex(RuntimeError,'unexpected'):
                player.main(['test.apsmb3x'],Path(d),'unused')

    def test_cancel_setup_is_quiet_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'existing.txt').write_text('untouched');box=Mock()
            with patch.dict(sys.modules,{'Utils':types.SimpleNamespace(messagebox=box)}),patch.object(player,'home',return_value=root),patch.object(player,'select',side_effect=dialogs.SetupCancelled('Selection cancelled')):
                player.main([],root,'unused')
            box.assert_not_called();self.assertEqual((root/'existing.txt').read_text(),'untouched')

# SPDX-License-Identifier: MPL-2.0
"""Physical-ROM launch boundary, with patch verification and native State mocked.

The valid control reaches process creation. Invalid files must fail before it.
No commercial ROM, emulator, server or private fixture is needed.
"""
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch, Mock
import sys
import tempfile
import types
import unittest
from smb3x.launcher import emulator, artifacts
from smb3x.client.persistence import checkpoints

class ProcessBoundary(Exception):
    pass

class RomLaunchTests(unittest.TestCase):
    def run_case(self, mode):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            root = Path(folder)
            game = root / 'game'
            game.mkdir()
            live = root / 'live'
            live.mkdir()
            expected = b'explicit synthetic reconstructed bytes'
            if mode != 'missing':
                (game / emulator.ROM_FILENAME).write_bytes(expected if mode == 'valid' else b'corrupt')
            lua = root / 'lua'
            for name in ('json.lua', 'x64/socket-windows-5-1.dll', 'x64/socket-windows-5-4.dll'):
                path = lua / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'fixture')
            stack.enter_context(patch.dict(sys.modules, {'Utils': types.SimpleNamespace(local_path=lambda *args: str(lua))}))
            verify = stack.enter_context(patch.object(artifacts, 'verify_game', return_value=(expected, {}, {})))
            stack.enter_context(patch.object(emulator, 'configuration', return_value={'StartPaused': False}))
            stack.enter_context(patch.object(emulator, 'emulator_identity', return_value={'profile': '2.10'}))
            stack.enter_context(patch.object(emulator, 'binding', return_value={'location_ids': []}))
            store = Mock(root=root / 'saves', recovery=None)
            store.new_run.return_value = ('a' * 32, live)
            stack.enter_context(patch.object(checkpoints, 'CheckpointStore', return_value=store))
            stack.enter_context(patch.object(emulator, 'retire_orphan'))
            stack.enter_context(patch.object(emulator, 'managed_configuration', return_value=(root / 'config', {'StartPaused': False})))
            spawn = stack.enter_context(patch.object(emulator.subprocess, 'Popen', side_effect=ProcessBoundary))
            exception = ProcessBoundary if mode == 'valid' else FileNotFoundError if mode == 'missing' else ValueError
            with self.assertRaises(exception):
                emulator.play(root, 'resource', root, game, root / 'original', root / 'EmuHawk.exe', 'room', None)
            verify.assert_called_once_with(game, root / 'original')
            self.assertEqual(spawn.call_count, int(mode == 'valid'))
            if mode == 'valid':
                self.assertEqual(spawn.call_args.args[0][-1], str(game / emulator.ROM_FILENAME))

    def test_valid_rom_reaches_process_creation(self):
        self.run_case('valid')

    def test_missing_rom_never_starts_emulator(self):
        self.run_case('missing')

    def test_corrupt_rom_never_starts_emulator(self):
        self.run_case('corrupt')

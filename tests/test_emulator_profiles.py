# SPDX-License-Identifier: MPL-2.0
"""Profile ownership and State/config refusal; native qualification is separate."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from smb3x.shared import emulators
from smb3x.launcher import preferences, emulator, player
from smb3x.client.persistence.checkpoints import validate_state_container


def identity(version):
    return dict(profile=version, revision=emulators.profile(version)['revision'], core='NesHawk')


class EmulatorProfileTests(unittest.TestCase):
    def test_fresh_session_can_replace_valid_remembered_emulator(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(player, 'emulator_identity', return_value=identity('2.11')), \
                patch.object(player, 'confirm', return_value=False) as confirm, \
                patch.object(player, 'select', return_value=Path('new.exe')) as select:
            result = player.select_emulator(Path(folder), 'remembered.exe')
            self.assertEqual(result, Path('new.exe'))
            confirm.assert_called_once()
            select.assert_called_once()

    def test_existing_session_does_not_offer_a_version_switch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'emulator-identity.json').write_text(json.dumps(identity('2.11')))
            with patch.object(player, 'emulator_identity', return_value=identity('2.11')), \
                    patch.object(player, 'confirm') as confirm, patch.object(player, 'select') as select:
                self.assertEqual(player.select_emulator(root, 'owned.exe'), Path('owned.exe'))
                confirm.assert_not_called()
                select.assert_not_called()

    def test_each_configuration_matches_its_profile_only(self):
        for version in emulators.profiles():
            config = preferences.configuration(version)
            preferences.validate_configuration(config, version)
            for other in emulators.profiles():
                if other != version:
                    with self.assertRaisesRegex(ValueError, 'configuration version'):
                        preferences.validate_configuration(config, other)

    def test_wrong_core_and_sync_settings_reject(self):
        for version in emulators.profiles():
            config = preferences.configuration(version)
            config['PreferredCores']['NES'] = 'QuickNes'
            with self.assertRaisesRegex(ValueError, 'core/sync'):
                preferences.validate_configuration(config, version)
            config = preferences.configuration(version)
            config['CoreSyncSettings'][preferences.NES_CORE]['RegionOverride'] = 1
            with self.assertRaisesRegex(ValueError, 'core/sync'):
                preferences.validate_configuration(config, version)

    def test_unknown_profiles_refused(self):
        for version in ('2.9.1', '99.0', None):
            with self.assertRaisesRegex(ValueError, 'Unsupported emulator profile'):
                emulators.profile(version)

    def test_modified_executable_refused(self):
        with patch.object(emulators, 'sha', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'Unrecognized or modified'):
                emulators.identify(Path('EmuHawk.exe'))

    def test_missing_dll_refused_even_with_correct_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            for profile in emulators.profiles().values():
                with patch.object(emulators, 'sha', return_value=profile['files']['EmuHawk.exe']):
                    with self.assertRaisesRegex(ValueError, 'core/runtime integrity'):
                        emulators.identify(Path(folder) / 'EmuHawk.exe')

    def test_cross_version_refusal_retains_all_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'emulator-identity.json'
            for version in emulators.profiles():
                path.write_text(json.dumps(identity(version)))
                before = path.read_bytes()
                emulator.require_session_emulator(root, identity(version))
                for other in emulators.profiles():
                    if other != version:
                        with self.assertRaisesRegex(ValueError, 'Cross-version Resume'):
                            emulator.require_session_emulator(root, identity(other))
                        self.assertEqual(path.read_bytes(), before)
                        self.assertEqual(list(root.iterdir()), [path])

    def test_missing_session_owner_never_infers_from_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'saves').mkdir()
            (root / 'saves/EPOCH.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'ownership record is missing'):
                emulator.require_session_emulator(root, identity('2.10'))

    def test_state_version_and_member_are_bound_not_inferred(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'native.State'
            for version, profile in emulators.profiles().items():
                with ZipFile(path, 'w') as archive:
                    archive.writestr(profile['state_core'], bytes.fromhex('28b52ffd') + b'explicitly mocked core')
                    archive.writestr('BizVersion.txt', profile['state_version'])
                    archive.writestr('UserData.txt', json.dumps({'o': {'smb3.m233.generation': 'marker'}}))
                    if profile['state_sync']:
                        archive.writestr('SyncSettings.json', json.dumps({'o': preferences.configuration(version)['CoreSyncSettings'][preferences.NES_CORE]}))
                validate_state_container(path, 'marker', identity(version))
                for other in emulators.profiles():
                    if other != version:
                        with self.assertRaises(ValueError):
                            validate_state_container(path, 'marker', identity(other))
                with self.assertRaisesRegex(ValueError, 'generation marker'):
                    validate_state_container(path, 'foreign', identity(version))

    def test_new_state_sync_settings_cannot_change_core_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'native.State'
            for version in ('2.11', '2.11.1'):
                selected = emulators.profile(version)
                sync = preferences.configuration(version)['CoreSyncSettings'][preferences.NES_CORE]
                sync['RegionOverride'] = 1
                with ZipFile(path, 'w') as archive:
                    archive.writestr(selected['state_core'], bytes.fromhex('28b52ffd') + b'mock')
                    archive.writestr('BizVersion.txt', selected['state_version'])
                    archive.writestr('UserData.txt', json.dumps({'o': {'smb3.m233.generation': 'marker'}}))
                    archive.writestr('SyncSettings.json', json.dumps({'o': sync}))
                with self.assertRaisesRegex(ValueError, 'sync settings differ'):
                    validate_state_container(path, 'marker', identity(version))

    def test_missing_lua_api_refused_before_bridge_startup(self):
        from lupa import LuaRuntime
        lua = LuaRuntime()
        lua.execute('client={getversion=function() return "2.11" end}; memory={}')
        source = (Path(__file__).parents[1] / 'src/smb3x/bizhawk/bridge.lua').read_text()
        with self.assertRaisesRegex(Exception, 'Required memory API missing'):
            lua.execute(source, lua.table_from(dict(emulator_version='2.11', lua_version='Lua 5.4')))

    def test_preference_roots_separate_versions_at_same_path(self):
        roots = []
        for version in emulators.profiles():
            with patch.object(preferences, 'identify', return_value=emulators.profile(version)):
                roots.append(preferences.profile_root('EmuHawk.exe'))
        self.assertEqual(len(set(roots)), 3)

    def test_late_close_merge_preserves_newer_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'preferences.json'
            path.write_text(json.dumps(dict(schema=1, values={'SoundVolume': 80, 'StartPaused': False})))
            conflicts = preferences.merge_preferences(root, {'SoundVolume': 50, 'StartPaused': False},
                                                      {'SoundVolume': 60, 'StartPaused': True})
            self.assertEqual(conflicts, ['SoundVolume'])
            self.assertEqual(json.loads(path.read_text())['values'], {'SoundVolume': 80, 'StartPaused': True})

    def test_lua_rejects_disagreement_before_memory_access(self):
        from lupa import LuaRuntime
        lua = LuaRuntime()
        lua.execute('client={getversion=function() return "2.11" end}; memory={}')
        source = (Path(__file__).parents[1] / 'src/smb3x/bizhawk/bridge.lua').read_text()
        with self.assertRaisesRegex(Exception, 'differs from the verified session'):
            lua.execute(source, lua.table_from(dict(emulator_version='2.10', lua_version='Lua 5.4')))

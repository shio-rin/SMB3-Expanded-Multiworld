# SPDX-License-Identifier: MPL-2.0
"""Profile ownership and State/config refusal; native qualification is separate."""
import json
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
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


@contextmanager
def installation(version, languages=()):
    """Real filesystem/hash validation with explicitly synthetic binary contents."""
    selected = deepcopy(emulators.profile(version))
    required = {name: (version + ':' + name).encode() for name in (
        'EmuHawk.exe', 'dll/BizHawk.Emulation.Cores.dll', 'dll/System.CommandLine.dll')}
    optional = {name: (version + ':' + name).encode() for name in selected['optional_files']}
    selected['files'] = {n: sha256(b).hexdigest() for n, b in required.items()}
    selected['optional_files'] = {n: sha256(b).hexdigest() for n, b in optional.items()}
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for name, data in {**required, **{n: optional[n] for n in languages}}.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        with patch.object(emulators, 'profiles', return_value={version: selected}):
            yield root, selected, optional


class OptionalLocalizationTests(unittest.TestCase):
    def test_official_installation_without_satellites_is_accepted(self):
        for version in emulators.profiles():
            with self.subTest(version=version), installation(version) as (root, selected, _):
                self.assertEqual(emulators.identify(root / 'EmuHawk.exe'), selected)

    def test_all_reviewed_languages_and_each_individual_language_are_optional(self):
        for version, selected in emulators.profiles().items():
            names = list(selected['optional_files'])
            for present in (names, *([n] for n in names)):
                with self.subTest(version=version, present=present), installation(version, present) as (root, expected, _):
                    self.assertEqual(emulators.identify(root / 'EmuHawk.exe'), expected)

    def test_optional_language_removal_preserves_exact_session_identity(self):
        for version, selected in emulators.profiles().items():
            with self.subTest(version=version), installation(version, selected['optional_files']) as (root, _, optional):
                before = emulator.emulator_identity(root / 'EmuHawk.exe')
                (root / 'emulator-identity.json').write_text(json.dumps(before))
                for name in optional:
                    (root / name).unlink()
                after = emulator.emulator_identity(root / 'EmuHawk.exe')
                self.assertEqual(before, after)
                emulator.require_session_emulator(root, after)

    def test_missing_required_runtime_is_not_made_optional(self):
        for version in emulators.profiles():
            for missing in ('dll/BizHawk.Emulation.Cores.dll', 'dll/System.CommandLine.dll'):
                with self.subTest(version=version, missing=missing), installation(version) as (root, _, _):
                    (root / missing).unlink()
                    with self.assertRaisesRegex(ValueError, 'Missing required files') as caught:
                        emulators.identify(root / 'EmuHawk.exe')
                    self.assertIn(missing, str(caught.exception))

    def test_modified_required_core_and_dependency_are_rejected(self):
        for version in emulators.profiles():
            for changed in ('dll/BizHawk.Emulation.Cores.dll', 'dll/System.CommandLine.dll'):
                with self.subTest(version=version, changed=changed), installation(version) as (root, _, _):
                    (root / changed).write_bytes(b'modified core or runtime')
                    with self.assertRaisesRegex(ValueError, 'Modified required files'):
                        emulators.identify(root / 'EmuHawk.exe')

    def test_modified_optional_resources_are_rejected(self):
        for version, selected in emulators.profiles().items():
            with self.subTest(version=version), installation(version, selected['optional_files']) as (root, _, optional):
                (root / next(iter(optional))).write_bytes(b'not the approved satellite')
                with self.assertRaisesRegex(ValueError, 'Modified optional language resources'):
                    emulators.identify(root / 'EmuHawk.exe')

    def test_unapproved_binaries_and_resource_names_are_rejected(self):
        for version in emulators.profiles():
            for extra in ('dll/puae.wbx.zst', 'dll/extra.dll', 'dll/other.exe',
                          'dll/de/Other.resources.dll', 'dll/xx/System.CommandLine.resources.dll',
                          'dll/de/nested/System.CommandLine.resources.dll'):
                with self.subTest(version=version, extra=extra), installation(version) as (root, _, _):
                    path = root / extra
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'unapproved binary')
                    with self.assertRaisesRegex(ValueError, 'Unapproved additional files') as caught:
                        emulators.identify(root / 'EmuHawk.exe')
                    self.assertIn(extra, str(caught.exception))

    def test_every_difference_is_reported_without_first_three_truncation(self):
        for version, selected in emulators.profiles().items():
            with self.subTest(version=version), installation(version, selected['optional_files']) as (root, _, optional):
                (root / 'dll/BizHawk.Emulation.Cores.dll').unlink()
                (root / 'dll/System.CommandLine.dll').write_bytes(b'changed')
                (root / next(iter(optional))).write_bytes(b'changed')
                extras = ['dll/extra' + str(i) + '.dll' for i in range(5)]
                for name in extras:
                    (root / name).write_bytes(b'extra')
                with self.assertRaises(ValueError) as caught:
                    emulators.identify(root / 'EmuHawk.exe')
                message = str(caught.exception)
                for name in (*extras, 'dll/BizHawk.Emulation.Cores.dll', 'dll/System.CommandLine.dll', next(iter(optional))):
                    self.assertIn(name, message)
                self.assertIn('Unapproved additional files (5)', message)

    def test_executable_substitution_is_still_rejected(self):
        for version in emulators.profiles():
            with self.subTest(version=version), installation(version) as (root, _, _):
                (root / 'EmuHawk.exe').write_bytes(b'wrong executable')
                with self.assertRaisesRegex(ValueError, 'Unrecognized or modified'):
                    emulators.identify(root / 'EmuHawk.exe')

    def test_optional_provenance_matches_each_required_dependency(self):
        for selected in emulators.profiles().values():
            self.assertEqual(len(selected['optional_files']), 13)
            self.assertFalse(selected['files'].keys() & selected['optional_files'].keys())
            self.assertEqual(selected['optional_files_source']['parent_sha256'],
                             selected['files']['dll/System.CommandLine.dll'])


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

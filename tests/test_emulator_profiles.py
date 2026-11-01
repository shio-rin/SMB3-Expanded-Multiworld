# SPDX-License-Identifier: MPL-2.0
"""Dependency verification, install variability, session and error contracts."""
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
def installation(version):
    """Real file/hash checks with synthetic dependency bytes, never real ROMs."""
    selected = deepcopy(emulators.profile(version))
    names = ('EmuHawk.exe', 'dll/BizHawk.Emulation.Cores.dll', 'dll/System.CommandLine.dll',
             'dll/NLua.dll', 'dll/lua54.dll', 'dll/libzstd.dll')
    data = {n: (version + ':' + n).encode() for n in (*names, 'dll/unrelated.wbx.zst', 'dll/OpenAL32.dll')}
    selected['files'] = {n: sha256(b).hexdigest() for n, b in data.items()}
    selected['validation_files'] = list(names)
    selected['managed_files'] = ['dll/BizHawk.Emulation.Cores.dll', 'dll/System.CommandLine.dll', 'dll/NLua.dll']
    selected['frontend_files'] = ['dll/OpenAL32.dll']
    config = b'<configuration><runtime><assemblyBinding xmlns="urn:schemas-microsoft-com:asm.v1" /></runtime></configuration>'
    selected['loader_config_sha256'] = emulators.loader_policy(config)
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for n, b in data.items():
            target = root / n
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b)
        (root / 'EmuHawk.exe.config').write_bytes(config)
        with patch.object(emulators, 'profiles', return_value={version: selected}):
            yield root, selected


class DependencyInstallationTests(unittest.TestCase):
    def test_complete_installation(self):
        for v in emulators.profiles():
            with installation(v) as (root, expected):
                self.assertEqual(emulators.identify(root / 'EmuHawk.exe'), expected)

    def test_arbitrary_extras_are_not_enumerated_or_hashed(self):
        for v in emulators.profiles():
            with installation(v) as (root, expected):
                extras = ('dll/puae.wbx.zst', 'dll/othercore.wbx.zst', 'dll/extra.dll', 'plugins/a.dll',
                          'dll/zz/Whatever.resources.dll', 'dll/cs/System.CommandLine.resources.dll',
                          'unrelated.exe', 'dll/notes.txt')
                for name in extras:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'unrelated content is not an execution dependency')
                with patch.object(emulators, 'sha', wraps=emulators.sha) as digest, \
                     patch.object(Path, 'rglob', side_effect=AssertionError('no inventory scan')):
                    self.assertEqual(emulators.identify(root / 'EmuHawk.exe'), expected)
                checked = {str(call.args[0]) for call in digest.call_args_list}
                self.assertFalse(checked & {str(root / n) for n in extras})

    def test_missing_unrelated_components_and_changed_extras_preserve_identity(self):
        for v in emulators.profiles():
            with installation(v) as (root, selected):
                before = emulator.emulator_identity(root / 'EmuHawk.exe')
                (root / 'emulator-identity.json').write_text(json.dumps(before))
                (root / 'dll/unrelated.wbx.zst').unlink()
                (root / 'dll/OpenAL32.dll').unlink()
                (root / 'dll/other.dll').write_bytes(b'extra')
                after = emulator.emulator_identity(root / 'EmuHawk.exe')
                self.assertEqual(before, after)
                self.assertEqual(after['files'], selected['files'])
                emulator.require_session_emulator(root, after)

    def test_every_missing_and_modified_required_component_rejects(self):
        for v in emulators.profiles():
            with installation(v) as (root, selected):
                for name in selected['validation_files']:
                    path = root / name
                    original = path.read_bytes()
                    path.write_bytes(b'modified')
                    with self.assertRaises(emulators.EmulatorCompatibilityError):
                        emulators.identify(root / 'EmuHawk.exe')
                    path.unlink()
                    with self.assertRaises(emulators.EmulatorCompatibilityError):
                        emulators.identify(root / 'EmuHawk.exe')
                    path.write_bytes(original)

    def test_all_critical_differences_are_reported(self):
        with installation('2.10') as (root, selected):
            for n in selected['validation_files'][1:]:
                (root / n).unlink()
            with self.assertRaises(emulators.EmulatorCompatibilityError) as caught:
                emulators.identify(root / 'EmuHawk.exe')
            for n in selected['validation_files'][1:]:
                self.assertIn(n, str(caught.exception))
            self.assertIn('Missing critical files (5)', str(caught.exception))

    def test_shadowing_paths_reject_but_identical_dependency_copy_accepts(self):
        for v in emulators.profiles():
            with installation(v) as (root, _):
                for n in ('NLua.dll', 'NLua/NLua.dll', 'NLua.exe', 'NLua/NLua.exe'):
                    path = root / n
                    path.parent.mkdir(exist_ok=True)
                    path.write_bytes(b'shadow')
                    with self.assertRaisesRegex(emulators.EmulatorCompatibilityError, 'Conflicting dependency copies'):
                        emulators.identify(root / 'EmuHawk.exe')
                    path.write_bytes((root / 'dll/NLua.dll').read_bytes())
                    emulators.identify(root / 'EmuHawk.exe')
                    path.unlink()

    def test_loader_policy_formatting_is_not_a_mismatch(self):
        with installation('2.10') as (root, _):
            p = root / 'EmuHawk.exe.config'
            p.write_text(p.read_text().replace('><', '>\n  <!-- comment -->\n<'))
            emulators.identify(root / 'EmuHawk.exe')

    def test_unrelated_native_similar_names_are_not_shadowing(self):
        with installation('2.10') as (root, _):
            (root / 'lua54.exe').write_bytes(b'unrelated executable')
            (root / 'lua54').mkdir()
            (root / 'lua54/lua54.dll').write_bytes(b'not a Win32 probe location')
            emulators.identify(root / 'EmuHawk.exe')

    def test_unrelated_app_and_gc_settings_are_not_binding_policy(self):
        with installation('2.10') as (root, _):
            p = root / 'EmuHawk.exe.config'
            p.write_text(p.read_text().replace('<runtime>', '<appSettings><add key="unrelated" value="1" /></appSettings><runtime><gcServer enabled="true" />'))
            emulators.identify(root / 'EmuHawk.exe')

    def test_redirects_probing_and_external_config_reject(self):
        for xml in ('<configuration><runtime><probing privatePath="plugins" /></runtime></configuration>',
                    '<configuration><runtime configSource="other.config" /></configuration>',
                    '<configuration><runtime><appDomainManagerAssembly value="foreign" /></runtime></configuration>',
                    '<configuration><runtime><assemblyBinding><codeBase href="elsewhere.dll" /></assemblyBinding></runtime></configuration>',
                    '<broken'):
            with installation('2.10') as (root, _):
                (root / 'EmuHawk.exe.config').write_text(xml)
                with self.assertRaises(emulators.EmulatorCompatibilityError):
                    emulators.identify(root / 'EmuHawk.exe')

    def test_renamed_executable_uses_its_own_loader_config(self):
        with installation('2.10') as (root, _):
            exe = root / 'Renamed.exe'
            exe.write_bytes((root / 'EmuHawk.exe').read_bytes())
            with self.assertRaisesRegex(emulators.EmulatorCompatibilityError, 'loader configuration'):
                emulators.identify(exe)
            Path(str(exe) + '.config').write_bytes((root / 'EmuHawk.exe.config').read_bytes())
            emulators.identify(exe)

    def test_openal_dependencies_are_only_required_when_selected(self):
        with installation('2.10') as (root, _):
            p = root / 'dll/OpenAL32.dll'
            emulators.verify_frontend(root / 'EmuHawk.exe', {'SoundOutputMethod': 2})
            p.unlink()
            emulators.verify_frontend(root / 'EmuHawk.exe', {'SoundOutputMethod': 1})
            with self.assertRaisesRegex(emulators.EmulatorCompatibilityError, 'OpenAL'):
                emulators.verify_frontend(root / 'EmuHawk.exe', {'SoundOutputMethod': 2})

    def test_unreadable_selected_frontend_has_actionable_error(self):
        with installation('2.10') as (root, _):
            original = emulators.sha
            def read(path):
                if Path(path).name == 'OpenAL32.dll':
                    raise PermissionError('OpenAL file locked')
                return original(path)
            with patch.object(emulators, 'sha', side_effect=read):
                with self.assertRaisesRegex(emulators.EmulatorCompatibilityError, 'Cannot read.*OpenAL'):
                    emulators.verify_frontend(root / 'EmuHawk.exe', {'SoundOutputMethod': 2})

    def test_profile_dependency_sets_exclude_unrelated_cores(self):
        for p in emulators.profiles().values():
            self.assertLess(len(p['validation_files']), len(p['files']) / 2)
            self.assertFalse(set(p['validation_files']) - p['files'].keys())
            self.assertIn('dll/BizHawk.Emulation.Cores.dll', p['validation_files'])
            self.assertIn('dll/lua54.dll', p['validation_files'])
            self.assertNotIn('dll/Virtu.dll', p['validation_files'])
            self.assertFalse(any(n.endswith('.wbx.zst') for n in p['validation_files']))
            self.assertNotIn('optional_files', p)


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
                    with self.assertRaisesRegex(ValueError, 'critical runtime integrity'):
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

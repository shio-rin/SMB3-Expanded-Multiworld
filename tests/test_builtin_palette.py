# SPDX-License-Identifier: MPL-2.0
"""Built-in emulator colors are a local runtime dependency, not packaged data."""
import unittest
from smb3x.launcher import preferences as p


class BuiltinPaletteTests(unittest.TestCase):
    def test_default_is_emulator_owned(self):
        for version in ('2.10', '2.11', '2.11.1'):
            config = p.configuration(version)
            self.assertIsNone(config['CoreSettings'][p.NES_CORE]['Palette'])
            values = p.preference_values(config, version)
            self.assertIsNone(values['CoreSettings'][p.NES_CORE]['Palette'])
            p.validate_configuration(p.apply_preferences(config, values), version)

    def test_explicit_local_palette_roundtrips(self):
        config = p.configuration('2.11.1')
        local = [[i, 255-i, i*2] for i in range(64)]
        config['CoreSettings'][p.NES_CORE]['Palette'] = local
        values = p.preference_values(config, '2.11.1')
        result = p.apply_preferences(p.configuration('2.11.1'), values)
        self.assertEqual(result['CoreSettings'][p.NES_CORE]['Palette'], local)
        p.validate_configuration(result, '2.11.1')

    def test_invalid_palette_rejects(self):
        for bad in (False, {}, [], [[256, 0, 0]] * 64, [[1, 2]] * 64):
            config = p.configuration()
            config['CoreSettings'][p.NES_CORE]['Palette'] = bad
            with self.assertRaisesRegex(ValueError, 'Palette'):
                p.preference_values(config)

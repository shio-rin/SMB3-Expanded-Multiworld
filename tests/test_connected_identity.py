# SPDX-License-Identifier: MPL-2.0
"""Current connection validation without importing the external AP client framework.

Compile the actual validator, not a copied implementation. Planners and contract
validators remain real; only the surrounding AP context is a synthetic object.
"""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from smb3x.shared import location_signals, effects, progression
from smb3x.shared.identity import Identity
from smb3x.shared.items import ITEM_REGISTRY_SHA256
from smb3x.planning import audiovisual, cosmetics, hazards, music, stages

GAME = 'Super Mario Bros. 3: Expanded Multiworld'
ROM_SHA1 = 'BB894D104C796F69BA16587EB66C0275F5C2FC02'


def validator():
    path = Path(__file__).resolve().parents[1] / 'src/smb3x/client/network.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'validate_connected_identity')
    namespace = dict(__package__='smb3x.client', GAME=GAME, ROM_SHA1=ROM_SHA1,
                     location_signals=location_signals, Identity=Identity,
                     ITEM_REGISTRY_SHA256=ITEM_REGISTRY_SHA256,
                     REGISTRY_SHA256=location_signals.REGISTRY_SHA256)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[function.name]


class ConnectedIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validate = staticmethod(validator())
        seed = 'synthetic-identity-characterization'
        shuffle = stages.assignments(seed, 'vanilla')
        cosmetic = cosmetics.assignments(seed)
        config = progression.validate(dict(inventory_mode='stacked', hammer_mode='regional'))
        ids = [int(r['id'], 16) for r in location_signals.profile_rows('m242', config)]
        cls.slot = dict(
            game=GAME, namespace='smb3x', identity_contract='smb3x-fresh-1',
            bridge_protocol=35, rom_payload_sha1=ROM_SHA1,
            location_registry_sha256=location_signals.REGISTRY_SHA256,
            item_registry_sha256=ITEM_REGISTRY_SHA256, location_profile='m242',
            progression=config, location_ids=ids, enabled_location_ids=ids,
            location_contract='m242-victory-only-1', cosmetics=cosmetic,
            level_shuffle=shuffle, audiovisual=audiovisual.plan(seed, shuffle, cosmetics=cosmetic)[0],
            release='m27-1', hazards=hazards.plan(seed, shuffle, 'off', 'off'),
            foundation_contract='m25-foundation-ui-audio-1',
            sfx_restoration_contract='m244-sfx-resume-1',
            interface_contract='m245-compact-travel-desk-1', trap_warning='show',
            presentation_contract='m251-presentation-1', effects=effects.settings('off', False, False),
            goal='standard', r3_music=music.plan(seed, shuffle, cosmetic, 'vanilla'),
            ending_receipt_version=1, m242_palettes={'synthetic': 'prepared palette'},
        )
        cls.seed = seed

    def setUp(self):
        self.data = deepcopy(self.slot)
        self.ctx = SimpleNamespace(
            server_seed_name=self.seed, expected_seed=self.seed, slot=1, team=0,
            slot_info={1: SimpleNamespace(name='Synthetic', game=GAME)},
            requested_slot='Synthetic', notifications=SimpleNamespace(trap_warning=None),
        )

    def test_current_identity_and_notification_update(self):
        self.assertEqual(self.validate(self.ctx, self.data), Identity(self.seed, 0, 1))
        self.assertEqual(self.ctx.notifications.trap_warning, 'show')

    def test_old_release_rejects_before_hazard_planning_or_notification_mutation(self):
        for release in ('m241-1', 'm244-1', 'm25-foundation-1', 'm251-1', 'm26-1', None):
            with self.subTest(release=release), patch.object(hazards, 'plan') as plan:
                self.data['release'] = release
                with self.assertRaisesRegex(ValueError, 'matching cached runtime'):
                    self.validate(self.ctx, self.data)
                plan.assert_not_called()
                self.assertIsNone(self.ctx.notifications.trap_warning)

    def test_current_release_still_requires_each_later_contract(self):
        for key, message in (
            ('foundation_contract', 'Foundation audio'),
            ('sfx_restoration_contract', 'Foundation audio'),
            ('interface_contract', 'interface contract'),
            ('presentation_contract', 'presentation contract'),
            ('trap_warning', 'presentation contract'),
            ('ending_receipt_version', 'ending receipt'),
        ):
            with self.subTest(key=key):
                data = dict(self.data, **{key: None})
                with self.assertRaisesRegex(ValueError, message):
                    self.validate(self.ctx, data)

    def test_prepared_palette_owner_and_missing_owner_reject(self):
        self.ctx.expected_palette_selection = self.data['m242_palettes']
        for release in (None, 'm241-1', 'm26-1'):
            if release is not None:
                self.ctx.expected_release = release
            with self.subTest(release=release), self.assertRaisesRegex(ValueError, 'palette/release'):
                self.validate(self.ctx, self.data)
        self.ctx.expected_release = 'm27-1'
        self.validate(self.ctx, self.data)
        self.ctx.expected_palette_selection = {}
        with self.assertRaisesRegex(ValueError, 'palette/release'):
            self.validate(self.ctx, self.data)

    def test_invalid_protocol_short_circuits_location_profile_reader(self):
        self.data['bridge_protocol'] = 34
        with patch.object(location_signals, 'profile_rows') as rows:
            with self.assertRaisesRegex(ValueError, 'protocol/ROM/location'):
                self.validate(self.ctx, self.data)
            rows.assert_not_called()


if __name__ == '__main__':
    unittest.main()

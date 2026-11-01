# SPDX-License-Identifier: MPL-2.0
"""Final slot data and hash-bound Archipelago player container."""

from pathlib import Path
from hashlib import sha256
import hashlib, json
from worlds.Files import APPlayerContainer
from ..shared.resources import DATA
from ..shared import locations
from ..shared.effects import settings as effect_settings
from .settings import settings
from .types import GAME
from ..planning.stages import assignments
from ..planning.audiovisual import plan
from ..planning.cosmetics import DEFAULTS
from ..native.music.score.pack import load_pack
from ..planning.hazards import plan as hazards
from ..planning.palettes import plan as palette_plan
from ..planning.special_palettes import plan as special_palette_plan
from ..planning.music import plan as music_plan

ROM_PAYLOAD_SHA1 = 'BB894D104C796F69BA16587EB66C0275F5C2FC02'
RESOURCE_ID = None
RESOURCE_ROOT = None
PATCH_VERSION = 'm26-native-2'
PERSISTENCE = 3


class SMB3PlayerFile(APPlayerContainer):
    game = GAME
    patch_file_ending = '.apsmb3x'

    def __init__(self, *args, record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record

    def write_contents(self, z):
        super().write_contents(z)
        z.writestr('session.json', json.dumps(self.record, sort_keys=True, separators=(',', ':')))

    def get_manifest(self):
        value = super().get_manifest()
        value.update(
            smb3x_container=1, resource_id=RESOURCE_ID, patch=PATCH_VERSION, persistence=PERSISTENCE
        )
        value['session_sha256'] = hashlib.sha256(
            json.dumps(self.record, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest()
        return value


def av_settings(world):
    o = world.options
    result = {
        k: getattr(o, k).current_key
        for k in (
            'music_policy',
            'secondary_music',
            'level_palette_style',
            'overworld_palette_style',
        )
    }
    result.update(
        {k: getattr(o, k).value for k in ('original_music_percent', 'custom_track_budget')}
    )
    result.update(
        music_families=sorted(o.music_families.value), themes=sorted(o.palette_themes.value)
    )
    return result


def shuffle_plan(world):
    o = world.options
    return assignments(
        world.multiworld.seed_name,
        o.level_shuffle.current_key,
        o.classic_level_packs.current_key,
        o.classic_stage_count.value,
        o.special_stage_shuffle.current_key,
    )


def slot_data(world):
    """Produce deterministic plans and stable contracts shared by server and preparation."""
    from ..planning.cosmetics import assignments as cosmetic_assignments

    if not hasattr(world, '_resolved_music_pack'):
        path = world.options.music_pack.value
        world._resolved_music_pack = (
            load_pack(path, development=bool(world.options.development_music.value))
            if path
            else None
        )
    shuffle = shuffle_plan(world)
    cosmetic = dict(
        cosmetic_assignments(
            world.multiworld.seed_name, {k: getattr(world.options, k).current_key for k in DEFAULTS}
        )['settings']
    )
    for kind in ('level', 'overworld'):
        if getattr(world.options, kind + '_palette_style').current_key == 'constrained':
            cosmetic[kind + '_palette_shuffle'] = 'constrained'
    cosmetics = cosmetic_assignments(world.multiworld.seed_name, cosmetic)
    av, _ = plan(
        world.multiworld.seed_name,
        shuffle,
        world._resolved_music_pack,
        av_settings(world),
        cosmetics,
    )
    data = dict(
        bridge_protocol=35,
        rom_payload_sha1=ROM_PAYLOAD_SHA1,
        location_registry_sha256=locations.HASH,
        item_registry_sha256=sha256((DATA / 'items_m25.json').read_bytes()).hexdigest(),
        location_profile='m242',
        location_ids=[int(r['id'], 16) for r in world.locations],
        goal=world.options.goal.current_key,
        ending_receipt_version=1,
        progression=settings(world),
        cosmetics=cosmetics,
        level_shuffle=shuffle,
        audiovisual=av,
        hazards=hazards(
            world.multiworld.seed_name,
            shuffle,
            world.options.poison_mushrooms.current_key,
            world.options.angry_sun.current_key,
        ),
    )
    data.update(
        release='m27-1',
        game=GAME,
        namespace='smb3x',
        identity_contract='smb3x-fresh-1',
        location_contract=locations.VERSION,
        enabled_location_ids=locations.IDS,
        music_shuffle=world.options.music_shuffle.current_key,
        m242_palettes=palette_plan(
            world.multiworld.seed_name, world.options.palette_mode.current_key
        ),
        world_pass_placement=world.options.world_pass_placement.current_key,
        placement_policy=getattr(world, 'placement_report', None),
        special_palette_selection=special_palette_plan(
            world.multiworld.seed_name, world.options.palette_mode.current_key
        ),
        interface_contract='m245-compact-travel-desk-1',
        foundation_contract='m25-foundation-ui-audio-1',
        sfx_restoration_contract='m244-sfx-resume-1',
        trap_warning=world.options.trap_warning.current_key,
        presentation_contract='m251-presentation-1',
        effects=effect_settings(
            world.options.trap_frequency.current_key,
            bool(world.options.blessings.value),
            bool(world.options.death_link.value),
        ),
    )
    data['r3_music'] = music_plan(
        world.multiworld.seed_name,
        shuffle,
        cosmetics,
        world.options.music_shuffle.current_key,
        bool(world.options.music_reserves.value),
        sorted(world.options.music_tracks.value),
    )
    return data


def generate_output(world, directory):
    record = dict(
        format='smb3x-player-1',
        seed_name=world.multiworld.seed_name,
        team=0,
        slot=world.player,
        slot_name=world.multiworld.player_name[world.player],
        slot_data=world.fill_slot_data(),
        resource_id=RESOURCE_ID,
    )
    target = Path(directory) / (world.multiworld.get_out_file_name_base(world.player) + '.apsmb3x')
    SMB3PlayerFile(
        str(target), player=world.player, player_name=record['slot_name'], record=record
    ).write()

# SPDX-License-Identifier: MPL-2.0
from ..planning import music as music_plan
'Combined production build over the sealed 72-source Poison implementation.'
from pathlib import Path
from .patches.special_palettes import install as palettes, P, BOSS
from .bps import make_bps, apply_bps
from .rom import digest
from ..shared.resources import RESOURCE_ROOT as ROOT
PATCH_VERSION = 'm244-native-1'

def audio_palette_stage(source, identity, original, base, *args, palette_mode='atmospheric', music_mode='vanilla', music_reserves=False, music_tracks=(), private_pack=None, music_payloads=None, **kwargs):
    selection = P['plan'](identity.seed, palette_mode)
    rom = bytearray(original)
    extension = None if palette_mode == 'original' else palettes(rom, base, selection)
    from .music.install import install as music
    music_selection = music_plan.plan(identity.seed, base['level_shuffle'], base['cosmetics'], music_mode, music_reserves, music_tracks)
    music_extension = music(rom, source, base, music_selection, private_pack, music_payloads)
    from .patches.camera_sun import install as sun
    hazards, sun_extension, poison_extension = sun(rom, source, base, identity.seed, kwargs.get('poison_mushrooms', 'off'), kwargs.get('angry_sun', 'off'))
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, special_palette_selection=selection, special_palette_extension=extension, koopaling_palette_revision=BOSS['VERSION'], r3_music=music_selection, r3_extension=music_extension, hazards=hazards, camera_sun=sun_extension, m243_hazard_extension=poison_extension)
    rom = bytes(rom)
    return (rom, config)

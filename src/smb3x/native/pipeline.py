# SPDX-License-Identifier: MPL-2.0
"""Current native construction, in the exact certified patch order.

Each stage owns one responsibility. Stages receive preceding bytes and metadata;
none loads or mutates a historical builder. Only the final output receives a BPS.
"""

from .core import build as build_core
from .audio_stage import expand_audio
from .contexts import contexts
from .spade import spade
from .palette_stage import palette_stage
from .expanded_hazards import expanded_hazards
from .audio_palette_stage import audio_palette_stage
from .interface import interface
from .restoration import restoration
from .effects_stage import effects_stage
from .bps import make_bps, apply_bps
from .rom import digest, verify_base

PATCH_VERSION = 'm26-native-2'


def build(
    source,
    identity,
    goal='standard',
    progression=None,
    *,
    cosmetics=None,
    level_shuffle='vanilla',
    audiovisual=None,
    pack=None,
    poison_mushrooms='off',
    angry_sun='off',
    special_stage_shuffle='off',
    palette_mode='original',
    world_pass_placement='unrestricted',
    placement_policy=None,
    music_mode='vanilla',
    music_reserves=False,
    music_tracks=(),
    private_pack=None,
    music_payloads=None,
    effects=None,
    trap_warning='show'
):
    verify_base(source)
    settings = dict(
        goal=goal,
        progression=progression,
        cosmetics=cosmetics,
        level_shuffle=level_shuffle,
        audiovisual=audiovisual,
        pack=pack,
        poison_mushrooms=poison_mushrooms,
        angry_sun=angry_sun,
        special_stage_shuffle=special_stage_shuffle,
    )
    if (progression or {}).get('inventory_mode', 'stacked') != 'stacked':
        raise ValueError('New games require Stacked inventory')
    progression = dict(progression or {}, inventory_mode='stacked')
    settings['progression'] = progression
    if pack is not None or (audiovisual or {}).get('music_policy', 'vanilla') != 'vanilla':
        raise ValueError('Public builds support original SMB3 music only')
    rom, base = build_core(source, identity, goal, progression, cosmetics=cosmetics)
    rom, base = expand_audio(
        source, identity, rom, base, (), goal=goal, progression=progression, cosmetics=cosmetics
    )
    rom, base = contexts(source, identity, rom, base, **dict(settings, poison_mushrooms='off'))
    rom, base = spade(source, identity, rom, base)
    rom, base = palette_stage(
        source,
        identity,
        rom,
        base,
        palette_mode=palette_mode,
        world_pass_placement=world_pass_placement,
        placement_policy=placement_policy,
        **dict(settings, poison_mushrooms='off')
    )
    rom, base = expanded_hazards(source, identity, rom, base, **settings)
    rom, base = audio_palette_stage(
        source,
        identity,
        rom,
        base,
        palette_mode=palette_mode,
        music_mode=music_mode,
        music_reserves=music_reserves,
        music_tracks=music_tracks,
        private_pack=private_pack,
        music_payloads=music_payloads,
        **settings
    )
    rom, base = interface(source, identity, rom, base)
    rom, base = restoration(source, identity, rom, base)
    rom, base = effects_stage(
        source, identity, rom, base, effects=effects, trap_warning=trap_warning
    )
    config = {
        k: v
        for k, v in base.items()
        if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')
    }
    patch = make_bps(source, rom, config)
    if apply_bps(source, patch) != rom:
        raise ValueError('Final BPS reproduction mismatch')
    return (
        rom,
        patch,
        dict(
            config,
            source=digest(source),
            output=digest(rom),
            bps=digest(patch),
            prg_sha256=digest(rom[16:524304])['sha256'],
            chr_sha256=digest(rom[524304:])['sha256'],
        ),
    )

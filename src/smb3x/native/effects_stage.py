# SPDX-License-Identifier: MPL-2.0
"""preserves the complete UI/R3/audio foundation and adds native death dispatch."""
from .patches.death_dispatch import install
from .bps import make_bps, apply_bps
from .rom import digest
from ..shared import effects as effect_settings
PATCH_VERSION = 'm26-native-2'

def effects_stage(source, identity, original, base, *args, effects=None, trap_warning='show', **kwargs):
    if trap_warning not in ('show', 'hide'):
        raise ValueError('Invalid trap warning presentation')
    effects = effect_settings.validate_settings(effects or effect_settings.settings())
    rom, dispatcher = install(original)
    from .patches.giant_blocks import install as correct_giant
    rom, giant_correction = correct_giant(rom)
    from hashlib import sha256
    if sha256(rom[16 + 24 * 8192 + 522:16 + 24 * 8192 + 609]).hexdigest() != 'a01be1ec4863b531f148a310d88f67bca80dcf33d5a7175ac9125041f7034ad9':
        raise ValueError('castle text source ownership mismatch')
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, effects=effects, trap_warning=trap_warning, presentation_contract='m251-presentation-1', death_dispatch=dispatcher, giant_correction=giant_correction)
    return (rom, config)

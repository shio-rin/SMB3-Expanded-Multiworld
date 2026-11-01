# SPDX-License-Identifier: MPL-2.0
"""Accepted interface plus the exact restoration-only SFX helper."""
from .music.restoration import install, CONTRACT
from .bps import make_bps, apply_bps
from .rom import digest
PATCH_VERSION = 'm25-foundation-native-1'
FOUNDATION_CONTRACT = 'm25-foundation-ui-audio-1'

def restoration(source, identity, original, base, *args, **kwargs):
    rom = bytearray(original)
    restoration = install(rom, source, base)
    rom = bytes(rom)
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, foundation_contract=FOUNDATION_CONTRACT, sfx_restoration_contract=CONTRACT, sfx_restoration=restoration)
    return (rom, config)

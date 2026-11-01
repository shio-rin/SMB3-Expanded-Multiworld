# SPDX-License-Identifier: MPL-2.0
"""native static-Spade correction over the immutable accepted builder."""
from pathlib import Path
from .patches.spade import install
from .rom import digest
from .bps import make_bps, apply_bps
from ..shared.resources import RESOURCE_ROOT as ROOT
PATCH_VERSION = 'm232-native-1'

def spade(source, identity, original, base, *args, **kwargs):
    rom = bytearray(original)
    fix = install(rom, source)
    rom = bytes(rom)
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, m232_spade=fix, m232_sources={__file__.replace('\\', '/').rsplit('/', 1)[-1]: digest(Path(__file__).read_bytes())['sha256']})
    return (rom, config)

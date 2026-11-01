# SPDX-License-Identifier: MPL-2.0
"""Install the current native progression display after palette and audio patches."""
from .bps import make_bps, apply_bps
from .rom import digest
from .patches.interface import install
PATCH_VERSION = 'm245-native-2'
INTERFACE_CONTRACT = 'm245-compact-travel-desk-1'

def interface(source, identity, original, base, *args, engineering_only=False, **kwargs):
    rom = bytearray(original)
    ui = install(rom, source, base)
    rom = bytes(rom)
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, m245_ui=ui, interface_contract=INTERFACE_CONTRACT)
    if engineering_only:
        config['engineering_only'] = True
    return (rom, config)

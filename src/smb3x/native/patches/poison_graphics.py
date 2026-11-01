# SPDX-License-Identifier: MPL-2.0
"""Exact native mushroom art reuse; no private art or shared palette mutation."""
import hashlib

def expand(rom, source):
    if len(rom) not in (655376, 786448) or rom[5] not in (16, 32):
        raise ValueError('Expected supported CHR')
    start = 16 + 524288
    native = source[16 + 262144 + 4096:16 + 262144 + 5120]
    if rom[start + 4096:start + 5120] != native:
        raise ValueError('Native common sprite source guard')
    if len(rom) == 655376:
        rom.extend(bytes(131072))
        rom[5] = 32
    if any(rom[start + 128 * 1024:start + 129 * 1024]):
        raise ValueError('Retired Poison page ownership')
    return {'version': 'm221-native-mushroom-recolor-1', 'chr_kib': 256, 'poison_page': 4, 'poison_pattern': 81, 'native_graphics_reused': True, 'duplicated_tiles': 0, 'retired_private_page': 128, 'native_tile_sha256': hashlib.sha256(native[256:288]).hexdigest(), 'art': 'exact native Super Mushroom; original mirrored drawing, positions and flips', 'palette': 3, 'color': 'native amber/orange cap ($27), pink/cream details ($36)', 'palette_writes': 0, 'limitation': 'Purple is not isolated; all four native sprite palettes have shared owners. Existing palette3 is distinct from normal palette1 red/white without recoloring other sprites.'}

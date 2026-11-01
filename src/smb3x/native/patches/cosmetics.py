# SPDX-License-Identifier: MPL-2.0
"""Source-guarded cosmetic ROM edits. No queue writes or sound driver replacement."""
from pathlib import Path
from ..rom import Edit, prg_offset, digest
from ...planning.cosmetics import assignments, HEADERS

def edits(source, seed, settings=None):
    plan = assignments(seed, settings)
    result = []

    def patch(bank, address, old, new, name, origin=40960):
        result.append(Edit(prg_offset(bank, address, origin), bytes(old), bytes(new), name))
    for h in HEADERS:
        key = h['key']
        off = h['offset']
        if key in plan['level_music'] or key in plan['level_palettes']:
            if digest(source[off:off + 9])['sha256'] != h['header_sha256']:
                raise ValueError('Cosmetic header source mismatch: ' + key)
        if key in plan['level_music']:
            result.append(Edit(off + 8, bytes([h['music_byte']]), bytes([h['music_byte'] & 240 | plan['level_music'][key]]), 'Level music ' + key))
        if key in plan['level_palettes']:
            result.append(Edit(off + 5, bytes([h['palette_byte']]), bytes([h['palette_byte'] & 248 | plan['level_palettes'][key]]), 'Level palette ' + key))
    if plan['overworld_music']:
        values = [plan['overworld_music'][str(w)] for w in range(1, 9)]
        for bank, address, origin in [(30, 33812, 32768), (10, 50106, 49152)]:
            patch(bank, address, range(1, 9), values, 'Paired overworld music table', origin)
    if plan['overworld_palettes']:
        patch(12, 42013, [0, 1, 0, 3], [plan['overworld_palettes'][str(w)] for w in range(1, 5)], 'W1-4 constrained map backgrounds')
    if plan['settings']['player_appearance'] == 'luigi':
        patch(8, 42282, [22], [42], 'Luigi ordinary in-level player palette')
        patch(27, 47120, [22], [26], 'Luigi initial map palette')
        patch(10, 52673, [22], [26], 'Luigi Cloud restoration palette', 49152)
        for i in (0, 1, 3, 8):
            patch(26, 42351 + 4 * i, [22], [26], 'Luigi inventory powerup palette ' + str(i))
        old = bytes.fromhex('0f1630360f163021')
        new = bytes.fromhex('0f1a30360f1a3031')
        patch(27, 47096, old, new, 'Luigi bonus-intro player palette')
        patch(30, 34416, bytes.fromhex('ad2607'), bytes.fromhex('a901ea'), 'Luigi world-intro label only', 32768)
        patch(24, 47311, bytes.fromhex('ad2607'), bytes.fromhex('a901ea'), 'Luigi Peach-scene presentation only')
        patch(24, 47330, bytes.fromhex('c5c3'), bytes.fromhex('c4c3'), 'Peach-scene recolor compares OAM index, not color')
    return (result, plan)

# SPDX-License-Identifier: MPL-2.0
"""Single native start action; private title CHR, guarded PRG1 input routing."""
import hashlib
import json
from pathlib import Path
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source):
    verify_base(source)
    rom = bytearray(target)
    if len(rom) != 786448 or rom[4:6] != bytes([32, 32]):
        raise ValueError('title requires accepted expanded architecture')
    s = json.loads((ROOT / 'native/symbols/m22_symbols.json').read_text())
    edits = []

    def patch(bank, address, before, after):
        if len(before) != len(after):
            raise ValueError('Title patch length')
        for b in [bank, bank + 32] if bank in (30, 31) else [bank]:
            offset = 16 + b * 8192 + (address & 8191)
            if rom[offset:offset + len(before)] != before:
                raise ValueError(f'Title source guard {b}:{address:04x}')
            rom[offset:offset + len(after)] = after
        edits.append(dict(bank=bank, address=address, before=before.hex(), after=after.hex()))

    def original(bank, address, size):
        off = 16 + bank * 8192 + (address & 8191)
        return source[off:off + size]
    start, end = (s['PRG024_AC52'] + 3, s['PRG024_AC6B'])
    replacement = bytes.fromhex('a9008d2b078d2607')
    patch(24, start, original(24, start, end - start), replacement + b'\xea' * (end - start - len(replacement)))
    debug = s['Title_DebugMenu']
    patch(24, debug, original(24, debug, 3), b'L' + s['Title_Do1P2PMenu'].to_bytes(2, 'little'))
    helper = bytes.fromhex('a9008d2607a9018d2b0760')
    patch(24, debug + 3, original(24, debug + 3, len(helper)), helper)
    prep = s['Title_PrepForWorldMap']
    window = original(24, prep, 16)
    inc = window.find(bytes.fromhex('ee2b07'))
    if inc < 0:
        raise ValueError('Native player-count initialization changed')
    patch(24, prep + inc, bytes.fromhex('ee2b07'), b' ' + (debug + 3).to_bytes(2, 'little'))
    chr_start = 16 + 524288
    page = bytearray(source[16 + 262144 + 120 * 1024:16 + 262144 + 124 * 1024])
    glyphs = {'S': [0, 62, 96, 60, 6, 6, 124, 0], 'T': [0, 126, 24, 24, 24, 24, 24, 0], 'C': [0, 60, 102, 96, 96, 102, 60, 0], 'H': [0, 102, 102, 126, 102, 102, 102, 0], 'I': [0, 126, 24, 24, 24, 24, 126, 0], 'O': [0, 60, 102, 102, 102, 102, 60, 0]}
    font = dict(zip('PLAREGM ', [10, 11, 12, 13, 27, 28, 29, 92]))
    slots = [18, 79, 94, 124, 248, 30]
    for tile, (letter, rows) in zip(slots, glyphs.items()):
        font[letter] = tile
        outline = []
        for y, row in enumerate(rows):
            halo = 0
            for neighbor in rows[max(0, y - 1):min(8, y + 2)]:
                halo |= neighbor | neighbor << 1 | neighbor >> 1
            outline.append(halo & ~row & 255)
        page[tile * 16:(tile + 1) * 16] = bytes(outline) + bytes(rows)
    destination = chr_start + 132 * 1024
    if any(rom[destination:destination + 4096]):
        raise ValueError('Private title CHR already owned')
    rom[destination:destination + 4096] = page
    address = s['PRG030_845A'] + 9
    patch(30, address, bytes.fromhex('a978'), bytes.fromhex('a984'))
    patch(30, address + 5, bytes.fromhex('a97a'), bytes.fromhex('a986'))
    text_address = s['Title_LoadMenu']
    before = original(25, text_address, 32)
    if before[:3] != bytes.fromhex('226a0d') or before[16:19] != bytes.fromhex('22aa0d'):
        raise ValueError('Title text record layout changed')
    after = before[:3] + bytes((font[c] for c in '    START    ')) + before[16:19] + bytes((font[c] for c in ' ARCHIPELAGO '))
    patch(25, text_address, before, after)
    if rom[chr_start:chr_start + 131072] != target[chr_start:chr_start + 131072]:
        raise ValueError('Title modified original CHR')
    target[:] = rom
    return dict(version='m22-title-1', label='START ARCHIPELAGO', lines=['START', 'ARCHIPELAGO'], player_count=1, appearance='seed YAML only', chr_pages=[132, 133, 134, 135], source_chr_pages=[120, 121, 122, 123], glyph_patterns=slots, private_chr_sha256=hashlib.sha256(page).hexdigest(), edits=edits)

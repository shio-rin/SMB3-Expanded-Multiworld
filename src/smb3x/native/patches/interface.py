# SPDX-License-Identifier: MPL-2.0
"""Guarded installer for the native progression display and travel controls."""
from pathlib import Path
import hashlib
from ...shared.resources import RESOURCE_ROOT as ROOT
GLYPHS = 'ABCDEFGHIKLMNOPRSTUVW Y0123456789/>-'
SLOTS = (78, 106, 107, 160, 161, 162, 163, 186, 188, 216, 217, 218, 219, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 251)
assert len(GLYPHS) == len(SLOTS) == 36

def tile(c):
    return SLOTS[GLYPHS.index(c)]

def install(rom, source, base):
    from ..interface_text import rows as menu_rows, values_data
    old = bytes(rom)
    symbols = base['assembly']['symbols']
    pre = '\n'.join((f'{k} = ${v:04X}' for k, v in dict(NativeMenuControl=symbols['MenuControl'], NativeMenuStatus=symbols['MenuStatus'], NativeMenuRender=symbols['MenuRender'], NativeBankCall=symbols['BankCall'], GlyphOwned=tile('Y'), GlyphX=tile('-'), GlyphBlank=tile(' '), GlyphW=tile('W'), GlyphArrow=tile('>'), GlyphSlash=tile('/')).items()))
    text = (ROOT / 'native/asm/m245_menu.asm').read_text().replace('; @NATIVE_CONSTANTS', pre).replace('; @UI_ROWS', menu_rows(tile))
    for name in ('controls', 'geometry', 'values'):
        text = text.replace('; @' + name.upper(), (ROOT / f'native/asm/m245_{name}.asm').read_text())
    text = text.replace('; @VALUES_DATA', values_data(tile, base, old))
    from ..interface_certificate import compile_ui
    data, sy, source_key = compile_ui(text)
    edits = []

    def write(bank, addr, chunk, name, before=None, origin=40960):
        offset = 16 + bank * 8192 + addr - origin
        if before is not None and rom[offset:offset + len(before)] != before:
            raise ValueError('Hook guard ' + name)
        rom[offset:offset + len(chunk)] = chunk
        edits.append(dict(bank=bank, address=addr, size=len(chunk), name=name))

    def emitted(bank, start, end):
        lo, hi = (sy[start], sy[end])
        off = 16 + bank * 8192 + lo - 40960
        return data[off:off + hi - lo]
    for start, end in (('UiControlHook', 'UiControlHookEnd'), ('UiStatusHook', 'UiStatusHookEnd'), ('UiHelpers', 'UiHelpersEnd')):
        write(26, sy[start], emitted(26, start, end), start)
    if not 40960 < sy['UiAllCodeEnd'] < 46368 or not 47616 < sy['UiRowsEnd'] <= 49152:
        raise ValueError('UI code/data allocation')
    write(53, 40960, emitted(53, 'UiControl', 'UiAllCodeEnd'), 'UI authored code', b'\xff' * (sy['UiAllCodeEnd'] - 40960))
    write(53, 47616, data[16 + 53 * 8192 + 6656:16 + 53 * 8192 + sy['UiRowsEnd'] - 40960], 'UI authored rows', b'\xff' * (sy['UiRowsEnd'] - 47616))
    write(53, 46368, emitted(53, 'UiEntry', 'UiEntryEnd'), 'UI entry and ROM identity', b'\xff' * (sy['UiEntryEnd'] - 46368))
    for b in (30, 62):
        addr = symbols['BankCall']
        off = 16 + b * 8192 + addr - 32768
        gate = old[off:16 + b * 8192 + symbols['FixedEnd'] - 32768]
        if gate[4:12] != bytes.fromhex('a91ae0079002a919'):
            raise ValueError('Bank gate selection guard')
        revised = gate[:9] + b'\x03' + bytes.fromhex('addf7a') + gate[12:]
        if len(revised) != len(gate) + 1:
            raise ValueError('Bank gate bound')
        write(b, addr, revised, 'Scoped UI bank gate', gate + b'\xff', 32768)
        for hook, target, opcode in ((34174, 'ReloadStub', 76), (33952, 'InitStub', 32), (37009, 'AirshipStub', 76)):
            before = bytes([opcode]) + symbols[target].to_bytes(2, 'little')
            write(b, hook, bytes([opcode]) + (symbols[target] + 1).to_bytes(2, 'little'), target + ' relocated', before, 32768)
    init = symbols['ColdTracker']
    off = 16 + 26 * 8192 + init - 40960
    sequence = bytes([162, 13, 32]) + symbols['BankCall'].to_bytes(2, 'little')
    index = old.index(sequence, off, off + 64)
    write(26, 40960 + index - (16 + 26 * 8192), b' ' + sy['UiColdInit'].to_bytes(2, 'little') + b'\xea\xea', 'Cold UI initialization', sequence)
    write(53, 46592, old[16 + 12 * 8192:16 + 12 * 8192 + 1024], 'Local source map metatile definitions', b'\xff' * 1024)
    totals_addr = symbols['ProgressionWorldTotals']
    totals_off = 16 + 25 * 8192 + totals_addr - 40960
    totals = old[totals_off:totals_off + 8]
    if sum(totals) != old[16 + 30 * 8192 + 7962]:
        raise ValueError('Active count registry binding')
    write(53, sy['UiTotals'], totals, 'Authoritative build world totals', bytes(8))
    chrbase = 524304
    srcbase = 262160
    layout = old[16 + 12 * 8192:16 + 12 * 8192 + 1024]
    if set(SLOTS) & set(layout):
        raise ValueError('Map font collides with metatile pattern')
    changed = []
    for sourcebank, newbank in ((20, 224), (112, 226), (114, 228), (116, 230), (22, 232)):
        chunk = bytearray(old[chrbase + sourcebank * 1024:chrbase + (sourcebank + 2) * 1024])
        for c, slot in zip(GLYPHS, SLOTS):
            if not (128 if sourcebank == 22 else 0) <= slot < (256 if sourcebank == 22 else 128):
                continue
            n = 176 + ord(c) - 65 if c.isalpha() else 240 + int(c) if c.isdigit() else None
            if n is not None:
                glyph = source[srcbase + 92 * 1024 + n * 16:srcbase + 92 * 1024 + (n + 1) * 16]
                masks = [~(glyph[y] | glyph[y + 8]) & 255 if c.isalpha() else ~glyph[y] & glyph[y + 8] & 255 for y in range(8)]
            else:
                masks = {' ': [0] * 8, '/': [1, 2, 4, 8, 16, 32, 64, 0], '>': [0, 64, 32, 16, 32, 64, 0, 0], '-': [0, 0, 0, 255, 0, 0, 0, 0]}[c]
            offset = (slot & 127) * 16
            chunk[offset:offset + 16] = bytes(([255] * 8 if c == '-' else [m ^ 255 for m in masks]) + masks)
        if sourcebank == 22:
            borders = {128: [0, 0, 0, 15, 8, 8, 8, 8], 129: [0, 0, 0, 248, 8, 8, 8, 8], 130: [8, 8, 8, 15, 0, 0, 0, 0], 131: [8, 8, 8, 248, 0, 0, 0, 0], 204: [8] * 8}
            for slot, mask in borders.items():
                off = (slot & 127) * 16
                chunk[off:off + 16] = bytes([255] * 8 + mask)
        off = chrbase + newbank * 1024
        if any(rom[off:off + 2048]):
            raise ValueError('CHR clone allocation occupied')
        rom[off:off + 2048] = chunk
        changed.append(dict(source=sourcebank, destination=newbank, size=2048))
    return dict(version='m245-compact-travel-desk-1', source_text_sha256=source_key, symbols=sy, edits=edits, chr_clones=changed, cache=dict(start=28672, end=29208, row_buffers=[29696, 29728], scope='volatile map only'), max_tile_writes=28, max_attribute_writes=8, max_command_bytes=34, ppu_reads=0, irq_changes=0, nmi_changes=0, chr_bytes=10240, prg_bank=53)

# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Guarded source-world lookup for expanded original content only.\n\nNo world latch, no new RAM, no global World_Num substitution. Reuse the accepted\nbank51 trampoline; allocate only guarded slack outside its bounded hazard tables.\n'
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source, rows):
    if len(target) != 786448 or target[4:6] != bytes([32, 32]):
        raise ValueError('Expected accepted PRG512/CHR256 architecture')
    rows = sorted(rows, key=lambda r: (r['world'], r['hi'], r['x'], r['y']))
    if len(rows) > 127 or len({tuple((r[k] for k in ('world', 'hi', 'x', 'y'))) for r in rows}) != len(rows):
        raise ValueError('Duplicate or oversized context table')
    for r in rows:
        if set(r) != set(('world', 'hi', 'x', 'y', 'source_world')) or not 0 <= r['world'] < 8 or (not 0 <= r['source_world'] < 8) or (not 0 <= r['hi'] < 4) or r['x'] % 16 or (not 0 <= r['x'] <= 240) or (r['y'] not in range(32, 176, 16)):
            raise ValueError('Invalid physical source-context row')
    symbols = json.loads((ROOT / 'native/symbols/m222_symbols.json').read_text(encoding='utf-8'))
    text = (ROOT / 'native/asm/m222_context.asm').read_text(encoding='utf-8')
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'context.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        run = assemble_file(tmp / 'context.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (tmp / 'context.fns').read_text(), re.M)}
        data = (tmp / 'context.nes').read_bytes()
    rom = bytearray(target)
    edits = []

    def patch(bank, address, before, after):
        if len(before) != len(after):
            raise ValueError('Context patch size')
        for b in [bank, bank + 32] if bank in (30, 31) else [bank]:
            off = 16 + b * 8192 + (address & 8191)
            if rom[off:off + len(before)] != before:
                raise ValueError(f'Context source guard {b}:{address:04x}')
            rom[off:off + len(after)] = after
            edits.append(dict(bank=b, address=address, size=len(after)))
    for bank, first, last, limit in [(26, 'M222SourceWorldY', 'M222SourceWorldYEnd', 49152), (5, 'M222PiranhaTimer', 'M222PiranhaTimerEnd', 49152), (51, 'M222Dispatch', 'M222ContextEnd', 55296)]:
        lo, hi = (labels[first], labels[last])
        if not lo < hi <= limit:
            raise ValueError(('Context code capacity', first, hex(lo), hex(hi), hex(limit)))
        output_bank = 20 if bank == 51 else bank
        off = 16 + output_bank * 8192 + (lo & 8191)
        patch(bank, lo, b'\xff' * (hi - lo), data[off:off + hi - lo])
    patch(51, 55039, b'\xff', bytes([len(rows)]))
    for page, k in enumerate(('world', 'hi', 'x', 'y', 'source_world'), 8):
        patch(51, 49280 + page * 256, b'\xff' * len(rows), bytes((r[k] for r in rows)))
    patch(51, 49152, bytes.fromhex('c007d0034c80c6'), b'L' + labels['M222Dispatch'].to_bytes(2, 'little') + b'\xea' * 4)
    opcode = b'\xac' + symbols['World_Num'].to_bytes(2, 'little')
    hooks = []
    for first, last in [('LevelJct_BigQuestionBlock', 'LevelJct_General'), ('LevelJct_GenericExit', 'LevelJct_SpecialToadHouse')]:
        start = symbols[first]
        end = symbols[last]
        b = 26
        sites = [a for a in range(start, end) if source[16 + b * 8192 + (a & 8191):16 + b * 8192 + (a & 8191) + 3] == opcode]
        if len(sites) != 1:
            raise ValueError(('Ambiguous world-context hook', first, sites))
        patch(b, sites[0], opcode, b' ' + labels['M222SourceWorldY'].to_bytes(2, 'little'))
        hooks.append(dict(bank=b, address=sites[0], source=first))
    for first, last in [('Piranha_Attack', 'Piranha_HideInPipe'), ('Piranha_HideInPipe', 'Piranha_SpitFire')]:
        start = symbols[first]
        end = symbols[last]
        b = 5
        sites = [a for a in range(start, end) if source[16 + b * 8192 + (a & 8191):16 + b * 8192 + (a & 8191) + 3] == opcode]
        if len(sites) != 1:
            raise ValueError(('Ambiguous Piranha hook', first, sites))
        address = sites[0] - 3
        off = 16 + b * 8192 + (address & 8191)
        before = source[off:off + 13]
        if before[:3] != b'\xbd' + symbols['Objects_Timer'].to_bytes(2, 'little') or before[6] != 208 or before[8:10] != b'\xc9(' or (before[10] != 240) or (before[12] != 152):
            raise ValueError('Piranha timer sequence source guard')
        patch(b, address, before, b' ' + labels['M222PiranhaTimer'].to_bytes(2, 'little') + b'\xea' * 10)
        hooks.append(dict(bank=b, address=address, source=first))
    if rom[16 + 30 * 8192:16 + 32 * 8192] != rom[16 + 62 * 8192:16 + 64 * 8192]:
        raise ValueError('Fixed mirror mismatch')
    target[:] = rom
    return dict(version='m222-source-context-1', rows=rows, hooks=hooks, symbols=labels, edits=edits, bank=51, dpcm_sha256=hashlib.sha256(rom[16 + 51 * 8192 + 6144:16 + 52 * 8192]).hexdigest(), new_ram_bytes=0)

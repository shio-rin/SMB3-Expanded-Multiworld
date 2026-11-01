# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Isolated mixed-completion proof foundation; admission remains separately gated.'
from pathlib import Path
import json
import re
import subprocess
import tempfile
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source, rows):
    verify_base(source)
    keys = ('world', 'hi', 'x', 'y', 'tileset', 'layout', 'objects', 'effect')
    rows = sorted(rows, key=lambda r: tuple((r[k] for k in keys[:4])))
    if len(rows) > 31 or len({tuple((r[k] for k in keys[:4])) for r in rows}) != len(rows):
        raise ValueError('Mixed card table identity/capacity')
    for r in rows:
        if set(r) != set(keys) or r['world'] not in range(8) or r['hi'] not in range(4) or (r['x'] not in range(0, 256, 16)) or (r['y'] not in range(32, 176, 16)) or (not 1 <= r['tileset'] <= 14) or (not 40960 <= r['layout'] < 49152) or (not 49152 <= r['objects'] < 57344) or (not 1 <= r['effect'] <= 4):
            raise ValueError('Unreviewed mixed card binding')
    symbols = json.loads((ROOT / 'native/symbols/m222_mixed_symbols.json').read_text())
    text = (ROOT / 'native/asm/m222_mixed.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'mixed.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        run = assemble_file(tmp / 'mixed.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (tmp / 'mixed.fns').read_text(), re.M)}
        data = (tmp / 'mixed.nes').read_bytes()
    rom = bytearray(target)
    edits = []

    def at(b, a):
        return 16 + b * 8192 + (a & 8191)

    def patch(b, a, before, after):
        o = at(b, a)
        if len(before) != len(after) or rom[o:o + len(before)] != before:
            raise ValueError(f'Mixed exact source guard {b}:{a:04X}')
        rom[o:o + len(after)] = after
        edits.append(dict(bank=b, address=a, size=len(after)))
    lo = labels['M222MixedCard']
    hi = labels['M222MixedEnd']
    if not lo == 49536 < hi <= 49920:
        raise ValueError('Mixed code capacity')
    patch(52, lo, b'\xff' * (hi - lo), data[at(20, lo):at(20, hi)])
    patch(2, 48468, bytes.fromhex('8d1307ee1400'), bytes.fromhex('a012209fe2ea'))
    patch(52, 54528, b'\xff', bytes([len(rows)]))
    fields = ('world', 'hi', 'x', 'y', 'tileset', 'layout_lo', 'layout_hi', 'effect', 'objects_lo', 'objects_hi')
    for j, key in enumerate(fields):
        values = [r[key[:-3]] & 255 if key.endswith('_lo') else r[key[:-3]] >> 8 if key.endswith('_hi') else r[key] for r in rows]
        patch(52, 54560 + j * 32, b'\xff' * len(rows), bytes(values))
    target[:] = rom
    return dict(version='m222-mixed-terminal-1', rows=rows, edits=edits, symbols=labels, new_ram_bytes=0, contract='Real card exit after collision/time/lives; host fortress effect, native card rewards preserved')

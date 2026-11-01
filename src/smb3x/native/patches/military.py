# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Bounded native Big Tanks treasure-to-host map-effect translation.'
from pathlib import Path
import json
import re
import subprocess
import tempfile
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source, rows):
    verify_base(source)
    keys = ('slot', 'host_type', 'hi', 'x', 'y', 'treasure', 'effect', 'receipt')
    rows = sorted(rows, key=lambda r: r['slot'])
    if len(rows) > 3 or len({r['slot'] for r in rows}) != len(rows):
        raise ValueError('Military identity/capacity')
    expected = {2: (14, 0, 64, 112, 0, 2), 3: (13, 0, 128, 112, 1, 4), 5: (14, 3, 64, 112, 4, 16)}
    for r in rows:
        if set(r) != set(keys) or r['slot'] not in expected or type(r['treasure']) is not bool:
            raise ValueError('Unreviewed military binding')
        if tuple((r[k] for k in ('host_type', 'hi', 'x', 'y', 'effect', 'receipt'))) != expected[r['slot']]:
            raise ValueError('Military physical host contract')
    symbols = json.loads((ROOT / 'native/symbols/m222_military_symbols.json').read_text())
    text = (ROOT / 'native/asm/m222_military.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'military.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        run = assemble_file(tmp / 'military.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (tmp / 'military.fns').read_text(), re.M)}
        data = (tmp / 'military.nes').read_bytes()
    rom = bytearray(target)
    edits = []

    def at(b, a):
        return 16 + b * 8192 + (a & 8191)

    def patch(b, a, before, after):
        o = at(b, a)
        if len(before) != len(after) or rom[o:o + len(before)] != before:
            raise ValueError(f'Military exact source guard {b}:{a:04X}')
        rom[o:o + len(after)] = after
        edits.append(dict(bank=b, address=a, size=len(after)))
    lo = labels['M222MilitaryTreasure']
    hi = labels['M222MilitaryEnd']
    if not lo == 50688 < hi <= 51199:
        raise ValueError('Military code capacity')
    patch(52, lo, b'\xff' * (hi - lo), data[at(20, lo):at(20, hi)])
    patch(5, 48301, bytes.fromhex('ee1400a9008d1307'), bytes.fromhex('a011209fe2eaeaea'))
    patch(52, 54016, b'\xff', bytes([len(rows)]))
    for j, key in enumerate(('slot', 'host_type', 'hi', 'x', 'y', 'treasure', 'effect')):
        patch(52, 54048 + j * 32, b'\xff' * len(rows), bytes((int(r[key]) for r in rows)))
    patch(52, 54432, b'\xff' * len(rows), bytes((r['receipt'] for r in rows)))
    target[:] = rom
    return dict(version='m222-military-context-1', rows=rows, edits=edits, symbols=labels, new_ram_bytes=0, contract='Native collected-chest delay terminal, assigned Big Tanks room, bound physical military slot; Air Force excluded')

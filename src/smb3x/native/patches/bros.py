# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Exact guarded complete-Bros battle overrides; physical map objects stay native.'
from pathlib import Path
import json
import re
import subprocess
import tempfile
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source, rows):
    verify_base(source)
    if len(target) != 786448:
        raise ValueError('architecture required')
    keys = ('world', 'slot', 'host_type', 'battle_type', 'tileset', 'layout', 'objects', 'prize', 'receipt')
    rows = sorted(rows, key=lambda r: (r['world'], r['slot']))
    if len(rows) > 31 or len({(r['world'], r['slot']) for r in rows}) != len(rows):
        raise ValueError('Bros table identity/capacity')
    for r in rows:
        if set(r) != set(keys) or r['world'] not in range(6) or r['slot'] not in range(2, 5) or (r['host_type'] not in (3, 4, 5, 6)) or (r['battle_type'] not in (3, 4, 5, 6)) or (r['tileset'] not in (1, 3, 9, 11, 12, 13)) or (not 40960 <= r['layout'] < 49152) or (not 49152 <= r['objects'] < 57344) or (not 1 <= r['prize'] <= 13) or (r['receipt'] not in (8, 16, 32, 64, 128)):
            raise ValueError('Unreviewed Bros binding')
    symbols = json.loads((ROOT / 'native/symbols/m222_bros_symbols.json').read_text())
    text = (ROOT / 'native/asm/m222_bros.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'bros.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        run = assemble_file(tmp / 'bros.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (tmp / 'bros.fns').read_text(), re.M)}
        data = (tmp / 'bros.nes').read_bytes()
    rom = bytearray(target)
    edits = []

    def at(b, a):
        return 16 + b * 8192 + (a & 8191)

    def patch(b, a, before, after):
        if len(before) != len(after):
            raise ValueError('Bros patch length')
        o = at(b, a)
        if rom[o:o + len(before)] != before:
            raise ValueError(f'Bros exact source guard {b}:{a:04X}')
        rom[o:o + len(after)] = after
        edits.append(dict(bank=b, address=a, size=len(after)))
    for bank, first, last, limit in [(12, 'M222BrosPrepareStub', 'M222BrosPrepareStubEnd', 49152), (4, 'M222BrosEnemyStub', 'M222BrosEnemyStubEnd', 49152), (52, 'M222BrosDispatch', 'M222BrosEnd', 51199)]:
        lo, hi = (labels[first], labels[last])
        if not lo < hi <= limit:
            raise ValueError('Bros code capacity')
        o = at(20 if bank == 52 else bank, lo)
        patch(bank, lo, b'\xff' * (hi - lo), data[o:o + hi - lo])
    table = symbols['Map_DoEnterViaID'] + 3
    for typ in (3, 4, 5, 6):
        patch(12, table + 2 * typ, symbols['MO_Unused'].to_bytes(2, 'little'), labels['M222BrosPrepareStub'].to_bytes(2, 'little'))
    old = b'\xb9' + symbols['BattleEnemy_ByEnterID'].to_bytes(2, 'little')
    a = symbols['ObjInit_HammerBro']
    sites = [p for p in range(a, a + 32) if source[at(4, p):at(4, p) + 3] == old]
    if len(sites) != 1:
        raise ValueError('Bros actor hook ambiguity')
    patch(4, sites[0], old, b' ' + labels['M222BrosEnemyStub'].to_bytes(2, 'little'))
    patch(27, 48063, bytes.fromhex('ad1307f027'), bytes.fromhex('a0104c9fe2'))
    patch(52, 53504, b'\xff', bytes([len(rows)]))
    fields = ('world', 'slot', 'host_type', 'battle_type', 'tileset', 'layout_lo', 'layout_hi', 'objects_lo', 'objects_hi', 'prize', 'receipt')
    for j, key in enumerate(fields):
        values = []
        for r in rows:
            v = r[key[:-3]] & 255 if key.endswith('_lo') else r[key[:-3]] >> 8 if key.endswith('_hi') else r[key]
            values.append(v)
        patch(52, 53536 + j * 32, b'\xff' * len(rows), bytes(values))
    target[:] = rom
    return dict(version='m222-bros-context-1', rows=rows, edits=edits, symbols=labels, new_ram_bytes=0, coin_ship='Native type11 override bypasses battle assignment; exact accepted prize/removal proof retained', map_icon='Physical native icon/type retained to preserve movement/transformation eligibility')

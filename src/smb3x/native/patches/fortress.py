# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Guarded special-context foundation. Not a production certification bypass.'
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source, rows):
    verify_base(source)
    if len(target) != 786448 or target[4:6] != bytes([32, 32]):
        raise ValueError('expanded architecture required')
    rows = sorted(rows, key=lambda r: (r['world'], r['hi'], r['x'], r['y']))
    keys = ('world', 'hi', 'x', 'y', 'tileset', 'layout', 'objects', 'effect', 'secret')
    if len(rows) > 127 or len({tuple((r[k] for k in keys[:4])) for r in rows}) != len(rows):
        raise ValueError('Special context table identity/capacity')
    for r in rows:
        if set(r) != set(keys) or not 0 <= r['world'] < 8 or (not 0 <= r['hi'] < 4) or (r['x'] not in range(0, 256, 16)) or (r['y'] not in range(32, 176, 16)) or (r['tileset'] not in (2, 9, 10, 11, 12)) or (not 40960 <= r['layout'] < 49152) or (not 49152 <= r['objects'] < 57344) or (not 0 <= r['effect'] <= 7) or (type(r['secret']) is not bool):
            raise ValueError('Unreviewed special context row')
    symbols = json.loads((ROOT / 'native/symbols/m222_special_symbols.json').read_text())
    text = (ROOT / 'native/asm/m222_special.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'special.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        run = assemble_file(tmp / 'special.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (tmp / 'special.fns').read_text(), re.M)}
        data = (tmp / 'special.nes').read_bytes()
    rom = bytearray(target)
    edits = []

    def at(bank, address):
        return 16 + bank * 8192 + (address & 8191)

    def patch(bank, address, before, after):
        if len(before) != len(after):
            raise ValueError('Special patch length')
        for b in [bank, bank + 32] if bank in (30, 31) else [bank]:
            off = at(b, address)
            if rom[off:off + len(before)] != before:
                raise ValueError(f'Special exact source guard {b}:{address:04X}')
            rom[off:off + len(after)] = after
            edits.append(dict(bank=b, address=address, size=len(after)))

    def absop(op, name):
        return bytes([op]) + symbols[name].to_bytes(2, 'little')

    def call(address):
        return b' ' + address.to_bytes(2, 'little')
    old = absop(173, 'PAGE_C000') + b'H\xa93' + absop(141, 'PAGE_C000') + call(symbols['PRGROM_Change_C000']) + call(49152) + b'\xa8h' + absop(141, 'PAGE_C000') + call(symbols['PRGROM_Change_C000']) + b'\x98`'
    end = labels['M222BankCallEnd']
    if end != 58044:
        raise ValueError('Special fixed trampoline capacity')
    after = data[at(31, 58015):at(31, end)]
    lookup = bytes.fromhex('b9a79a60')
    patch(31, 58044, b'\xff' * 4, lookup)
    branch_sites = []
    for address in range(57946, 57977):
        off = at(31, address)
        op = rom[off]
        delta = rom[off + 1]
        if op in (144, 176, 208) and address + 2 + (delta if delta < 128 else delta - 256) == 58040:
            branch_sites.append(address)
    if len(branch_sites) != 3:
        raise ValueError('External render lookup branch ownership')
    for address in branch_sites:
        off = at(31, address)
        before = bytes(rom[off:off + 2])
        patch(31, address, before, bytes([before[0], 58044 - address - 2]))
    patch(31, 58015, old + lookup, after)
    lo = labels['M222OrbEffect']
    hi = labels['M222OrbEffectEnd']
    if not 49133 == lo < hi <= 49152:
        raise ValueError('Orb wrapper capacity')
    patch(3, lo, b'\xff' * (hi - lo), data[at(3, lo):at(3, hi)])
    bank = bytearray(b'\xff' * 8192)
    size = labels['M222SpecialEnd'] - 49152
    if not 0 < size <= 384:
        raise ValueError('Special code capacity')
    bank[:size] = data[at(20, 49152):at(20, 49152) + size]
    if not labels['M222OrbObjects'] == 50944 < labels['M222ObjectsEnd'] <= 51199:
        raise ValueError('Special object guard capacity')
    bank[1792:labels['M222ObjectsEnd'] - 49152] = data[at(20, 50944):at(20, labels['M222ObjectsEnd'])]
    if not labels['M222SecretTerminal'] == 51008 < labels['M222SecretTerminalEnd'] <= 51199:
        raise ValueError('Secret terminal capacity')
    bank[1856:labels['M222SecretTerminalEnd'] - 49152] = data[at(20, 51008):at(20, labels['M222SecretTerminalEnd'])]
    bank[2047] = len(rows)
    for i, r in enumerate(rows):
        for page, v in enumerate([r['world'], r['hi'], r['x'], r['y'], r['tileset'], r['layout'] & 255, r['layout'] >> 8, r['effect'], int(r['secret'])], 8):
            bank[page * 256 + i] = v
        bank[5760 + i] = r['objects'] & 255
        bank[5888 + i] = r['objects'] >> 8
    bank[6144:] = source[at(29, 55296):at(29, 55296) + 2048]
    if len(bank) != 8192:
        raise ValueError('Special DPCM allocation')
    patch(52, 49152, b'\xff' * 8192, bank)
    patch(25, 48768, bytes.fromhex('adae79c901'), bytes.fromhex('a00d4c9fe2'))
    a = symbols['ObjNorm_BoomBoomQBall']
    b = symbols['PRG003_A8FE']
    wanted = absop(141, 'Map_DoFortressFX')
    sites = [p for p in range(a, b) if source[at(3, p):at(3, p) + 3] == wanted]
    if len(sites) != 1:
        raise ValueError('Orb terminal hook ambiguity')
    patch(3, sites[0], wanted, call(lo))
    tense = bytes([169, 24]) + absop(172, 'World_Num') + b'\xd0\x01\n'
    a = symbols['PRG003_AC4D']
    b = symbols['PRG003_AC5D']
    sites = [p for p in range(a, b) if source[at(3, p):at(3, p) + len(tense)] == tense]
    if len(sites) != 1:
        raise ValueError('Boom Boom tense hook ambiguity')
    patch(3, sites[0], tense, b'\xa0\x0b' + call(58015) + b'\xea' * 3)
    speed = absop(173, 'World_Num') + b'\xd0\x02\xc8\xc8' + absop(185, 'BoomBoom_FinalAttackXVel')
    a = symbols['PRG003_AD29']
    b = symbols['PRG003_AD3E']
    sites = [p for p in range(a, b) if source[at(3, p):at(3, p) + len(speed)] == speed]
    if len(sites) != 1:
        raise ValueError('Boom Boom speed hook ambiguity')
    patch(3, sites[0], speed, bytes([132, symbols['Temp_Var16'], 160, 12]) + call(58015) + b'\xea' * 3)
    if rom[at(30, 32768):at(30, 32768) + 16384] != rom[at(62, 32768):at(62, 32768) + 16384]:
        raise ValueError('Special fixed mirror mismatch')
    target[:] = rom
    return dict(version='m222-special-context-2', rows=rows, symbols=labels, edits=edits, bank=52, dpcm_sha256=hashlib.sha256(bank[6144:]).hexdigest(), new_ram_bytes=0, certification='native mechanism foundation; separate category certification mandatory')

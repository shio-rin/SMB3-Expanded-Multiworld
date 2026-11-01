# SPDX-License-Identifier: MPL-2.0
"""Exact-guarded bank48 data extension; no native hooks or persistent RAM."""
from pathlib import Path
import hashlib, json, re, tempfile, subprocess
from ...shared.resources import RESOURCE_ROOT as ROOT
from ...planning import special_palettes
P = vars(special_palettes)
from ...planning import boss_palettes
BOSS = vars(boss_palettes)

def assemble():
    text = (ROOT / 'native/asm/m24_special_content.asm').read_text()
    symbols = json.loads((ROOT / 'native/symbols/m20_symbols.json').read_text())
    symbols.update(Temp_Var1=0, Temp_Var2=1, LevelJctBQ_Flag=32438, Level_JctBackupTileset=32439, Map_EnterViaID=30)
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    key = hashlib.sha256((prelude + text).encode()).hexdigest()
    cache = ROOT / 'native/certificates/m24-special-palette-assembly.json'
    if cache.exists():
        row = json.loads(cache.read_text())
        assert row['input_sha256'] == key
        code = bytes.fromhex(row['code'])
        assert hashlib.sha256(code).hexdigest() == row['code_sha256']
        return (code, row)
    folder = ROOT / 'generated/m24-special/assembly'
    folder.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        tmp = Path(tmp)
        (tmp / 'special.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        exe = ROOT / 'references/smb3/nesasm.exe'
        assert hashlib.sha256(exe.read_bytes()).hexdigest() == 'd6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'
        r = subprocess.run([str(exe), 'special.asm'], cwd=tmp, capture_output=True, text=True, check=True)
        assert 'error' not in (r.stdout + r.stderr).lower(), r.stdout + r.stderr
        sym = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (tmp / 'special.fns').read_text(), re.M)}
        assert sym['ContentExtension'] == 49152 and sym['ContentExtensionEnd'] < 50944
        code = (tmp / 'special.nes').read_bytes()[16 + 20 * 8192:16 + 20 * 8192 + sym['ContentExtensionEnd'] - 49152]
    row = dict(input_sha256=key, code=code.hex(), code_sha256=hashlib.sha256(code).hexdigest(), symbols=sym)
    return (code, row)

def install(rom, base, selection):
    assert base['patch_version'] in ('m242-native-2', 'm243-native-1')
    ext = base['m242_extension']
    assert ext and ext['code_bytes'] == 188 and (ext['areas'] == 143)
    start = 16 + 48 * 8192
    bank = bytearray(rom[start:start + 8192])
    before = bytes(rom)
    assert hashlib.sha256(bank).hexdigest() == ext['output_bank_sha256']
    assert hashlib.sha256(bank[:188]).hexdigest() == 'a84e535e404c1f7bc953c9e7223021ca5b221f75a0296fbae8871aa40f15d241'
    code, assembly = assemble()
    bank[:1792] = b'\xff' * 1792
    bank[:len(code)] = code
    indices = dict(ext['themes'])
    assert len(indices) == 49
    for t in P['ADAPTED'] + BOSS['THEMES']:
        i = len(indices) + 1
        indices[t['id']] = i
        assert i < 64
        bank[3616 + i] = 53248 + 16 * i & 255
        bank[3680 + i] = 53248 + 16 * i >> 8
        bank[4096 + 16 * i:4096 + 16 * i + 16] = bytes(t['background'])
    n = bank[2047]
    known = {(bank[2048 + i], bank[2304 + i] + 256 * bank[2560 + i]) for i in range(n)}
    for row in selection['areas']:
        assert (row['tileset'], row['layout']) not in known, 'Existing area cannot be overwritten'
        assert n < 255
        tid = BOSS['render_id'](row['theme'], row['category'])
        for page, value in ((2048, row['tileset']), (2304, row['layout'] & 255), (2560, row['layout'] >> 8), (2816, 0), (3072, indices.get(tid, 0)), (3840, 0)):
            bank[page + n] = value
        n += 1
    bank[2047] = n
    bank[3592] = len(indices) + 1
    for world in range(1, 8):
        row = next((r for r in selection['areas'] if r['symbol'] == f'W{world}AirshipL'))
        bank[3600 + world - 1] = indices.get(row['theme'], 0)
    assert bank[6144:] == rom[start + 6144:start + 8192]
    rom[start:start + 8192] = bank
    assert before[:start] == rom[:start] and before[start + 8192:] == rom[start + 8192:]
    return dict(version=P['VERSION'], definition_revision=BOSS['VERSION'], bank=48, areas=n, nonzero_slots=len(indices), new_area_rows=len(selection['areas']), new_slots=9, code_bytes=len(code), assembly=assembly, new_hooks=0, new_ram=0, new_chr=0, themes=indices, bank_sha256=hashlib.sha256(bank).hexdigest())

# SPDX-License-Identifier: MPL-2.0
"""Bounded bank48 palette replacement over the verified preceding native build."""
from pathlib import Path
import hashlib, json, re, subprocess, tempfile
from ...shared.resources import RESOURCE_ROOT as ROOT
from ...planning import palette_library
CONTRACT = vars(palette_library)
EXTERNAL_AUTUMN = {**next((t for t in CONTRACT['ACCEPTED'] if t['id'] == 'hills-autumn')), 'id': 'hills-autumn-external'}
EXTERNAL_AUTUMN['background'] = list(EXTERNAL_AUTUMN['background'])
EXTERNAL_AUTUMN['background'][3] = EXTERNAL_AUTUMN['background'][0]
THEMES = CONTRACT['THEMES'] + [EXTERNAL_AUTUMN]

def assemble():
    text = (ROOT / 'native/asm/m24_content.asm').read_text()
    symbols = json.loads((ROOT / 'native/symbols/m20_symbols.json').read_text())
    symbols.update(Temp_Var1=0, Temp_Var2=1, LevelJctBQ_Flag=32438, Level_JctBackupTileset=32439)
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    cache = ROOT / 'native/certificates/m241-palette-assembly.json'
    if cache.exists():
        row = json.loads(cache.read_text())
        data = bytes.fromhex(row['code'])
        if row['input_sha256'] != hashlib.sha256((prelude + text).encode()).hexdigest() or row['code_sha256'] != hashlib.sha256(data).hexdigest() or len(data) != 188 or (row['symbols']['ContentExtension'] != 49152) or (row['symbols']['ContentExtensionEnd'] != 49152 + len(data)):
            raise ValueError('palette assembly cache/source mismatch')
        return (data, row['symbols'])
    folder = ROOT / 'generated/m24/assembly'
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder) as temp:
        temp = Path(temp)
        (temp / 'content.asm').write_text(prelude + text, encoding='utf-8', newline='\n')
        executable = ROOT / 'references/smb3/nesasm.exe'
        if hashlib.sha256(executable.read_bytes()).hexdigest() != 'd6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501':
            raise ValueError('Assembler mismatch')
        p = subprocess.run([str(executable), 'content.asm'], cwd=temp, capture_output=True, text=True, check=True)
        if 'error' in (p.stdout + p.stderr).lower():
            raise ValueError(p.stdout + p.stderr)
        local = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', (temp / 'content.fns').read_text(), re.M)}
        lo = local['ContentExtension']
        hi = local['ContentExtensionEnd']
        if lo != 49152 or hi > 50944:
            raise ValueError('extension exceeds existing code allocation')
        data = (temp / 'content.nes').read_bytes()[16 + 20 * 8192:16 + 20 * 8192 + hi - lo]
    return (data, local)

def _install(rom, base, selection):
    if base['patch_version'] not in ('m232-native-1', 'm241-native-1') or base['content_extension']['bank'] != 48:
        raise ValueError('baseline mismatch')
    original = bytes(rom)
    start = 16 + 48 * 8192
    bank = bytearray(rom[start:start + 8192])
    code, symbols = assemble()
    old_size = base['content_extension']['code_bytes']
    if old_size != 114 or hashlib.sha256(bank[:old_size]).hexdigest() != '6c3d2b64a98358ce83eb0995c6442db0f7c14be247433e27722361e929056387' or bank[2047] != base['content_extension']['areas']:
        raise ValueError('Exact accepted lookup source guard')
    bank[:1792] = b'\xff' * 1792
    bank[:len(code)] = code
    rows = list(selection['areas'])
    old_music = {r['id']: r for r in base['audiovisual']['music']}
    old_palettes = {r['area']: r['theme'] for r in base['audiovisual']['palettes']}
    known = {r['id'] for r in rows}
    external = []
    for aid, row in old_music.items():
        if aid in known:
            continue
        if not row['content'].startswith('classic/'):
            raise ValueError('Unresolved accepted area ' + aid)
        retained = {**row, 'theme': old_palettes.get(aid)}
        rows.append(retained)
        external.append(dict(area=aid, content=row['content'], theme=retained['theme'], policy='exact accepted Classic selection; no new M24 recolor'))
    if len(rows) > 255 or len(THEMES) >= 64:
        raise ValueError('table capacity exceeded')
    indices = {t['id']: i + 1 for i, t in enumerate(THEMES)}
    bank[2047] = len(rows)
    bank[2048:3328] = bytes(1280)
    for i, a in enumerate(rows):
        old = old_music.get(a['id'], {})
        music = old.get('selector', 0) if old.get('custom') or old.get('reason') == 'inherited-parent' else 0
        for page, value in ((2048, a['tileset']), (2304, a['layout'] & 255), (2560, a['layout'] >> 8), (2816, music), (3072, indices.get(a['theme'], 0))):
            bank[page + i] = value
    bank[3840:4096] = bytes(256)
    chosen = {a['id']: a['theme'] for a in rows}
    for i, a in enumerate(rows):
        target = selection['big_question_bindings'].get(a['id'])
        bank[3840 + i] = indices.get(chosen.get(target), 0)
    bank[3584:3593] = bytes(9)
    bank[3592] = len(THEMES) + 1
    bank[3616:3744] = bytes(128)
    bank[4096:5120] = bytes(1024)
    for t in THEMES:
        v = t['background']
        i = indices[t['id']]
        address = 53248 + i * 16
        if len(v) != 16 or any((type(x) is not int or not 0 <= x < 64 or x % 16 == 13 for x in v)) or len({v[j] for j in (0, 4, 8, 12)}) != 1:
            raise ValueError('Unsafe theme ' + t['id'])
        bank[3616 + i] = address & 255
        bank[3680 + i] = address >> 8
        bank[4096 + i * 16:4096 + i * 16 + 16] = bytes(v)
    for world, tid in selection['map_themes'].items():
        bank[3584 + int(world) - 1] = indices.get(tid, 0)
    rom[start:start + 8192] = bank
    if original[:start] != rom[:start] or original[start + 8192:] != rom[start + 8192:]:
        raise ValueError('escaped bank48')
    if original[start + 6144:start + 8192] != rom[start + 6144:start + 8192]:
        raise ValueError('DPCM mirror changed')
    return dict(bank=48, code_bytes=len(code), previous_code_bytes=old_size, symbols=symbols, areas=len(rows), themes=indices, retained_external=external, baseline_bank_sha256=hashlib.sha256(original[start:start + 8192]).hexdigest(), output_bank_sha256=hashlib.sha256(bank).hexdigest(), new_persistent_ram_bytes=0)
from ...planning import palettes as corrected_palettes
P = vars(corrected_palettes)

def install(rom, base, selection):
    P['corrected'](THEMES)
    result = _install(rom, base, selection)
    start = 16 + 48 * 8192
    for theme, edit in P['CORRECTIONS'].items():
        offset = start + 4096 + 16 * result['themes'][theme] + edit['index']
        if rom[offset] != edit['old']:
            raise ValueError('palette byte source guard')
        rom[offset] = edit['new']
    result['output_bank_sha256'] = hashlib.sha256(rom[start:start + 8192]).hexdigest()
    result['definition_revision'] = 'm242-fortress-contrast-1'
    result['definition_corrections'] = P['CORRECTIONS']
    return result

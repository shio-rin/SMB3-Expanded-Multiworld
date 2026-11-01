# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Exact-source-guarded poison mechanism; eligibility is a separate policy.'
from pathlib import Path
import re, json, subprocess, tempfile
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT

def original_sun_areas():
    registry = json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_text())['contents']
    catalog = json.loads((ROOT / 'planning/data/hazards_m221.json').read_text())['contents']
    admitted = {c['content_id'] for c in catalog if any((a['sun_zones'] for a in c['areas']))}
    return {(c['tileset'], c['layout']): c for c in registry if c['content_id'] in admitted}

def install(target, source, placements, suns=(), *, graphics=False, collision_area=None):
    verify_base(source)
    rom = bytearray(target)
    if len(rom) != 655376 or len(placements) > 127 or len(suns) > 127:
        raise ValueError('architecture/capacity')
    symbols = json.loads((ROOT / 'native/symbols/m221_symbols.json').read_text())
    text = (ROOT / 'native/asm/m221_poison.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    layout = 0 if collision_area is None else collision_area['layout']
    if collision_area is not None and (collision_area['id'] != 'classic/smw/yoshis-island-2/main' or collision_area['tileset'] != 3 or (not 34304 <= layout < 40960)):
        raise ValueError('SMW flat collision identity')
    prelude += f'M221SmwLayout = ${layout:04X}\n'
    prelude += f"M221SunDesertEnabled = {int(any((p['tileset'] == 9 and p['layout'] == 46906 for p in suns)))}\nM221SunPlainsEnabled = {int(any((p['tileset'] == 1 and p['layout'] == 47292 for p in suns)))}\n"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'poison.asm').write_text(prelude + text)
        run = assemble_file(tmp / 'poison.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\dA-Fa-f]+)', (tmp / 'poison.fns').read_text(), re.M)}
        data = (tmp / 'poison.nes').read_bytes()
    edits = []

    def patch(bank, cpu, origin, old, new):
        if len(old) != len(new):
            raise ValueError('Patch length')
        for b in [bank, bank + 32] if bank in (30, 31) else [bank]:
            off = 16 + b * 8192 + cpu - origin
            if rom[off:off + len(old)] != old:
                raise ValueError(f'Poison source guard {b}:{cpu:04x}')
            rom[off:off + len(new)] = new
            edits.append({'bank': b, 'cpu': cpu, 'length': len(new)})
    allocations = [(26, 40960, 'M221CopyEnemyList', 'M221CopyEnemyListEnd', 49152), (1, 40960, 'M21MushroomInit', 'M21PoisonInitEnd', 49152), (1, 40960, 'M21ChoosePowerup', 'M21PoisonChooseEnd', 47232), (5, 40960, 'M21SunWait', 'M21SunWaitEnd', 49130), (5, 40960, 'M221SunEdge', 'M221SunEdgeEnd', 49152), (31, 57344, 'M21HazardCall', 'M21HazardCallEnd', 58048), (31, 57344, 'M221SelectCollision', 'M221SelectCollisionEnd', 65344), (31, 57344, 'M221SpriteBank', 'M221SpriteBankEnd', 65344)]
    if graphics:
        allocations.append((7, 40960, 'M21DrawFinish', 'M21DrawFinishEnd', 49152))
    for b, origin, first, last, limit in allocations:
        lo, hi = (labels[first], labels[last])
        if not lo < hi <= limit:
            raise ValueError('Poison code allocation exceeded')
        off = 16 + b * 8192 + lo - origin
        patch(b, lo, origin, b'\xff' * (hi - lo), data[off:off + hi - lo])

    def call(name):
        return b' ' + labels[name].to_bytes(2, 'little')
    if any(((p['tileset'], p['layout']) in ((9, 46906), (1, 47292)) for p in suns)):
        patch(0, 51834, 49152, b')\x7f\x9d' + (symbols['PatTable_BankSel'] + 4).to_bytes(2, 'little'), call('M221SpriteBank') + b'\xea\xea')
    patch(8, symbols['PRG008_A347'], 40960, b'\x8c' + symbols['Level_SlopeEn'].to_bytes(2, 'little'), call('M221SelectCollision'))
    opcode = b' ' + symbols['LevelLoad_CopyObjectList'].to_bytes(2, 'little')
    native = source[16 + 30 * 8192:16 + 31 * 8192]
    sites = [i for i in range(2560, 3072) if native[i:i + 3] == opcode]
    if len(sites) != 1:
        raise ValueError('Enemy copy source layout')
    patch(30, 32768 + sites[0], 32768, opcode, call('M221CopyEnemyList'))
    patch(1, symbols['ObjInit_PUpMush'], 40960, b' ' + symbols['Mushroom_SetFall'].to_bytes(2, 'little'), call('M21MushroomInit'))
    patch(1, symbols['ObjHit_PUpMush'], 40960, b'\xa9\x01\x85' + bytes([symbols['Temp_Var1']]), b'L' + labels['M21MushroomHit'].to_bytes(2, 'little') + b'\xea')
    patch(1, symbols['PRG001_A56F'] + 13, 40960, b'\xb9' + symbols['Bouncer_PUp'].to_bytes(2, 'little'), call('M21ChoosePowerup'))
    patch(5, symbols['Sun_WaitFarEnough'], 40960, b'\xa9\x00\x9d' + symbols['Objects_Frame'].to_bytes(2, 'little'), b'L' + labels['M21SunWait'].to_bytes(2, 'little') + b'\xea\xea')
    native5 = source[16 + 5 * 8192:16 + 6 * 8192]
    edge = b'\xa9\x91\x99' + (symbols['Sprite_RAM'] + 1).to_bytes(2, 'little')
    edge_sites = [i for i in range(3671, 3880) if native5[i:i + 5] == edge]
    if len(edge_sites) != 2:
        raise ValueError('Native Sun extra edge source guard')
    for i in edge_sites:
        patch(5, 40960 + i, 40960, edge, call('M221SunEdge') + b'\xea\xea')
    patch(5, symbols['ObjectGroup04_InitJumpTable'] + (175 - 144) * 2, 40960, symbols['ObjInit_Sun'].to_bytes(2, 'little'), labels['M21SunInit'].to_bytes(2, 'little'))
    if graphics:
        opcode = b' ' + symbols['Gameplay_UpdateAndDrawMisc'].to_bytes(2, 'little')
        native = source[16 + 30 * 8192:16 + 31 * 8192]
        sites = [i for i in range(3584, 3904) if native[i:i + 3] == opcode]
        if len(sites) != 1:
            raise ValueError('Post-draw hook source layout')
        patch(30, 32768 + sites[0], 32768, opcode, call('M21DrawFinish'))
    bank = bytearray(b'\xff' * 8192)
    size = labels['M221HazardsEnd'] - 49152
    if not 0 < size <= 2047:
        raise ValueError('Hazard lookup capacity')
    bank[:size] = data[16 + 20 * 8192:16 + 20 * 8192 + size]
    bank[6144:] = source[16 + 29 * 8192 + 6144:16 + 30 * 8192]
    bank[2047] = len(placements)
    seen = set()
    for i, p in enumerate(sorted(placements, key=lambda p: (p['tileset'], p['layout'], p['x'], p['y']))):
        key = tuple((p[k] for k in ('tileset', 'layout', 'x', 'y')))
        external = p['tileset'] in (3, 14) and 34304 <= p['layout'] <= 40959
        reviewed_area = external
        if not external and 'source_rom_offset' in p:
            original_catalog = json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_text())['contents']
            content = next((c for c in original_catalog if (c['tileset'], c['layout']) == (p['tileset'], p['layout'])), None)
            catalog = json.loads((ROOT / 'planning/data/hazards_m221.json').read_text())
            certified = next((b for c in catalog['contents'] if content and c['content_id'] == content['content_id'] for a in c['areas'] if a['id'] == 'main' for b in a['blocks'] if (b['x'] * 16, b['y'] * 16) == (p['x'], p['y'])), None)
            if not certified or any((certified[k] != p[k] for k in ('source_rom_offset', 'source_bytes'))):
                raise ValueError('Original poison registry mismatch')
            offset = p['source_rom_offset']
            expected = bytes.fromhex(p['source_bytes'])
            if len(expected) != 3 or source[offset:offset + 3] != expected:
                raise ValueError('Original block source bytes')
            reviewed_area = True
        if key in seen or not reviewed_area or (not 0 <= p['x'] < 3840) or (not 0 <= p['y'] < 432):
            raise ValueError('Unreviewed poison identity')
        seen.add(key)
        for page, value in [(8, p['tileset']), (9, p['layout'] & 255), (10, p['layout'] >> 8), (11, p['x'] & 255), (12, p['x'] >> 8), (13, p['y'] & 255), (14, p['y'] >> 8)]:
            bank[page * 256 + i] = value
    bank[4095] = len(suns)
    seen = set()
    for i, p in enumerate(sorted(suns, key=lambda p: (p['tileset'], p['layout']))):
        key = (p['tileset'], p['layout'])
        original_record = original_sun_areas().get(key)
        original = original_record is not None
        if key in seen or not (original or (p['tileset'] == 3 and 34304 <= p['layout'] <= 40959)) or (not 256 <= p['activation_x'] < 3584):
            raise ValueError('Unreviewed Sun identity')
        seen.add(key)
        if original:
            assert original_record['enemy_bank'] == 6 and original_record['tileset'] in (1, 3, 9)
            ptr = 16 + 6 * 8192 + original_record['objects'] - 49152
            records = []
            for j in range(1, 143, 3):
                if source[ptr + j] == 255:
                    break
                records.append(tuple(source[ptr + j:ptr + j + 3]))
            else:
                raise ValueError('Original enemy terminator/capacity')
            if len(records) >= 47 or any((r[0] == 175 for r in records)) or [r[1] for r in records] != sorted((r[1] for r in records)):
                raise ValueError('Original enemy insertion contract')
        for page, value in [(16, p['tileset']), (17, p['layout'] & 255), (18, p['layout'] >> 8), (19, p['activation_x'] >> 8), (20, p['activation_x'] & 255)]:
            bank[page * 256 + i] = value
        bank[5376 + i] = p['spawn_column']
        bank[5632 + i] = int(original)
    patch(51, 49152, 49152, b'\xff' * 8192, bank)
    appearance = {'appearance': 'native palette3 provisional; final danger artwork pending'}
    if graphics:
        from .poison_graphics import expand
        appearance = expand(rom, source)
        registry = json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_text())['contents']
        for cid, ts, composite_layout, allowed_ids in (('smb3-prg1-w2-2-5', 9, 46906, {137, 109, 114, 65}), ('smb3-prg1-w3-3-7', 1, 47292, {41, 108, 166, 110, 65})):
            c = next((c for c in registry if c['content_id'] == cid))
            if (c['tileset'], c['layout']) != (ts, composite_layout) or {r['id'] for r in c['enemy_records']} != allowed_ids:
                raise ValueError('Sun composite source object set')
        chr_start = 16 + 524288
        src_chr = 16 + 262144
        page = bytearray(source[src_chr + 10 * 1024:src_chr + 11 * 1024])
        page[512:704] = source[src_chr + 50 * 1024 + 256:src_chr + 50 * 1024 + 448]
        off = chr_start + 136 * 1024
        if any(rom[off:off + 1024]):
            raise ValueError('Sun composite CHR136 ownership')
        rom[off:off + 1024] = page
        import hashlib
        appearance['sun_composite'] = {'page': 136, 'base_page': 10, 'sun_source_page': 50, 'source_patterns': '90..9B', 'destination_patterns': 'A0..AB', 'content_ids': ['smb3-prg1-w2-2-5', 'smb3-prg1-w3-3-7'], 'sha256': hashlib.sha256(page).hexdigest()}
    target[:] = rom
    return {'version': 'm221-hazard-native-3', 'symbols': labels, 'edits': edits, 'placements': placements, 'suns': suns, 'flat_collision_content': None if collision_area is None else {'id': collision_area['id'], 'tileset': 3, 'layout': layout}, 'marker': 'Objects_SprAttr bit2; no new RAM', 'graphics': appearance}

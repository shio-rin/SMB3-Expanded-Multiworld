# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Guarded native generator copies. Callers must separately certify area graphs.'
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
from ..rom import verify_base
from ...shared.resources import RESOURCE_ROOT as ROOT
VERSION = 'm21-generator-copy-1'
REGIONS = {3: (16, 49), 14: (13, 50)}
PREFIX_END = 1399
DATA_START = 1536

def sha(data):
    return hashlib.sha256(data).hexdigest()

def install(rom, source, areas, *, scenery=False):
    target = rom
    rom = bytearray(rom)
    verify_base(source)
    if len(rom) != 655376 or rom[4] != 32:
        raise ValueError('Expected accepted expanded MMC3 architecture')
    symbols = json.loads((ROOT / 'native/symbols/m221_symbols.json').read_text())
    if symbols['W2PY_InsideL'] != 42359 or symbols['W502L'] != 42359:
        raise ValueError('Unsupported generator source layout')
    text = (ROOT / 'native/asm/m22_loader.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'loader.asm').write_text(prelude + text)
        run = assemble_file(tmp / 'loader.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        labels = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\dA-Fa-f]+)', (tmp / 'loader.fns').read_text(), re.M)}
        data = (tmp / 'loader.nes').read_bytes()
    lo, hi = (labels['M21TerrainBank'], labels['M21TerrainBankEnd'])
    if lo != 57977 or not lo < hi <= 58048:
        raise ValueError('Loader overlaps native DPCM code or accepted trampoline')

    def patch(bank, offset, before, after):
        if len(before) != len(after):
            raise ValueError('Patch length')
        for b in [bank, bank + 32] if bank in (30, 31) else [bank]:
            pos = 16 + b * 8192 + offset
            if rom[pos:pos + len(before)] != before:
                raise ValueError(f'Native source guard {b}:{offset:04x}')
            rom[pos:pos + len(after)] = after
    off = 16 + 31 * 8192 + lo - 57344
    patch(31, lo - 57344, b'\xff' * (hi - lo), data[off:off + hi - lo])
    if scenery:
        for first, last, limit in [('M21RenderBank', 'M21RenderBankEnd', 57968), ('M21OriginalRenderBank', 'M21OriginalRenderBankEnd', 58048)]:
            begin, end = (labels[first], labels[last])
            if not begin < end <= limit:
                raise ValueError('Scenery selector allocation')
            off = 16 + 31 * 8192 + begin - 57344
            patch(31, begin - 57344, b'\xff' * (end - begin), data[off:off + end - begin])
        opcode = b'\xb9' + symbols['TileLayoutPage_ByTileset'].to_bytes(2, 'little')
        native = source[16 + 30 * 8192:16 + 31 * 8192]
        sites = [i for i in range(6853, 7168) if native[i:i + 3] == opcode]
        if len(sites) != 4:
            raise ValueError('Runtime tile lookup source layout')
        for site in sites:
            patch(30, site, opcode, b' ' + labels['M21RenderBank'].to_bytes(2, 'little'))
    candidates = [i for i in range(2427, 2475) if source[16 + 30 * 8192 + i:16 + 30 * 8192 + i + 3] == bytes.fromhex('b9e983')]
    if len(candidates) != 1:
        raise ValueError('Ambiguous initial terrain bank selection')
    patch(30, candidates[0], bytes.fromhex('b9e983'), b' ' + lo.to_bytes(2, 'little'))
    banks = {}
    for tileset, (original, bank) in REGIONS.items():
        start = 16 + bank * 8192
        if rom[start:start + 8192] != b'\xff' * 8192:
            raise ValueError('Content bank already owned')
        payload = bytearray(b'\xff' * 8192)
        payload[:PREFIX_END] = source[16 + original * 8192:16 + original * 8192 + PREFIX_END]
        if scenery and tileset == 3:
            if payload[775] != 255:
                raise ValueError('Cloud quartet source guard')
            payload[775] = 253
            begin, end = (labels['M21Backdrop'], labels['M21BackdropEnd'])
            if begin != 42368 or not begin < end <= 42496:
                raise ValueError('Backdrop code capacity')
            offset = 16 + 16 * 8192 + begin - 40960
            payload[begin - 40960:end - 40960] = data[offset:offset + end - begin]
            table = symbols['LeveLoad_FixedSizeGen_TS3'] - 40960 - 4
            if payload[table:table + 2] != symbols['LoadLevel_Tunnel'].to_bytes(2, 'little'):
                raise ValueError('Backdrop generator source guard')
            payload[table:table + 2] = begin.to_bytes(2, 'little')
            for quadrant, pattern in enumerate((5, 6, 7, 8)):
                if payload[quadrant * 256 + 13] != 255:
                    raise ValueError('Unused backdrop tile source guard')
                payload[quadrant * 256 + 13] = pattern
            for quadrant, pattern in enumerate((5, 6, 7, 8)):
                if payload[quadrant * 256 + 134] != pattern:
                    raise ValueError('SMW decorative dirt source guard')
                payload[quadrant * 256 + 134] = 119
        banks[tileset] = payload
    cursors = {k: DATA_START for k in banks}
    rows = []
    seen = set()
    for area in sorted(areas, key=lambda a: a['id']):
        if area['id'] in seen or area['tileset'] not in banks:
            raise ValueError('Duplicate area or unsupported generator')
        seen.add(area['id'])
        stream = area['terrain']
        if not isinstance(stream, bytes) or len(stream) < 10 or stream[-1] != 255:
            raise ValueError('Unterminated terrain stream')
        if stream[4] & 15 > 14 or stream[6] & 16:
            raise ValueError('Horizontal RAM limit or unsupported vertical stage')
        ts = area['tileset']
        p = cursors[ts]
        if p + len(stream) > 8192:
            raise ValueError('Generator-copy capacity exceeded')
        banks[ts][p:p + len(stream)] = stream
        rows.append({'id': area['id'], 'tileset': ts, 'bank': REGIONS[ts][1], 'virtual_pointer': 32768 + p, 'pointer': 40960 + p, 'length': len(stream), 'sha256': sha(stream)})
        cursors[ts] += len(stream)
    by_id = {r['id']: r for r in rows}
    for area in areas:
        row = by_id[area['id']]
        alternate = area.get('alternate')
        if alternate is None:
            if area['terrain'][:4] != bytes(4):
                raise ValueError('Unbound alternate header')
            continue
        other = by_id.get(alternate)
        if other is None or next((a for a in areas if a['id'] == alternate)).get('alternate') != area['id']:
            raise ValueError('Missing or nonreciprocal area dependency')
        enemy = area.get('alternate_objects')
        if type(enemy) is not int or not 56064 <= enemy < 57344:
            raise ValueError('Unreviewed alternate enemy pointer')
        p = row['pointer'] - 40960
        payload = banks[row['tileset']]
        payload[p:p + 2] = other['virtual_pointer'].to_bytes(2, 'little')
        payload[p + 2:p + 4] = enemy.to_bytes(2, 'little')
        payload[p + 6] = payload[p + 6] & 240 | other['tileset']
        row['alternate'] = alternate
        row['sha256'] = sha(payload[p:p + row['length']])
    for ts, payload in banks.items():
        start = 16 + REGIONS[ts][1] * 8192
        rom[start:start + 8192] = payload
    target[:] = rom
    return {'version': VERSION, 'areas': rows, 'symbols': labels, 'external_cloud_quartet_fix': scenery, 'external_smw_decorative_dirt': scenery, 'hook': 32768 + candidates[0], 'fixed_bytes': hi - lo, 'banks': [{'tileset': ts, 'bank': REGIONS[ts][1], 'source_bank': REGIONS[ts][0], 'prefix_sha256': sha(payload[:PREFIX_END]), 'used_end': cursors[ts], 'capacity': 8192 - DATA_START} for ts, payload in banks.items()]}

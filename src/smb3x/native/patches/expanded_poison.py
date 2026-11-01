# SPDX-License-Identifier: MPL-2.0
from ...planning import hazards as hazard_plan
'Production install of the exact proven note/wood/giant/BQ component only.'
from pathlib import Path
import hashlib, json
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(rom, source, base, selection):
    from ..rom import verify_base
    verify_base(source)
    original = bytes(rom)
    assembly = json.loads((ROOT / 'native/certificates/m243-poison-assembly.json').read_bytes())
    for key, name in [('source_sha256', 'native/asm/m243_poison.asm'), ('symbols_sha256', 'native/symbols/m243_symbols.json')]:
        if hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != assembly[key]:
            raise ValueError('M24.3 authored assembly binding: ' + name)
    if assembly['lookup_end'] > 49408 or assembly['giant_end'] > 50176 or assembly['new_ram'] != 0:
        raise ValueError('native allocation')
    for e in assembly['edits']:
        off = e['offset']
        before = bytes.fromhex(e['before'])
        after = bytes.fromhex(e['after'])
        if len(before) != len(after) or rom[off:off + len(before)] != before:
            raise ValueError('M24.3 native source guard: ' + e['description'])
        rom[off:off + len(after)] = after
    old = json.loads((ROOT / 'planning/data/hazards_m242.json').read_bytes())
    extra = json.loads((ROOT / 'planning/data/hazards_m243.json').read_bytes())
    legacy = vars(hazard_plan)
    areas = {c['content_id']: c for c in json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_bytes())['contents']}
    blocks = {legacy['stable_block_id'](c['content_id'], a['id'], b): (b, [dict(tileset=areas[c['content_id']]['tileset'], layout=areas[c['content_id']]['layout'])]) for c in old['contents'] if c['content_id'].startswith('smb3') for a in c['areas'] for b in a['blocks']}
    added = {b['block_id']: b for b in extra['additional_sources']}
    rows = []
    canonical = set()
    start = 16 + 51 * 8192
    if rom[start + 2047] != 0:
        raise ValueError('requires empty Poison table')
    for page in range(8, 15):
        if rom[start + page * 256:start + page * 256 + 127] != b'\xff' * 127:
            raise ValueError('table allocation guard')
    for p in selection['poison']:
        bid = p['block_id']
        if bid in canonical:
            raise ValueError('Duplicate canonical Poison chance')
        canonical.add(bid)
        if bid in added:
            b = added[bid]
            contexts = b['native_contexts']
            if p != b:
                raise ValueError('additional source identity')
        elif bid in blocks:
            b, contexts = blocks[bid]
            if any((p.get(k) != v for k, v in b.items())):
                raise ValueError('retained source identity')
        else:
            raise ValueError('Uncertified source')
        off = b['source_rom_offset']
        guard = bytes.fromhex(b['source_bytes'])
        if b.get('mandatory', True) or off in extra['protected_source_offsets'] or source[off:off + len(guard)] != guard:
            raise ValueError('resource/source guard')
        for c in contexts:
            rows.append((c['tileset'], c['layout'], b['x'] * 16, b['y'] * 16))
    if len(rows) > 127 or len(rows) != len(set(rows)):
        raise ValueError('lookup capacity/alias collision')
    rom[start + 2047] = len(rows)
    for i, (ts, layout, x, y) in enumerate(sorted(rows)):
        for page, value in [(8, ts), (9, layout & 255), (10, layout >> 8), (11, x & 255), (12, x >> 8), (13, y & 255), (14, y >> 8)]:
            rom[start + page * 256 + i] = value
    for page in range(8, 15):
        if rom[start + page * 256 + 127:start + (page + 1) * 256] != original[start + page * 256 + 127:start + (page + 1) * 256]:
            raise ValueError('Source-context tail ownership')
    if rom[start + 6144:start + 8192] != original[start + 6144:start + 8192]:
        raise ValueError('DPCM ownership')
    if rom[524304:] != original[524304:]:
        raise ValueError('Poison must not modify CHR')
    return dict(version='m243-poison-native-1', canonical_sources=len(canonical), rows=len(rows), capacity=127, new_ram=0, lookup_end=assembly['lookup_end'], giant_end=assembly['giant_end'], edits=assembly['edits'], bank_sha256=hashlib.sha256(rom[start:start + 8192]).hexdigest())

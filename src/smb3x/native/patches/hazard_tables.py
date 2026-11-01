# SPDX-License-Identifier: MPL-2.0
"""Populate only the reserved poison SoA rows after the accepted empty install."""
from pathlib import Path
import json, hashlib
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(rom, source, selection):
    areas = {c['content_id']: c for c in json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_bytes())['contents']}
    catalog = json.loads((ROOT / 'planning/data/hazards_m242.json').read_bytes())
    certified = {(c['content_id'], a['id'], b['object_index']): b for c in catalog['contents'] for a in c['areas'] for b in a['blocks']}
    placements = []
    seen = set()
    for p in selection['poison']:
        b = certified.get((p['content_id'], p['area'], p['object_index']))
        if not b or any((b[k] != p[k] for k in b)) or p['area'] != 'main' or p['mandatory']:
            raise ValueError('exact Poison source-object contract')
        a = areas[p['content_id']]
        expected = bytes.fromhex(p['source_bytes'])
        offset = p['source_rom_offset']
        if len(expected) != 3 or source[offset:offset + 3] != expected:
            raise ValueError('Poison original source bytes')
        row = (a['tileset'], a['layout'], p['x'] * 16, p['y'] * 16)
        if row in seen:
            raise ValueError('Duplicate Poison source identity')
        seen.add(row)
        placements.append(row)
    if len(placements) > 127:
        raise ValueError('Poison reserved table capacity')
    start = 16 + 51 * 8192
    if rom[start + 2047] != 0:
        raise ValueError('requires empty accepted Poison table')
    for page in range(8, 15):
        if rom[start + page * 256:start + page * 256 + 127] != b'\xff' * 127:
            raise ValueError('Poison table allocation guard')
    rom[start + 2047] = len(placements)
    for i, (tileset, layout, x, y) in enumerate(sorted(placements)):
        for page, value in ((8, tileset), (9, layout & 255), (10, layout >> 8), (11, x & 255), (12, x >> 8), (13, y & 255), (14, y >> 8)):
            rom[start + page * 256 + i] = value
    return dict(version='m242-poison-table-1', count=len(placements), capacity=127, bank=51, sha256=hashlib.sha256(rom[start:start + 8192]).hexdigest())

# SPDX-License-Identifier: MPL-2.0
from ...planning import hazards as hazard_plan
'Unchanged certified Sun-exp3 helper; production admission restricted to 2-5/40/44.'
from pathlib import Path
import hashlib, json
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(target, source, base, seed, poison, sun):
    hazards = hazard_plan.plan(seed, base['level_shuffle'], poison, sun)
    original = bytes(target)
    assembly = json.loads((ROOT / 'native/certificates/m244-sun-native.json').read_bytes())
    for name, expected in assembly['source_guards'].items():
        # Certificate keys retain their original source identities; only the
        # physical authoring directory changed. No guard or source is replaced.
        if not name.startswith('rom/') or len(Path(name).parts) != 2:
            raise ValueError('Sun certificate source path')
        path = ROOT / 'native/asm' / Path(name).name
        if hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError('Sun authored source binding')
    for e in assembly['edits']:
        before = bytes.fromhex(e['before'])
        after = bytes.fromhex(e['after'])
        offset = e['offset']
        if len(before) != len(after) or target[offset:offset + len(before)] != before:
            raise ValueError('Sun exact native guard: ' + e['reason'])
        target[offset:offset + len(after)] = after
    start = 16 + 51 * 8192
    allowed = {(p['content_id'], p['spawn_column'], p['activation_column']) for p in hazards['suns'] if p.get('camera_relative')}
    selected = []
    areas = {p['content_id']: p for p in json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_bytes())['contents']}
    for p in hazards['suns']:
        if (p['content_id'], p['spawn_column'], p['activation_column']) not in allowed:
            continue
        area = areas[p['content_id']]
        matches = [i for i in range(target[start + 4095]) if (target[start + 4096 + i], target[start + 4352 + i] + 256 * target[start + 4608 + i], target[start + 5376 + i], target[start + 4864 + i] * 256 + target[start + 5120 + i]) == (area['tileset'], area['layout'], p['spawn_column'], p['activation_column'] * 16)]
        if len(matches) != 1:
            raise ValueError('Sun research source/table identity')
        i = matches[0]
        if target[start + 5632 + i] != 1:
            raise ValueError('Original native Sun cannot be upgraded')
        target[start + 5632 + i] = 129
        selected.append(p['content_id'])
    poison_ids = {p['block_id'] for p in hazards['poison']}
    old = base['hazards']['poison']
    if len(poison_ids) != len(old):
        removed = [p for p in old if p['block_id'] not in poison_ids]
        extra = json.loads((ROOT / 'planning/data/hazards_m243.json').read_bytes())
        extra = {p['block_id']: p for p in extra['additional_sources']}
        gone = set()
        for p in removed:
            contexts = extra[p['block_id']]['native_contexts'] if p['block_id'] in extra else [dict(tileset=areas[p['content_id']]['tileset'], layout=areas[p['content_id']]['layout'])]
            gone.update(((c['tileset'], c['layout'], p['x'] * 16, p['y'] * 16) for c in contexts))
        rows = []
        for i in range(target[start + 2047]):
            values = [target[start + page * 256 + i] for page in range(8, 15)]
            if (values[0], values[1] + 256 * values[2], values[3] + 256 * values[4], values[5] + 256 * values[6]) not in gone:
                rows.append(values)
        target[start + 2047] = len(rows)
        for page in range(8, 15):
            for i in range(127):
                target[start + page * 256 + i] = rows[i][page - 8] if i < len(rows) else 255
    assert target[524304:] == original[524304:], 'No experimental CHR'
    assert target[start + 6144:start + 8192] == original[start + 6144:start + 8192], 'DPCM unchanged'
    return (hazards, dict(contract='m244-camera-sun-1', allowed=[list(v) for v in sorted(allowed)], selected=selected, native=assembly, new_ram=0, new_chr=False), dict(base['m243_hazard_extension'], canonical_sources=len(hazards['poison']), rows=target[start + 2047], bank_sha256=hashlib.sha256(target[start:start + 8192]).hexdigest()))

# SPDX-License-Identifier: MPL-2.0
"""Independent, stateless hazard decisions over explicitly certified metadata.

This module never imports random or consumes World.random. Content certification
and native allocation are separate gates; callers cannot supply arbitrary zones.
"""
import hashlib
import json
VERSION = 'm221-hazards-2'
POISON_RATES = {'off': 0, 'rare': 5, 'normal': 15, 'chaos': 35}
SUN_RATES = {'off': 0, 'rare': 5, 'normal': 15, 'chaos': 30}

def draw(seed, domain, identity):
    payload = json.dumps([VERSION, str(seed), domain, identity], ensure_ascii=True, separators=(',', ':')).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big')

def stable_block_id(content, area, block):
    return f"{content}/{area}/{block['object_index']}:{block['kind']}:{block['x']}:{block['y']}"

def validate_catalog(catalog):
    if catalog.get('version') != VERSION:
        raise ValueError('Hazard registry version')
    seen = set()
    for content in catalog['contents']:
        cid = content['content_id']
        if cid in seen:
            raise ValueError('Duplicate hazard content')
        seen.add(cid)
        areas = set()
        for area in content['areas']:
            aid = area['id']
            width = area['width']
            blocks = set()
            zones = set()
            if aid in areas or type(width) != int or (not 32 <= width <= 240):
                raise ValueError('Hazard area contract')
            areas.add(aid)
            for b in area['blocks']:
                key = stable_block_id(cid, aid, b)
                if key in blocks or b['kind'] not in ('power', 'brick_power') or b.get('mandatory', True) or (not b.get('native_certification')):
                    raise ValueError('Uncertified ordinary block')
                if any((type(b[k]) != int for k in ('object_index', 'x', 'y'))) or not 0 <= b['x'] < width or (not 1 <= b['y'] < 26):
                    raise ValueError('Block coordinates')
                blocks.add(key)
            for z in area['sun_zones']:
                if z['id'] in zones or not z.get('native_certification') or area.get('tileset') not in (1, 3, 9) or area.get('vertical', True) or area.get('autoscroll', True) or area.get('existing_sun', True):
                    raise ValueError('Uncertified Sun region')
                if any((type(z[k]) != int for k in ('spawn_column', 'activation_column'))) or not 16 <= z['spawn_column'] < z['activation_column'] < width - 24:
                    raise ValueError('Sun region coordinates')
                zones.add(z['id'])
    return catalog

def assign(seed, catalog, loaded_content_ids, poison='off', sun='off'):
    validate_catalog(catalog)
    if poison not in POISON_RATES or sun not in SUN_RATES:
        raise ValueError('Unknown hazard setting')
    requested = list(loaded_content_ids)
    if len(requested) != len(set(requested)):
        raise ValueError('Duplicate loaded content identity')
    by_id = {c['content_id']: c for c in catalog['contents']}
    result = {'version': VERSION, 'settings': {'poison_mushrooms': poison, 'angry_sun': sun}, 'nominal_percent': {'poison': POISON_RATES[poison], 'sun': SUN_RATES[sun]}, 'poison': [], 'suns': [], 'suppressed_poison': [], 'excluded_content': sorted(set(requested) - set(by_id)), 'eligible_blocks': 0, 'eligible_sun_stages': 0}
    scale = 1 << 64
    for cid in sorted(set(requested) & set(by_id)):
        content = by_id[cid]
        zones = [(a, z) for a in content['areas'] for z in a['sun_zones']]
        encounter = None
        if zones:
            result['eligible_sun_stages'] += 1
            if draw(seed, 'sun-presence', cid) * 100 < SUN_RATES[sun] * scale:
                area, zone = min(zones, key=lambda az: (draw(seed, 'sun-position', [cid, az[0]['id'], az[1]['id']]), az[1]['id']))
                encounter = {'content_id': cid, 'area': area['id'], **zone}
                result['suns'].append(encounter)
        for area in sorted(content['areas'], key=lambda a: a['id']):
            for block in sorted(area['blocks'], key=lambda b: stable_block_id(cid, area['id'], b)):
                result['eligible_blocks'] += 1
                bid = stable_block_id(cid, area['id'], block)
                if draw(seed, 'poison-block', bid) * 100 >= POISON_RATES[poison] * scale:
                    continue
                placement = {'content_id': cid, 'area': area['id'], 'block_id': bid, **block}
                if encounter and encounter['area'] == area['id'] and (abs(block['x'] - encounter['activation_column']) <= 16):
                    result['suppressed_poison'].append({'block_id': bid, 'reason': 'within one screen of seeded Sun activation'})
                else:
                    result['poison'].append(placement)
    if len(result['poison']) > 127 or len(result['suns']) > 127:
        raise ValueError('Native hazard table capacity')
    result['actual_counts'] = {'poison': len(result['poison']), 'sun': len(result['suns'])}
    result['assignment_sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result

def player_summary(manifest):
    """No stage names, block coordinates, counts or encounter positions."""
    return {'version': manifest['version'], 'settings': dict(manifest['settings']), 'description': 'Optional hazards are fixed for this seed, including deaths and retries.'}
from ..shared.resources import DATA as ROOT

def _base_plan(seed, shuffle, poison='off', sun='off'):
    raw = (ROOT / 'hazards_m242.json').read_bytes()
    catalog = json.loads(raw)
    if catalog['version'] != 'm242-hazards-1' or catalog['status'] != 'certified-for-production':
        raise ValueError('hazard certification identity')
    catalog['version'] = VERSION
    areas = (ROOT / 'original_hazard_areas_m221.json').read_bytes()
    loaded = {c['content_id'] for c in json.loads(areas)['contents']}
    loaded -= {r['original_content'] for r in shuffle['assignments']}
    loaded |= {r['assigned_content'] for r in shuffle['assignments']}
    result = assign(seed, catalog, sorted(loaded), poison, sun)
    result.update(version='m242-hazards-1', draw_version=VERSION, registry_sha256=hashlib.sha256(raw).hexdigest(), area_registry_sha256=hashlib.sha256(areas).hexdigest())
    result.pop('assignment_sha256')
    result['assignment_sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    result['sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result

def _additional_catalogue():
    raw = (ROOT / 'hazards_m243.json').read_bytes()
    data = json.loads(raw)
    if data['version'] != 'm243-hazards-1' or data['status'] != 'private-production-candidate':
        raise ValueError('hazard catalogue identity')
    if data['baseline_registry_sha256'] != hashlib.sha256((ROOT / 'hazards_m242.json').read_bytes()).hexdigest():
        raise ValueError('original40 catalogue guard')
    blocks = data['additional_sources']
    if len(blocks) != 32 or len({b['block_id'] for b in blocks}) != 32:
        raise ValueError('canonical source count')
    if any((b['mandatory'] or b['source_rom_offset'] in data['protected_source_offsets'] or len(bytes.fromhex(b['source_bytes'])) != 3 for b in blocks)):
        raise ValueError('Protected or invalid Poison source')
    return (raw, data)

def _expanded_plan(seed, shuffle, poison='off', sun='off'):
    raw, catalog = _additional_catalogue()
    result = _base_plan(seed, shuffle, poison, sun)
    loaded = {c['content_id'] for c in json.loads((ROOT / 'original_hazard_areas_m221.json').read_bytes())['contents']}
    loaded -= {r['original_content'] for r in shuffle['assignments']}
    loaded |= {r['assigned_content'] for r in shuffle['assignments']}
    eligible = [b for b in catalog['additional_sources'] if set(b['loaded_parents']) & loaded]
    for b in eligible:
        if draw(seed, 'poison-block', b['block_id']) * 100 >= POISON_RATES[poison] * (1 << 64):
            continue
        conflict = any((s['content_id'] == b['content_id'] and s['area'] == b['area'] and (abs(s['activation_column'] - b['x']) <= 16) for s in result['suns']))
        if conflict:
            result['suppressed_poison'].append(dict(block_id=b['block_id'], reason='within one screen of seeded Sun activation'))
        else:
            result['poison'].append(dict(b))
    result['eligible_blocks'] += len(eligible)
    result['actual_counts']['poison'] = len(result['poison'])
    result['excluded_content'] = sorted(set(result['excluded_content']) - {p for b in eligible for p in b['loaded_parents']})
    result.update(version='m243-hazards-1', registry_sha256=hashlib.sha256(raw).hexdigest(), baseline_registry_sha256=catalog['baseline_registry_sha256'])
    result.pop('assignment_sha256', None)
    result.pop('sha256', None)
    result['assignment_sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    result['sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result

def plan(seed, shuffle, poison='off', sun='off'):
    result = _expanded_plan(seed, shuffle, poison, sun)
    raw = result['sha256']
    camera = []
    for row in result['suns']:
        if (row['content_id'], row['spawn_column'], row['activation_column']) in {('smb3-prg1-w2-2-5', 40, 44)}:
            row['camera_relative'] = True
            camera.append(row['content_id'])
    removed = [p['block_id'] for p in result['poison'] if p['content_id'] in camera]
    result['poison'] = [p for p in result['poison'] if p['content_id'] not in camera]
    result['actual_counts']['poison'] = len(result['poison'])
    result['camera_sun'] = dict(contract='m244-camera-sun-1', parent_raw_plan_sha256=raw, suppressed_poison=removed, policy='Full-area conservative suppression only for selected certified camera contexts')
    result['sha256'] = hashlib.sha256(json.dumps({k: v for k, v in result.items() if k != 'sha256'}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result

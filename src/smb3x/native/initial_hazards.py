# SPDX-License-Identifier: MPL-2.0
"""Initial source table before certified hazard extensions are applied."""
import hashlib, json
from ..planning.hazards import assign

def plan(seed, shuffle, poison='off', sun='off', *, engineering=False):
    from pathlib import Path
    from ..shared.resources import DATA as root
    raw = (root / 'hazards_m221.json').read_bytes()
    catalog = json.loads(raw)
    if not engineering and (poison != 'off' or sun != 'off') and (catalog['status'] != 'certified-for-production'):
        raise ValueError('hazard certification pending')
    area_raw = (root / 'original_hazard_areas_m221.json').read_bytes()
    loaded = {c['content_id'] for c in json.loads(area_raw)['contents']}
    loaded -= {r['original_content'] for r in shuffle['assignments']}
    loaded |= {r['assigned_content'] for r in shuffle['assignments']}
    result = assign(seed, catalog, sorted(loaded), poison, sun)
    result['registry_sha256'] = hashlib.sha256(raw).hexdigest()
    result['area_registry_sha256'] = hashlib.sha256(area_raw).hexdigest()
    result['sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result

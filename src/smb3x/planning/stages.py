# SPDX-License-Identifier: MPL-2.0
"""Certified 53-stage permutation with mode-owned neighboring-world policy."""
from pathlib import Path
from hashlib import sha256
import json
from ..shared.resources import DATA as BASE
from .catalogue import catalogue
CATALOGUE = catalogue('m22')
from . import matching as MATCH
from . import special_stages as SPECIAL
from . import mixed_fortresses as MIXED
canonical = MATCH.canonical
VERSION = 'm31-assignment-1'
POLICY = dict(version='m222-adjacent-worlds-1', source='immutable original world', hard_world_distance=1, outlier_exclusions=[], preference='minimize self matches, then seeded pair costs; no world-distance penalty', scope='physical-world placement, not AP progression spheres')
POLICY_HASH = sha256(canonical(POLICY)).hexdigest()
RAW = (BASE / 'contents_m222.json').read_bytes()
REGISTRY = json.loads(RAW)
REGISTRY_HASH = sha256(RAW).hexdigest()
CONTENTS = {**CATALOGUE['CONTENTS'], **{c['content_id']: c for c in REGISTRY['contents']}}
CONTENTS.update({cid: {**c, 'source_family': 'smb3-prg1', 'compatibility_group': 'mixed-native-terminal', 'difficulty': 'native fortress; no calibrated difficulty rating'} for cid, c in SPECIAL.CONTENTS.items() if c['pool'] == 'fortresses'})

def pool():
    rows = sorted((c for c in REGISTRY['contents'] if c['certified']), key=lambda c: c['content_id'])
    ids = {c['content_id'] for c in rows}
    if len(ids) != len(rows) or len({c['physical_location_id'] for c in rows}) != len(rows):
        raise ValueError('Expanded pool has duplicate content/physical identities')
    for c in rows:
        if c['source_family'] != 'smb3-prg1' or c['category'] != 'normal' or c['status'] != 'certified-for-production' or (not c['secondary_graph_complete']) or c['mandatory_items'] or c['exclusions'] or (not c['evidence']) or (not 1 <= c['original_world'] <= 8) or (not c['content_graph']['nodes']) or c['content_graph']['unresolved'] or (not set(c['technical_destinations']) <= ids):
            raise ValueError('Incomplete expanded certification: ' + c['content_id'])
    if len(rows) != 53:
        raise ValueError('Expanded original pool is not yet production certified')
    return rows

def allowed_graph(rows, adjacent):
    return {d['content_id']: [c['content_id'] for c in rows if d['content_id'] in c['technical_destinations'] and (not adjacent or abs(c['original_world'] - d['original_world']) <= 1)] for d in rows}

def assignments(seed, mode='vanilla', classic_level_packs='off', classic_stage_count=0, special_stage_shuffle='off'):
    if not isinstance(seed, str) or not seed or mode not in ('vanilla', 'compatible', 'balanced'):
        raise ValueError('Unsupported SMB3X seed/shuffle mode')
    if classic_level_packs != 'off' or classic_stage_count != 0:
        raise ValueError('New SMB3X games use the certified original 53-stage catalogue')
    special = SPECIAL.plan(seed, mode, special_stage_shuffle, classic_level_packs, classic_stage_count)
    rows = pool()
    graph = allowed_graph(rows, mode == 'balanced')
    ids = [c['content_id'] for c in rows]
    mixed_contract = None
    if special_stage_shuffle == 'mixed_fortresses':
        forts = [CONTENTS[c['content_id']] for c in SPECIAL.pool('fortresses')]
        rows, mapped, mixed_contract = MIXED.assignments(seed, mode, rows, forts, MATCH)
        graph = MIXED.graph([r for r in rows if r['category'] == 'normal'], forts, mode == 'balanced')
    elif mode == 'vanilla':
        mapped = {x: x for x in ids}
    else:
        mapped = MATCH.solve(seed, ids, ids, graph, domain=[REGISTRY['version'], REGISTRY_HASH, mode, POLICY_HASH if mode == 'balanced' else None])
    if any((c not in graph[d] for d, c in mapped.items())):
        raise ValueError('Assignment violates certified technical or world-band constraints')
    if mode != 'vanilla' and all((c == d for d, c in mapped.items())):
        raise ValueError('Requested shuffle has only fixed assignments')
    by_id = {c['content_id']: c for c in rows}
    result = dict(seed=seed, mode=mode, registry_version=REGISTRY['version'], registry_sha256=REGISTRY_HASH, classic_level_packs=classic_level_packs, classic_stage_count=classic_stage_count, selected_classics=[], assignments=[dict(physical_location_id=d['physical_location_id'], physical_stage=d['stage'], original_content=d['content_id'], assigned_content=mapped[d['content_id']], compatibility_group=d['compatibility_group'], source_world=by_id[mapped[d['content_id']]]['original_world'], destination_world=d['original_world'], difficulty=by_id[mapped[d['content_id']]]['difficulty'], native_entry={k: by_id[mapped[d['content_id']]][k] for k in ('tileset', 'layout', 'objects')}) for d in rows], balanced_policy={'version': POLICY['version'], 'sha256': POLICY_HASH, 'scope': POLICY['scope']} if mode == 'balanced' else None)
    if mixed_contract is not None:
        result['mixed_completion_contract'] = mixed_contract
    result.update(version=VERSION, pool_version=REGISTRY['version'], expanded_registry_sha256=REGISTRY_HASH, matching_version=MATCH.VERSION, special_stage_shuffle=special)
    return {**result, 'sha256': sha256(canonical(result)).hexdigest()}

def validate(plan, seed):
    if not isinstance(plan, dict) or plan != assignments(seed, plan.get('mode'), plan.get('classic_level_packs'), plan.get('classic_stage_count'), plan.get('special_stage_shuffle', {}).get('setting')):
        raise ValueError('Invalid SMB3X seed/mode/registry-bound assignment')
    return plan

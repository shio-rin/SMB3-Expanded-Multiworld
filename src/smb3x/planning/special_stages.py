# SPDX-License-Identifier: MPL-2.0
"""Separate, fail-closed special pools; physical ownership is never permuted."""
from pathlib import Path
from hashlib import sha256
import json
from ..shared.resources import DATA as ROOT
from . import matching as MATCH
canonical = MATCH.canonical
RAW = (ROOT / 'special_contents_m222.json').read_bytes()
REGISTRY = json.loads(RAW)
REGISTRY_HASH = sha256(RAW).hexdigest()
CONTENTS = {r['content_id']: r for r in REGISTRY['candidates']}
VERSION = 'm222-special-assignment-1'
POLICY = dict(version='m222-special-policy-1', balanced='same or immediately adjacent immutable source world; no calibrated special-stage difficulty claim', compatible='all technically certified pairs within each type', preference='minimize unchanged gameplay descriptors, then seeded cost; identities allowed for feasibility', streams=['fortresses', 'bros', 'military'], coin_ship='genuine native transformation overrides assigned battle for that visit; physical identity retained', mixed='explicitly gated combined ordinary/fortress contract; independent Bros/military streams retained')

def graph(rows, balanced):
    return {d['content_id']: [c['content_id'] for c in rows if d['content_id'] in c['technical_destinations'] and (not balanced or abs(c['original_world'] - d['original_world']) <= 1)] for d in rows}

def pool(kind):
    rows = sorted((r for r in CONTENTS.values() if r['pool'] == kind and r['certified']), key=lambda r: r['content_id'])
    ids = {r['content_id'] for r in rows}
    if len(rows) < 2 or len(ids) != len(rows) or len({r['physical_location_id'] for r in rows}) != len(rows):
        raise ValueError('Special pool not production certified: ' + kind)
    for r in rows:
        if r['status'] != 'certified-for-production' or not r['evidence'] or r['content_graph']['unresolved'] or (not r['technical_destinations']) or (not set(r['technical_destinations']) <= ids) or (not r.get('completion_contract')) or (not r.get('secondary_graph_complete')):
            raise ValueError('Incomplete special content certification: ' + r['content_id'])
    if len({r['gameplay_fingerprint'] for r in rows}) < 2:
        raise ValueError('Special pool has no distinct gameplay: ' + kind)
    return rows

def plan(seed, main_mode, setting='off', classic_level_packs='off', classic_stage_count=0):
    if not isinstance(seed, str) or not seed or main_mode not in ('vanilla', 'compatible', 'balanced'):
        raise ValueError('Invalid special shuffle seed/main mode')
    if setting not in ('off', 'by_type', 'mixed_fortresses'):
        raise ValueError('Unknown special_stage_shuffle')
    if setting != 'off' and main_mode == 'vanilla':
        raise ValueError('Vanilla main shuffle requires special_stage_shuffle=off')
    if setting != 'off' and (classic_level_packs != 'off' or classic_stage_count != 0):
        raise ValueError('Special shuffling requires Classics Off and count0')
    if setting == 'mixed_fortresses':
        contract = json.loads((ROOT / 'mixed_m222.json').read_text())
        if contract['status'] != 'certified-for-production':
            raise ValueError('Mixed fortresses has an isolated two-way proof, but generalized production certification is pending')
    plans = {}
    if setting != 'off':
        for kind in ('bros', 'military') if setting == 'mixed_fortresses' else ('fortresses', 'bros', 'military'):
            rows = pool(kind)
            ids = [r['content_id'] for r in rows]
            allowed = graph(rows, main_mode == 'balanced')
            equivalence = {r['content_id']: r['gameplay_fingerprint'] for r in rows}
            mapped = MATCH.solve(seed, ids, ids, allowed, domain=[VERSION, REGISTRY['version'], REGISTRY_HASH, kind, main_mode, POLICY], equivalence=equivalence)
            if all((equivalence[d] == equivalence[c] for d, c in mapped.items())):
                raise ValueError('Special pool has only identity-equivalent assignments under this policy: ' + kind)
            by_id = {r['content_id']: r for r in rows}
            plans[kind] = [dict(physical_location_id=d['physical_location_id'], original_content=d['content_id'], assigned_content=mapped[d['content_id']], source_world=by_id[mapped[d['content_id']]]['original_world'], destination_world=d['original_world'], native_entry={k: by_id[mapped[d['content_id']]][k] for k in ('tileset', 'layout', 'objects')}) for d in rows]
    result = dict(version=VERSION, setting=setting, main_mode=main_mode, registry_version=REGISTRY['version'], registry_sha256=REGISTRY_HASH, completion_contract_version=REGISTRY['completion_contract_version'], policy=POLICY, pools=plans)
    return {**result, 'sha256': sha256(canonical(result)).hexdigest()}

def validate(value, seed, main_mode, classic_level_packs='off', classic_stage_count=0):
    if not isinstance(value, dict) or value != plan(seed, main_mode, value.get('setting'), classic_level_packs, classic_stage_count):
        raise ValueError('Wrong special pool/policy/terminal/assignment identity')
    return value

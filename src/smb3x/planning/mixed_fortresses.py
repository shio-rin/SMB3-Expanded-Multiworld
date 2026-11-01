# SPDX-License-Identifier: MPL-2.0
"""Combined matching, bounded by explicit native terminal certification."""
from pathlib import Path
from hashlib import sha256
import json
from ..shared.resources import DATA as ROOT
RAW = (ROOT / 'mixed_m222.json').read_bytes()
CONTRACT = json.loads(RAW)
CONTRACT_HASH = sha256(RAW).hexdigest()

def graph(ordinary, fortresses, adjacent):
    cross = {r['content_id'] for r in CONTRACT['ordinary_donors'] if r['cross_type_candidate']}
    rows = ordinary + fortresses
    fort_ids = {r['content_id'] for r in fortresses}
    return {d['content_id']: [c['content_id'] for c in rows if (not adjacent or abs(c['original_world'] - d['original_world']) <= 1) and (d['content_id'] in fort_ids and c['content_id'] not in fort_ids and (c['content_id'] in cross) or (d['content_id'] not in fort_ids and c['content_id'] in fort_ids) or d['content_id'] in c['technical_destinations'])] for d in rows}

def assignments(seed, mode, ordinary, fortresses, match):
    if CONTRACT['status'] != 'certified-for-production':
        raise ValueError('Mixed fortresses has an isolated two-way proof, but generalized production certification is pending')
    rows = ordinary + fortresses
    ids = [r['content_id'] for r in rows]
    allowed = graph(ordinary, fortresses, mode == 'balanced')
    mapping = match.solve(seed, ids, ids, allowed, domain=['m222-combined-matching-1', CONTRACT_HASH, mode])
    return (rows, mapping, dict(version=CONTRACT['version'], sha256=CONTRACT_HASH, scope='Explicit single-main-card donors may enter fortress hosts; other ordinary donors remain in ordinary hosts; admitted fortress graphs may enter either type', cards='Native source card/score/life effects retained; no fabricated boss credit', rng='Combined ordinary/fortress plan intentionally differs from by_type; Bros/military streams unchanged'))

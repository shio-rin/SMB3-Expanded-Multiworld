# SPDX-License-Identifier: MPL-2.0
"""Experimental special-scene extension. Never imported by production generation."""
from pathlib import Path
import json, hashlib
from ..shared.resources import DATA as ROOT
from . import palettes as P
from . import palette_library as LIB
VERSION = 'm24-special-palettes-2'
AUDIT = json.loads((ROOT / 'special_palette_areas_m24.json').read_text())
ADAPTED = [dict(id='special-toad-ember', name='Ember Keep Â· Lantern Interior', parent='fortress-ember', kind='atmospheric', background=[15, 15, 48, 60, 15, 23, 39, 55, 15, 39, 48, 23, 15, 18, 49, 33]), dict(id='special-toad-indigo', name='Haunted Indigo Â· Evening Interior', parent='fortress-indigo', kind='atmospheric', background=[15, 15, 48, 60, 15, 18, 34, 50, 15, 39, 48, 23, 15, 18, 49, 33]), dict(id='special-toad-moss', name='Ancient Moss Â· Woodland Interior', parent='fortress-moss', kind='unusual', background=[15, 15, 48, 60, 15, 27, 43, 59, 15, 39, 48, 23, 15, 18, 49, 33]), dict(id='special-airship-sunset', name='Sunset Â· Airship', parent='plains-sunset', kind='atmospheric', background=[38, 15, 48, 60, 38, 15, 54, 39, 38, 15, 48, 16, 38, 15, 39, 23]), dict(id='special-airship-dusk', name='Dusk Â· Airship', parent='plains-dusk', kind='atmospheric', background=[4, 15, 48, 60, 4, 15, 52, 20, 4, 15, 48, 16, 4, 15, 39, 23])]
BY_ID = {t['id']: t for t in P.corrected(LIB.THEMES) + ADAPTED}

def eligible(row):
    cat = row['category']
    ts = row['tileset']
    if cat == 'house':
        return [t['id'] for t in ADAPTED if t['id'].startswith('special-toad')]
    if cat == 'airship-deck':
        return ['special-airship-sunset', 'special-airship-dusk', 'military-ashfall', 'military-steel', 'military-crimson']
    if cat == 'airship-boss':
        return ['fortress-indigo', 'fortress-ember', 'military-crimson', 'fortress-moss']
    if cat == 'bros':
        if ts == 9:
            return ['plains-midnight', 'plains-dusk', 'plains-storm']
        if ts == 1:
            return ['plains-midnight', 'plains-sunset', 'plains-dusk', 'plains-peach-dawn', 'plains-storm', 'plains-candy']
        if ts in (3, 11):
            return ['hills-autumn', 'hills-spring', 'hills-lavender', 'hills-misty-teal', 'plains-midnight', 'plains-dusk']
        if ts == 12:
            return ['ice-arctic-dawn', 'ice-blue-night', 'ice-aurora']
        if ts == 13:
            return ['sky-golden', 'sky-thunder', 'sky-violet', 'plains-midnight']
    return []

def rank(seed, domain, value):
    return int(LIB.fingerprint([VERSION, str(seed), domain, value]), 16)

def plan(seed, mode='atmospheric', force=None):
    base = P.plan(seed, mode)
    usage = {}
    rows = []
    for r in AUDIT['rows']:
        pool = eligible(r)
        if mode == 'atmospheric':
            pool = [x for x in pool if BY_ID[x].get('kind', 'atmospheric') == 'atmospheric']
        if not pool:
            continue
        chosen = None
        if mode != 'original':
            if force is not None:
                chosen = force if force in pool else None
            elif rank(seed, 'original', r['id']) % 100 >= 20:
                unusual = rank(seed, 'class', r['id']) % 80 >= 55
                subset = [x for x in pool if (BY_ID[x].get('kind', 'atmospheric') == 'unusual') == unusual] or pool
                chosen = min(subset, key=lambda x: (usage.get(x, 0), rank(seed, 'theme', [r['id'], x])))
                usage[chosen] = usage.get(chosen, 0) + 1
        rows.append(dict(id=r['id'], tileset=r['tileset'], layout=r['layout'], symbol=r['symbol'], category=r['category'], eligible=pool, theme=chosen))
    return dict(version=VERSION, mode=mode, base=base, areas=rows, force_review_theme=force, sha256=LIB.fingerprint([VERSION, base['sha256'], rows]), selection_counts=usage, identity='loaded area, shared across hosts and visits; separate cosmetic hash domain; old M24 selections exact')

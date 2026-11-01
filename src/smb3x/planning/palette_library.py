# SPDX-License-Identifier: MPL-2.0
"""Opt-in cosmetics. No calls to World.random or progression allocators."""
from pathlib import Path
import hashlib
import json
from ..shared.resources import DATA as ROOT
VERSION = 'm24-curated-2'
LIBRARY = json.loads((ROOT / 'palettes_m24.json').read_text())
NEW = LIBRARY['themes']
ACCEPTED = json.loads((ROOT / 'palettes_m20.json').read_text())[1:]
THEMES = ACCEPTED + NEW
BY_ID = {t['id']: t for t in THEMES}
ORDINARY = json.loads((ROOT / 'contents_m222.json').read_text())['contents']
SPECIAL = [c for c in json.loads((ROOT / 'special_contents_m222.json').read_text())['candidates'] if c['pool'] in ('fortresses', 'military')]
EXCLUDED_AREAS = {'12:ab97:08': 'Native fallback: 7-1 vertical-pipe secondary renders and restores its parent palette, but the assisted return/death fixture remains incomplete in both baseline and themed runs', '0d:b470:0e': 'Native fallback: World6 shared Big Question room entry renders, but its assisted return fixture dies in both baseline and themed runs; no independent selection certified'}

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def rank(seed, domain, value):
    return int(fingerprint([VERSION, str(seed), domain, value]), 16)

def family(ts, palette, scope='normal'):
    if ts == 2 or scope == 'fortresses':
        return 'fortress'
    if ts == 10:
        return 'military'
    if ts in (8, 14):
        return 'underground'
    if ts == 6:
        return 'water'
    if ts == 9:
        return 'underground' if palette in (2, 3, 6) else 'desert'
    if ts == 12:
        return 'ice' if palette == 0 else 'fortress' if scope == 'fortresses' else 'underground'
    if ts in (4, 13):
        return 'sky'
    if ts in (3, 11):
        return 'underground' if palette in (3, 4, 5, 6, 7) else 'hills'
    if ts == 1:
        return 'underground' if palette in (5, 7) else 'plains'
    return None

def areas():
    resolved = {}
    for c in ORDINARY + SPECIAL:
        for i, n in enumerate(c['content_graph']['nodes']):
            h = n['header']
            ts = n['tileset']
            aid = f"{h['bank']:02x}:{n['layout']:04x}:{ts:02x}"
            f = family(ts, h['background_palette'], c.get('pool', 'normal') if i == 0 else 'normal')
            if aid in EXCLUDED_AREAS:
                f = None
            row = dict(id=aid, tileset=ts, layout=n['layout'], objects=n['objects'], bank=h['bank'], symbol=h['symbol'], palette=h['background_palette'], family=f, secondary=bool(i), parents=[], contents=[], header_sha256=h['header_sha256'], source=h['source'], fallback_reason=None if f else EXCLUDED_AREAS.get(aid, 'protected native bonus/Toad/event tileset'), big_question_policy='separate immutable native parent-to-resolved-room lookup; ambiguous parents native')
            if aid in resolved:
                old = resolved[aid]
                if any((old[k] != row[k] for k in ('tileset', 'layout', 'palette', 'header_sha256', 'family'))):
                    raise ValueError('Shared palette identity conflict ' + aid)
                old['secondary'] &= bool(i)
            else:
                resolved[aid] = row
            row = resolved[aid]
            row['contents'] = sorted(set(row['contents'] + [c['content_id']]))
            if i:
                main = c['content_graph']['nodes'][0]
                mh = main['header']
                row['parents'] = sorted(set(row['parents'] + [f"{mh['bank']:02x}:{main['layout']:04x}:{main['tileset']:02x}"]))
    if len(resolved) > 255:
        raise ValueError('unsigned area table capacity exceeded')
    return [resolved[k] for k in sorted(resolved)]

def bq_bindings():
    result = {}
    for c in ORDINARY + SPECIAL:
        nodes = {n['id']: n for n in c['content_graph']['nodes']}
        for e in c['content_graph']['edges']:
            if e['kind'] != 'big-question-potential':
                continue
            if e['source'] not in nodes or e['target'] not in nodes:
                continue

            def aid(key):
                n = nodes[key]
                return f"{n['header']['bank']:02x}:{n['layout']:04x}:{n['tileset']:02x}"
            parent, target = (aid(e['source']), aid(e['target']))
            if parent in result and result[parent] != target:
                result[parent] = None
            else:
                result[parent] = target
    return result

def eligible(area):
    result = [t['id'] for t in NEW if t['scope'] == 'stage' and t['family'] == area['family']]
    if not area['secondary']:
        if area['tileset'] == 1 and area['palette'] in (0, 3):
            result += ['plains-midnight', 'plains-sunset', 'plains-dusk']
        if area['tileset'] == 3 and area['palette'] == 0:
            result += ['hills-autumn']
    return sorted(result)

def plan(seed, *, original_percent=20, theme_subset=None, force_theme=None):
    if type(original_percent) is not int or not 0 <= original_percent <= 100:
        raise ValueError('original_percent must be 0..100')
    if theme_subset is not None and (not isinstance(theme_subset, list) or len(theme_subset) != len(set(theme_subset)) or (not set(theme_subset) <= set(BY_ID))):
        raise ValueError('Unknown/duplicate themes')
    if force_theme is not None and force_theme not in BY_ID:
        raise ValueError('Unknown review theme')
    rows = areas()
    usage = {}
    assignments = []

    def pick(a, pool):
        pool = [x for x in pool if theme_subset is None or x in theme_subset]
        if force_theme:
            return force_theme if force_theme in pool else None
        if not pool or rank(seed, 'original', a) % 100 < original_percent:
            return None
        unusual = rank(seed, 'class', a) % 80 >= 55
        subset = [x for x in pool if (BY_ID[x].get('kind', 'atmospheric') == 'unusual') == unusual]
        subset = subset or pool
        selected = min(subset, key=lambda x: (usage.get(x, 0), rank(seed, 'theme', [a, x])))
        usage[selected] = usage.get(selected, 0) + 1
        return selected
    for a in rows:
        pool = eligible(a)
        chosen = pick(a['id'], pool)
        assignments.append({**a, 'eligible': pool, 'theme': chosen, 'technical_status': 'native validation pending', 'human_approval': 'pending' if chosen else 'native'})
    maps = {str(w): pick('map:' + str(w), sorted([t['id'] for t in NEW if t['scope'] == 'map' and w in t['worlds']] + (['map-midnight'] if w == 1 else []))) for w in range(1, 9)}
    result = dict(version=VERSION, cosmetic_seed=str(seed), original_percent=original_percent, theme_subset=theme_subset, review_force_theme=force_theme, library_sha256=hashlib.sha256((ROOT / 'palettes_m24.json').read_bytes()).hexdigest(), accepted_library_sha256=hashlib.sha256((ROOT / 'palettes_m20.json').read_bytes()).hexdigest(), areas=assignments, map_themes=maps, selection_counts=usage, big_question_bindings=bq_bindings(), secondary_policy='independent resolved area identity; shared rooms have one immutable assignment; unknown/forced areas native')
    result['sha256'] = fingerprint(result)
    return result

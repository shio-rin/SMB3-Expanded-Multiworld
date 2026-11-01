# SPDX-License-Identifier: MPL-2.0
"""Deterministic, progression-independent soundtrack and theme planning."""

from pathlib import Path
import hashlib
import json
import math


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()


from ..shared.resources import DATA as ROOT
from .catalogue import catalogue

CONTENT = catalogue('m19')['CONTENTS']
THEMES = json.loads((ROOT / 'palettes_m20.json').read_text())[1:]
PRIMARY = json.loads((ROOT / 'music_primary_m20.json').read_text())
PRIMARY_IDS = {r['content'] for r in PRIMARY['rows']}
DEFAULTS = {
    'music_policy': 'vanilla',
    'original_music_percent': 33,
    'custom_track_budget': 8,
    'music_families': ['local'],
    'secondary_music': 'independent',
    'level_palette_style': 'vanilla',
    'overworld_palette_style': 'vanilla',
    'themes': [t['id'] for t in THEMES],
}


def validate(settings=None):
    result = {**DEFAULTS, **(settings or {})}
    if set(result) != set(DEFAULTS):
        raise ValueError('Unknown audiovisual option')
    for key, allowed in {
        'music_policy': ('vanilla', 'contextual', 'mixed', 'anything_goes'),
        'secondary_music': ('inherit', 'independent'),
        'level_palette_style': ('vanilla', 'constrained', 'themed'),
        'overworld_palette_style': ('vanilla', 'constrained', 'themed'),
    }.items():
        if result[key] not in allowed:
            raise ValueError('Unsupported ' + key)
    if (
        type(result['original_music_percent']) is not int
        or not 25 <= result['original_music_percent'] <= 75
    ):
        raise ValueError('original_music_percent must be 25..75')
    if (
        type(result['custom_track_budget']) is not int
        or not 0 <= result['custom_track_budget'] <= 16
    ):
        raise ValueError('custom_track_budget must be 0 (automatic)..16')
    for key, allowed in [
        ('music_families', {'local', 'mario-classics', 'nes-classics', 'development'}),
        ('themes', {t['id'] for t in THEMES}),
    ]:
        value = result[key]
        if (
            not isinstance(value, list)
            or any((not isinstance(x, str) for x in value))
            or len(value) != len(set(value))
            or (not set(value) <= allowed)
        ):
            raise ValueError('Unsupported/duplicate ' + key)
    return result


def rank(seed, domain, value):
    return int(fingerprint(['m20-av-1', str(seed), domain, value]), 16)


def certified_palette_areas(shuffle, cosmetics=None):
    used = {
        r['content_id']
        for r in CONTENT.values()
        if r.get('category') == 'normal' and (not r['content_id'].startswith('classic/'))
    }
    used -= set((row['original_content'] for row in shuffle['assignments']))
    used.update((row['assigned_content'] for row in shuffle['assignments']))
    resolved = {}
    excluded = []
    for key in sorted(used):
        content = CONTENT[key]
        if not content.get('certified') and key not in PRIMARY_IDS:
            excluded.append(
                {'content': key, 'reason': 'outside certified content/secondary lifecycle set'}
            )
            continue
        if key.startswith('classic/'):
            headers = [
                {
                    'address': content['layout'],
                    'bank': 16,
                    'symbol': key,
                    'music': 0,
                    'background_palette': 0,
                    'graphics_index': 25,
                    'width_screens': 15,
                }
            ]
        else:
            headers = (
                content['potential_header_closure']
                if content.get('certified')
                else [content['main_header']]
            )
            if not content.get('certified') and len(content['potential_header_closure']) > 1:
                excluded.append(
                    {
                        'content': key,
                        'reason': 'primary-only music certification; secondary retains native selection',
                    }
                )
        for index, header in enumerate(headers):
            secondary = index > 0
            tileset = (
                content['tileset'] if not secondary else content['main_header']['alternate_tileset']
            )
            if header['music'] not in (0, 1, 2, 8):
                excluded.append(
                    {
                        'content': key,
                        'area': header['symbol'],
                        'reason': 'protected native music profile',
                    }
                )
                continue
            category = (
                'underground'
                if header['music'] == 1
                else (
                    'water'
                    if header['music'] == 2
                    else {
                        1: 'plains',
                        3: 'plains',
                        4: 'athletic',
                        6: 'water',
                        9: 'desert',
                        11: 'plains',
                        12: 'ice',
                        13: 'athletic',
                        14: 'underground',
                    }[tileset]
                )
            )
            area_id = f"{header['bank']:02x}:{header['address']:04x}:{tileset:02x}"
            main = headers[0]
            parent = f"{main['bank']:02x}:{main['address']:04x}:{content['tileset']:02x}"
            row = {
                'id': area_id,
                'content': key,
                'parents': [parent] if secondary else [],
                'symbol': header['symbol'],
                'tileset': tileset,
                'bank': header['bank'],
                'layout': header['address'],
                'category': category,
                'native_music': {0: 16, 1: 32, 2: 48, 8: 144}[header['music']],
                'secondary': secondary,
                'weight': 1 if secondary else 4,
                'palette': header['background_palette'],
                'graphics': header['graphics_index'],
                'width': header['width_screens'],
            }
            original_choice = (cosmetics or {}).get('level_music', {}).get(header['symbol'])
            if original_choice is not None:
                row['native_music'] = {0: 16, 1: 32, 2: 48, 8: 144}[original_choice]
            if area_id in resolved:
                old = resolved[area_id]
                if (old['category'], old['native_music']) != (category, row['native_music']):
                    raise ValueError('Conflicting shared area metadata')
                old['weight'] = max(old['weight'], row['weight'])
                old['parents'] = sorted(set(old['parents'] + row['parents']))
            else:
                resolved[area_id] = row
    return (list(resolved.values()), excluded)


def allocate(seed, resolved, excluded, pack=None, settings=None):
    """Return the deterministic audio/palette plan and selected scores, in slot order.

    Rank domains and iteration order are part of seed determinism. No global RNG
    is consumed, including for native-only music.
    """
    config = validate(settings)
    candidates = (
        []
        if pack is None or config['music_policy'] == 'vanilla'
        else [t for t in pack['tracks'] if t['family'] in config['music_families']]
    )

    def compatible(track, area):
        return config['music_policy'] != 'contextual' or area['category'] in track['contexts']

    demand = {}
    for area in resolved:
        if area['secondary'] and config['secondary_music'] == 'inherit':
            continue
        demand[area['category']] = demand.get(area['category'], 0) + area['weight']
    selected = []
    melodies = {}
    allocation = []
    budget = config['custom_track_budget'] or min(8, len(candidates))
    # Prefer uncovered demand, then the stable seed rank; repeated melodies cost more.
    while len(selected) < budget:
        best = None
        for t in candidates:
            if t in selected:
                continue
            marginal = 0
            for category, count in demand.items():
                area = {'category': category}
                if compatible(t, area):
                    present = sum((compatible(s, area) for s in selected))
                    affinity = (
                        2 if config['music_policy'] == 'mixed' and category in t['contexts'] else 1
                    )
                    marginal += affinity * math.isqrt(count * 1048576) // (1 + present)
            if not marginal:
                continue
            score = (
                marginal // (1 + melodies.get(t['melody'], 0)),
                rank(seed, 'song-selection', t['id']),
            )
            if best is None or score > best[0]:
                best = (score, t)
        if best is None:
            break
        t = best[1]
        selected.append(t)
        melodies[t['melody']] = melodies.get(t['melody'], 0) + 1
        allocation.append(
            {
                'track': t['id'],
                'marginal_score': best[0][0],
                'bank_bytes': t['storage_bytes'],
                'sequence_bytes': t['sequence_bytes'],
            }
        )
    selected.sort(key=lambda t: t['id'])
    music = []
    palettes = []
    for area in resolved:
        pool = [t for t in selected if compatible(t, area)]
        if config['music_policy'] == 'mixed':
            pool += [t for t in selected if area['category'] in t['contexts']]
        wants_custom = (
            rank(seed, 'original-or-custom', area['id']) % 100 >= config['original_music_percent']
        )
        inherited = area['secondary'] and config['secondary_music'] == 'inherit'
        chosen = None
        if config['music_policy'] != 'vanilla' and wants_custom and pool and (not inherited):
            chosen = pool[rank(seed, 'area-track', area['id']) % len(pool)]
        if not wants_custom:
            reason = 'selected-original'
        elif not pool:
            reason = 'no-compatible-custom'
        else:
            reason = 'selected-custom'
        if config['music_policy'] == 'vanilla':
            reason = 'vanilla-policy'
        if inherited:
            reason = 'inherit-pending'
        music.append(
            {
                **area,
                'track': None if chosen is None else chosen['id'],
                'selector': (
                    area['native_music'] if chosen is None else 208 + selected.index(chosen)
                ),
                'custom': chosen is not None,
                'reason': reason,
            }
        )
        eligible = []
        if not area['secondary'] and area['palette'] in (0, 3) and (area['tileset'] == 1):
            eligible = [t for t in THEMES if t['tilesets'] == [1]]
        if not area['secondary'] and area['palette'] == 0 and (area['tileset'] == 3):
            eligible = [t for t in THEMES if t['tilesets'] == [3]]
        eligible = [t for t in eligible if t['id'] in config['themes']]
        chosen_theme = (
            eligible[rank(seed, 'level-theme', area['id']) % len(eligible)]
            if eligible and config['level_palette_style'] == 'themed'
            else None
        )
        palettes.append(
            {
                'area': area['id'],
                'theme': chosen_theme['id'] if chosen_theme else None,
                'human_approval': False,
            }
        )
    by_id = {area['id']: area for area in music}
    for area in music:
        if area['reason'] != 'inherit-pending':
            continue
        parents = [by_id[p] for p in area['parents'] if p in by_id]
        if parents and len({p['selector'] for p in parents}) == 1:
            area.update(
                selector=parents[0]['selector'],
                track=parents[0]['track'],
                custom=parents[0]['custom'],
                reason='inherited-parent',
            )
        else:
            area['reason'] = 'shared-parent-conflict-native-fallback'
    result = {
        'version': 'm20-av-1',
        'settings': config,
        'pack_sha256': pack['sha256'] if pack else None,
        'palette_pack_sha256': hashlib.sha256(
            (ROOT / 'palettes_m20.json').read_bytes()
        ).hexdigest(),
        'primary_registry_sha256': hashlib.sha256(
            (ROOT / 'music_primary_m20.json').read_bytes()
        ).hexdigest(),
        'selected_tracks': [
            {
                'id': t['id'],
                'selector': 208 + i,
                'bank': 32 + i,
                'conversion': t['conversion'],
                'provenance': t['provenance'],
            }
            for i, t in enumerate(selected)
        ],
        'allocation_order': allocation,
        'weighted_category_counts': demand,
        'category_pools': {
            category: [t['id'] for t in selected if compatible(t, {'category': category})]
            for category in demand
        },
        'music': music,
        'palettes': palettes,
        'excluded': excluded,
        'map_themes': (
            {'1': 'map-midnight'}
            if config['overworld_palette_style'] == 'themed' and 'map-midnight' in config['themes']
            else {}
        ),
        'storage_bytes': sum((t['storage_bytes'] for t in selected)),
        'selection_budget': {
            'requested': config['custom_track_budget'],
            'effective_limit': budget,
            'selected': len(selected),
            'reduction_reason': (
                'insufficient eligible distinct tracks' if len(selected) < budget else None
            ),
        },
        'family_availability': {
            family: sum((t['family'] == family for t in candidates))
            for family in config['music_families']
        },
        'primary_certification': PRIMARY['version'],
        'policy_scope': 'source-audited ordinary primaries and five certified reciprocal secondary chains; event and map music protected',
    }
    result['sha256'] = fingerprint(result)
    return (result, [t['score'] for t in selected])

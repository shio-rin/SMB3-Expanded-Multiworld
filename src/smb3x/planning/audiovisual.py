# SPDX-License-Identifier: MPL-2.0
"""Original-area native music and conservative palettes for expanded relocation.

Only the certified original catalogue is used for new games.
No new custom-music lifecycle or palette certification is inferred here.
"""
from pathlib import Path
from . import audio_allocation as allocation
from . import stages
validate = allocation.validate
fingerprint = allocation.fingerprint
THEMES = allocation.THEMES
CONTENT = stages.CONTENTS

def areas(shuffle, cosmetics=None):
    used = {r['content_id'] for r in stages.REGISTRY['contents']}
    used.difference_update((r['original_content'] for r in shuffle['assignments']))
    used.update((r['assigned_content'] for r in shuffle['assignments']))
    resolved = {}
    excluded = []
    for cid in sorted(used):
        c = CONTENT[cid]
        if c['source_family'] != 'smb3-prg1':
            raise ValueError('Expanded audiovisual context is original-only')
        main = c['content_graph']['nodes'][0]
        parent = f"{main['header']['bank']:02x}:{main['layout']:04x}:{main['tileset']:02x}"
        for index, a in enumerate(c['content_graph']['nodes']):
            h = a['header']
            ts = a['tileset']
            if h['music'] not in (0, 1, 2, 8):
                excluded.append(dict(content=cid, area=a['id'], reason='protected native soundtrack; no override'))
                continue
            aid = f"{h['bank']:02x}:{a['layout']:04x}:{ts:02x}"
            category = 'underground' if h['music'] == 1 else 'water' if h['music'] == 2 else {1: 'plains', 3: 'plains', 4: 'athletic', 6: 'water', 8: 'underground', 9: 'desert', 11: 'plains', 12: 'ice', 13: 'athletic', 14: 'underground'}[ts]
            row = dict(id=aid, content=cid, parents=[parent] if index else [], symbol=h['symbol'], tileset=ts, bank=h['bank'], layout=a['layout'], category=category, native_music={0: 16, 1: 32, 2: 48, 8: 144}[h['music']], secondary=bool(index), weight=1 if index else 4, palette=h['background_palette'], graphics=h['graphics_index'], width=h['width_screens'])
            choice = (cosmetics or {}).get('level_music', {}).get(h['symbol'])
            if choice is not None:
                row['native_music'] = {0: 16, 1: 32, 2: 48, 8: 144}[choice]
            if aid in resolved:
                old = resolved[aid]
                if any((old[k] != row[k] for k in ('tileset', 'bank', 'layout', 'category', 'native_music', 'palette', 'graphics'))):
                    raise ValueError('Conflicting shared native area: ' + aid)
                old['parents'] = sorted(set(old['parents'] + row['parents']))
                old['weight'] = max(old['weight'], row['weight'])
            else:
                resolved[aid] = row
    if len(resolved) > 127:
        raise ValueError('Expanded native area lookup exceeds audited127-row capacity')
    return ([resolved[k] for k in sorted(resolved)], excluded)

def plan(seed, shuffle, pack=None, settings=None, cosmetics=None):
    config = validate(settings)
    if shuffle.get('special_stage_shuffle', {}).get('setting', 'off') != 'off':
        if pack is not None or config['music_policy'] != 'vanilla' or config['secondary_music'] != 'independent':
            raise ValueError('Special shuffling requires native music, no custom pack and independent native secondary tracks')
    if pack is not None or config['music_policy'] != 'vanilla' or config['secondary_music'] != 'independent':
        raise ValueError('Expanded original audiovisual certification requires native level/map music, no custom pack, and secondary_music=independent')
    result, songs = allocation.allocate(seed, *areas(shuffle, cosmetics), pack=None, settings=config)
    approved = {a['id'] for a in allocation.certified_palette_areas({'assignments': []}, cosmetics)[0] if not a['secondary']}
    for row in result['palettes']:
        if row['area'] not in approved:
            row['theme'] = None
            row['fallback_reason'] = 'Expanded environment retains native palette; no new theme certification inferred'
    result.update(version='m23-native-av-1', original_registry_sha256=stages.REGISTRY_HASH, policy_scope='loaded original area/header identity; independent native secondary tracks; accepted themed areas only')
    result.pop('sha256')
    result['sha256'] = fingerprint(result)
    return (result, songs)

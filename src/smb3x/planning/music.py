# SPDX-License-Identifier: MPL-2.0
"""Original-music selection and an explicitly bound optional private provider."""
from pathlib import Path
import hashlib, json
from ..shared.resources import DATA as ROOT
from collections.abc import Mapping
PRIVATE_PROVIDER_ENABLED = False
PRIVATE_UNAVAILABLE = 'Custom music is unavailable in this public build; use Vanilla or Shuffled original music. A separately versioned private build is required.'

class _PrivateCatalogue(Mapping):
    """Only an explicitly bound private build may supply catalogue metadata.

    Both files are immutable recipe resources in that flavor. Public builds
    include neither; native music never opens them. The existing player-file
    resource identity and custom plan catalogue identity bind host and player.
    """

    def __init__(self):
        self._value = None

    def available(self):
        return PRIVATE_PROVIDER_ENABLED and (ROOT / 'private_music_provider.json').is_file()

    def _load(self):
        if not PRIVATE_PROVIDER_ENABLED:
            raise ValueError(PRIVATE_UNAVAILABLE)
        if self._value is None:
            try:
                binding = json.loads((ROOT / 'private_music_provider.json').read_bytes())
                raw = (ROOT / 'music_catalogue_m244.json').read_bytes()
            except FileNotFoundError as exc:
                raise ValueError(PRIVATE_UNAVAILABLE) from exc
            if binding.get('format') != 'smb3x-private-music-provider-1' or hashlib.sha256(raw).hexdigest() != binding.get('catalogue_sha256'):
                raise ValueError('Private music provider integrity mismatch')
            self._value = json.loads(raw)
        return self._value

    def __getitem__(self, key):
        return self._load()[key]

    def __iter__(self):
        return iter(self._load())

    def __len__(self):
        return len(self._load())
CATALOGUE = _PrivateCatalogue()
from . import audiovisual as AV
VERSION = 'm244-r3-selection-1'
MODES = ('vanilla', 'shuffled', 'custom_mixed', 'custom_only')

def fingerprint(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def rank(seed, domain, v):
    return int(fingerprint([VERSION, str(seed), domain, v]), 16)

def plan(seed, shuffle, cosmetics, mode='vanilla', reserves=False, tracks=()):
    if mode not in MODES or type(reserves) is not bool:
        raise ValueError('Unsupported music mode/reserves')
    if not isinstance(tracks, (list, tuple)) or any((not isinstance(x, str) for x in tracks)) or len(set(tracks)) != len(tracks) or (len(tracks) > 16):
        raise ValueError('At most 16 distinct requested music tracks')
    tracks = sorted(tracks)
    eligible_ids = {t['id'] for t in CATALOGUE['tracks'] if t['private_eligible']} if tracks or mode in ('custom_mixed', 'custom_only') else set()
    if not set(tracks) <= eligible_ids:
        raise ValueError('Requested track has no certified level context')
    result = dict(version=VERSION, mode=mode, reserves=reserves, requested_tracks=tracks, catalogue_id=None, selected=[], music=[], excluded=[])
    if mode in ('custom_mixed', 'custom_only'):
        areas, excluded = AV.areas(shuffle, cosmetics)
        candidates = [t for t in CATALOGUE['tracks'] if t['private_eligible'] and (reserves or t['id'] in tracks or t['selection'] == 'preferred')]
        selected = [t for t in candidates if t['id'] in tracks]
        for cat in sorted({a['category'] for a in areas}):
            if any((cat in t['contexts'] for t in selected)):
                continue
            pool = [t for t in candidates if cat in t['contexts']]
            if pool and len(selected) < 16:
                selected.append(min(pool, key=lambda t: rank(seed, 'context-subset', [cat, t['id']])))
        pool = sorted([t for t in candidates if t not in selected], key=lambda t: rank(seed, 'subset', t['id']))
        selected = sorted(selected + pool[:16 - len(selected)], key=lambda t: t['id'])
        result.update(catalogue_id=CATALOGUE['id'], excluded=excluded, selected=[dict(id=t['id'], version=t['version'], score_sha256=t['score_sha256'], payload_sha256=t['payload_sha256'], selector=208 + i, bank=32 + i) for i, t in enumerate(selected)])
        forced = {}
        for t in sorted(selected, key=lambda t: sum((a['category'] in t['contexts'] for a in areas))):
            pool = [a for a in areas if a['id'] not in forced and a['category'] in t['contexts']]
            if pool:
                forced[min(pool, key=lambda a: rank(seed, 'showcase', [t['id'], a['id']]))['id']] = t
        eligible = [a for a in areas if any((a['category'] in t['contexts'] for t in selected))]
        target = len(eligible) if mode == 'custom_only' else round(len(eligible) * 0.67)
        remaining = sorted([a for a in eligible if a['id'] not in forced], key=lambda a: rank(seed, 'original-share', a['id']))
        custom_ids = set(forced) | {a['id'] for a in remaining[:max(0, target - len(forced))]}
        for a in areas:
            pool = [t for t in selected if a['category'] in t['contexts']]
            chosen = forced.get(a['id'])
            if chosen is None and pool and (a['id'] in custom_ids):
                chosen = min(pool, key=lambda t: rank(seed, 'area', [a['id'], t['id']]))
            result['music'].append(dict(id=a['id'], symbol=a['symbol'], tileset=a['tileset'], layout=a['layout'], category=a['category'], secondary=a['secondary'], track=chosen['id'] if chosen else None, selector=208 + selected.index(chosen) if chosen else 0, reason='custom' if chosen else 'original-share' if pool else 'no-compatible-custom'))
    result['sha256'] = fingerprint(result)
    return result

# SPDX-License-Identifier: MPL-2.0
from ..shared.resources import DATA
"Seed-bound presentation assignments; never consumes AP's progression RNG."
import hashlib, json
from pathlib import Path
VERSION = 'm19-cosmetics-1'
DEFAULTS = dict(level_music_shuffle='vanilla', overworld_music_shuffle='vanilla', level_palette_shuffle='off', overworld_palette_shuffle='off', player_appearance='mario')
CHOICES = dict(level_music_shuffle=('vanilla', 'compatible'), overworld_music_shuffle=('vanilla', 'compatible'), level_palette_shuffle=('off', 'constrained'), overworld_palette_shuffle=('off', 'constrained'), player_appearance=('mario', 'luigi'))
TRACKS = {0: 16, 1: 32, 2: 48, 8: 144}
HEADERS = json.loads((DATA / 'cosmetic_headers_m19.json').read_text())

def validate(value=None):
    result = dict(DEFAULTS)
    if value is not None:
        if not isinstance(value, dict) or set(value) - set(DEFAULTS):
            raise ValueError('Unknown cosmetic settings')
        result.update(value)
    if any((result[k] not in CHOICES[k] for k in result)):
        raise ValueError('Unsupported cosmetic setting')
    return result

def hash_value(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def rank(seed, domain, key):
    return hash_value([VERSION, str(seed), domain, str(key)])

def balanced(seed, domain, keys, choices):
    keys = sorted(keys, key=lambda k: (rank(seed, domain + '/keys', k), k))
    choices = sorted(choices, key=lambda k: (rank(seed, domain + '/choices', k), k))
    return {key: choices[i % len(choices)] for i, key in enumerate(keys)}

def assignments(seed, settings=None):
    c = validate(settings)
    levels = {}
    maps = {}
    palettes = {}
    map_palettes = {}
    if c['level_music_shuffle'] == 'compatible':
        eligible = [h['key'] for h in HEADERS if h['music'] in TRACKS and h['key'].startswith('W') and (h['bank'] != 22)]
        levels = balanced(seed, 'level-music', eligible, tuple(TRACKS))
    if c['overworld_music_shuffle'] == 'compatible':
        maps = balanced(seed, 'overworld-music', [str(w) for w in range(1, 9)], tuple(range(1, 9)))
    if c['level_palette_shuffle'] == 'constrained':
        eligible = [h['key'] for h in HEADERS if h['source'].startswith('PRG/levels/Plains/') and h['palette'] in (0, 3) and h['key'].startswith('W') and (h['music'] in TRACKS)]
        palettes = balanced(seed, 'level-palette', eligible, (0, 3))
    if c['overworld_palette_shuffle'] == 'constrained':
        map_palettes = balanced(seed, 'overworld-palette', ['1', '2', '3', '4'], (0, 1, 3))
    result = dict(version=VERSION, settings=c, level_music=levels, overworld_music=maps, level_palettes=palettes, overworld_palettes=map_palettes)
    return {**result, 'assignment_sha256': hash_value(result)}

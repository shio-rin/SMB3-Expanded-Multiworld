# SPDX-License-Identifier: MPL-2.0
"""Versioned enabled reward registry; historical Bowser ID is reserved forever."""
from .resources import DATA
import hashlib, json
VERSION = 'm242-victory-only-1'
RAW = (DATA / 'locations_m242.json').read_bytes()
ROWS = json.loads(RAW)
ACTIVE = tuple((r for r in ROWS if r['enabled']))
BOWSER = next((r for r in ROWS if r['kind'] == 'bowser'))
IDS = [int(r['id'], 16) for r in ACTIVE]
assert len(IDS) == len(set(IDS)) and (not BOWSER['enabled'])
HASH = hashlib.sha256(RAW).hexdigest()

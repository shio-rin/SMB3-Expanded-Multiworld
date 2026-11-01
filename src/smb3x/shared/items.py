# SPDX-License-Identifier: MPL-2.0
"""Canonical item IDs and stored inventory values, shared with the APWorld/Lua."""
from .resources import RESOURCE_ROOT
from hashlib import sha256
import json
from pathlib import Path
RAW = (RESOURCE_ROOT / 'planning/data/items_m25.json').read_bytes()
ITEM_REGISTRY_SHA256 = sha256(RAW).hexdigest()
ITEMS = {int(row['id'], 16): row for row in json.loads(RAW)}
ITEM_BY_NAME = {row['name']: item for item, row in ITEMS.items()}
PASS_ID = ITEM_BY_NAME['World 2 Pass']
ITEM_SIGNATURE = '|'.join((f"{i}:{r['name']}:{r['kind']}:{r.get('native', 0)}" for i, r in ITEMS.items()))
assert len(ITEMS) == len(ITEM_BY_NAME) == 28
assert ITEM_BY_NAME['1-Up'] == 1397568385
assert {r['native'] for r in ITEMS.values() if r['kind'] == 'inventory'} == {1, 2, 3, 4, 5, 6, 8, 9, 11}
PASS_WORLDS = {ITEM_BY_NAME[f'World {w} Pass']: w for w in (2, 3, 4, 5, 6, 7, 8)}
from .progression import HAMMERS
HAMMER_WORLDS = {ITEM_BY_NAME[n]: w for w, n in HAMMERS.items()}
STAR_ID = ITEM_BY_NAME['Star Fragment']

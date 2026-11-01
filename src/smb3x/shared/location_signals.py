# SPDX-License-Identifier: MPL-2.0
"""victory-only Bowser registry; its historical numeric ID stays reserved."""
from .resources import RESOURCE_ROOT
from hashlib import sha256
import json
from pathlib import Path
PATH = RESOURCE_ROOT / 'planning/data/locations_m242.json'
RAW = PATH.read_bytes()
REGISTRY_SHA256 = sha256(RAW).hexdigest()
ROWS = json.loads(RAW)

def signature(rows):
    result = []
    for row in rows:
        entry = row.get('entry', {})
        result.append(':'.join(map(str, [int(row['id'], 16), row['world'], row['stage'], row['kind'], row['signal'], int(row['enabled']), int(row['address'], 16), int(row['bit'], 16), row.get('slot', -1), *(int(entry.get(k, '0x00'), 16) for k in ('x_hi', 'x', 'y')), row.get('tileset', -1), int(row.get('terminal', False)), ','.join(map(str, row.get('object_ids', []))), row.get('receipt_bit', 0)])))
    return '|'.join(result)
SIGNATURE = signature(ROWS)
TERMINAL_ACTIVE = tuple((row for row in ROWS if row['enabled']))
ACTIVE = tuple((row for row in TERMINAL_ACTIVE if not row.get('terminal')))
BY_ID = {int(row['id'], 16): row for row in TERMINAL_ACTIVE}
IDS = frozenset((int(row['id'], 16) for row in ACTIVE if not row.get('hammer_required')))
TERMINAL_IDS = frozenset(BY_ID)

def profile_rows(profile, config=None):
    if profile == 'm242':
        return tuple((r for r in ACTIVE if not r.get('hammer_required') or (config and config['hammer_mode'] == 'regional')))
    raise ValueError('Unknown location profile')

def state_binding(slot_data):
    raw = json.dumps([slot_data['location_registry_sha256'], slot_data['item_registry_sha256'], slot_data['location_profile'], sorted(slot_data['location_ids']), slot_data['goal'], slot_data['progression'], slot_data['level_shuffle']['sha256'], slot_data['audiovisual']['sha256'], slot_data['hazards']['sha256'], slot_data.get('world_pass_placement'), slot_data.get('placement_policy')], separators=(',', ':'), sort_keys=True)
    return sha256(raw.encode()).hexdigest()
assert len({int(row['id'], 16) for row in ROWS}) == len(ROWS)
assert len({(row['world'], row['stage']) for row in ROWS}) == len(ROWS)

def snapshot_checks(world, snapshot):
    """Only committed/frozen-source snapshots; native receipts remain per world."""
    from ..client.persistence.snapshots import ADDRESSES, validate_snapshot
    snapshot = validate_snapshot(snapshot)
    memory = dict(zip(ADDRESSES, snapshot['data']))
    result = []
    for row in ACTIVE:
        if row['world'] != world + 1:
            continue
        if row['kind'] == 'bowser':
            continue
        bit = row.get('receipt_bit')
        proof = bool(memory[31200] & bit) if bit else bool(memory[int(row['address'], 16)] & int(row['bit'], 16))
        if row['kind'] in ('plant', 'military'):
            proof = proof and memory[32533 + row['slot']] == 0
        if row['kind'] in ('house', 'hand'):
            proof = proof and bool(memory[int(row['address'], 16)] & int(row['bit'], 16))
        if proof:
            result.append(int(row['id'], 16))
    return result

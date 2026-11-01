# SPDX-License-Identifier: MPL-2.0
"""transactional world checkpoints; intentionally separate from history."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from ...shared.world_geometry import SUPPORTED, world_descriptor, validate_world_snapshot, map_section
MAX_SEQUENCE = 65534
ADDRESSES = tuple((a for start, n in ((32000, 128), (32491, 56), (31062, 13), (31083, 3), (31087, 4)) for a in range(start, start + n))) + (2018, 1858, 32557, 1979, 31200)

def checksum(values):
    a = b = 0
    for value in values:
        a = a + value & 255
        b = b + a & 255
    return [a, b]

def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != {'data', 'point'}:
        raise ValueError('Invalid snapshot fields')
    data, point = (snapshot['data'], snapshot['point'])
    if not isinstance(data, list) or len(data) != len(ADDRESSES) or (not isinstance(point, list)) or (len(point) != 5) or any((type(v) is not int or not 0 <= v <= 255 for v in data + point)):
        raise ValueError('Invalid snapshot bytes')
    y, x, hi, scroll, scroll_hi = point
    if y < 32 or y > 160 or y % 16 or x % 16 or (hi > 3) or (scroll_hi > 3):
        raise ValueError('Invalid arrival position')
    return deepcopy(snapshot)

def occupied(data, point):
    return any((data[170 + i] and [data[128 + i], data[142 + i], data[156 + i]] == point[:3] for i in range(14)))

def destination_snapshot(world, snapshot, hammer_mode='regional'):
    result = validate_snapshot(snapshot)
    if hammer_mode not in ('legacy', 'regional'):
        raise ValueError('Unknown Hammer mode')
    if hammer_mode == 'legacy' and world in (1, 2, 3):
        address, bit = {1: (32021, 128), 2: (32015, 2), 3: (32025, 2)}[world]
        for a in (address, address + 64):
            result['data'][ADDRESSES.index(a)] |= bit
    descriptor = world_descriptor(world)
    validate_world_snapshot(world, result)
    if map_section(world, result['point'])['arrival'] == 'saved':
        if occupied(result['data'], result['point']):
            raise ValueError('Saved map-section arrival occupied')
        return result
    start = descriptor['start'][:]
    if not occupied(result['data'], start):
        result['point'] = start
    elif occupied(result['data'], result['point']):
        raise ValueError('Destination START and last safe position occupied')
    return result

def seal(snapshot):
    result = validate_snapshot(snapshot)
    return {'snapshot': result, 'sha256': sha256(bytes(result['data'] + result['point'])).hexdigest()}

def unseal(record):
    if not isinstance(record, dict) or set(record) != {'snapshot', 'sha256'}:
        raise ValueError('Invalid snapshot record')
    if seal(record['snapshot']) != record:
        raise ValueError('Snapshot digest mismatch')
    return deepcopy(record['snapshot'])

# SPDX-License-Identifier: MPL-2.0
"""Versioned world descriptors. supports all eight native worlds."""
from .resources import RESOURCE_ROOT
import json
from pathlib import Path
WORLD_ROWS = json.loads((RESOURCE_ROOT / 'planning/data/worlds_m191.json').read_text())
SUPPORTED = tuple((r['native_world'] for r in WORLD_ROWS if r['supported']))

def world_descriptor(world):
    if type(world) is not int or world not in SUPPORTED:
        raise ValueError('Unsupported world')
    return WORLD_ROWS[world]

def validate_world_snapshot(world, snapshot):
    r = world_descriptor(world)
    y, x, hi, lo, scroll_hi = snapshot['point']
    camera = lo + 256 * scroll_hi
    if hi >= r['map_pages'] or camera % 128 or camera > r['max_scroll']:
        raise ValueError('Position/camera outside world geometry')
    if not 0 <= hi * 256 + x - camera < 256:
        raise ValueError('Arrival is outside visible camera page')
    section = next((s for s in r['sections'] if hi in s['pages']), None)
    if section is None or (section['camera'] == 'fixed' and camera != 256 * hi):
        raise ValueError('Invalid overworld section/camera')
    return snapshot

def map_section(world, point):
    """Sections share native buffers; page membership disambiguates active map."""
    return next((s for s in world_descriptor(world)['sections'] if point[2] in s['pages']))

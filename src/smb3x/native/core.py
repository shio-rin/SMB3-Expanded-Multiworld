# SPDX-License-Identifier: MPL-2.0
"""Build the guarded native foundation. Historical patch/assembly names below are
certificate and serialized identities; the final pipeline owns the current release."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from ..shared.resources import RESOURCE_ROOT as ROOT
from ..shared.identity import Identity
from .rom import Edit, apply_bps, apply_edits, digest, make_bps, prg_offset, verify_base
PATCH_VERSION = 'm191-native-4'
MARKER_OFFSET = prg_offset(30, 40720, 32768)

def build(source: bytes, identity: Identity, goal: str='standard', progression=None, *, offline_fixture=False, cosmetics=None, level_shuffle='vanilla', classic_level_packs='off', classic_stage_count=0) -> tuple[bytes, bytes, dict]:
    verify_base(source)
    if offline_fixture and (not identity.seed.startswith('SMB3-M19.1-OFFLINE-FIXTURE-')):
        raise ValueError('Offline visual switch requires dedicated fixture identity')
    from ..shared.victory import GOALS, validate_goal
    validate_goal(goal)
    from ..shared.progression import validate, native_bytes
    progression = validate(progression)
    marker = b'SMB3APK\x00' + bytes([9, GOALS.index(goal), 0, 0]) + bytes.fromhex(identity.key) + native_bytes(progression)
    rows = json.loads((ROOT / 'planning/data/locations_m191.json').read_text())
    enabled = [r for r in rows if r['enabled'] and (not r.get('hammer_required') or progression['hammer_mode'] == 'regional')]
    marker = marker[:10] + bytes([len(enabled), (2 if offline_fixture else int(progression['reward_visual_style'] == 'mystery')) | (4 if progression['inventory_mode'] == 'stacked' else 0)]) + marker[12:]
    from .core_assembly import assemble
    edits, symbols = assemble()
    edits.append(Edit(MARKER_OFFSET, b'\xff' * len(marker), marker, 'PRG030 unused $9F10-$9F3F identity and enabled total'))
    from .patches.cosmetics import edits as cosmetic_edits
    changes, cosmetic_plan = cosmetic_edits(source, identity.seed, cosmetics)
    edits.extend(changes)
    from ..planning.stages import assignments
    changes = []
    shuffle_plan = assignments(identity.seed, level_shuffle, classic_level_packs, classic_stage_count)
    edits.extend(changes)
    target = apply_edits(source, edits)
    config = {'patch_version': PATCH_VERSION, 'protocol': 9, 'offline_fixture': bool(offline_fixture), 'identity': identity.as_dict(), 'session': identity.key, 'goal': goal, 'progression': progression, 'cosmetics': cosmetic_plan}
    config['level_shuffle'] = shuffle_plan
    config['classic_compiler_sha256'] = None
    manifest = {**config, 'source': digest(source), 'source_payload': digest(source[16:]), 'output': digest(target), 'output_payload': digest(target[16:]), 'prg_sha256': digest(target[16:262160])['sha256'], 'chr_sha256': digest(target[262160:])['sha256'], 'assembly': {'source_sha256': digest((ROOT / 'native/asm/m191.asm').read_bytes())['sha256'], 'assembler_sha256': 'd6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501', 'symbols': symbols}, 'edits': [{'offset': e.offset, 'size': len(e.after), 'name': e.name} for e in edits]}
    config['assembly'] = manifest['assembly']
    return (target, config)

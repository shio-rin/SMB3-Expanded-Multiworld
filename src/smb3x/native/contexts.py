# SPDX-License-Identifier: MPL-2.0
from ..planning import special_stages, mixed_fortresses
'Apply certified stage relocation, source contexts and special-stage patches.'
from pathlib import Path
import importlib.util
import json
import sys
from ..shared.resources import RESOURCE_ROOT as ROOT
from .rom import verify_base, digest
from .patches.stage_storage import install as install_areas
from .allocation import Registry
from .bps import make_bps, apply_bps
from .patches.cosmetics import assignments as cosmetic_assignments
PATCH_VERSION = 'm23-native-1'

def contexts(source, identity, original, base, goal='standard', progression=None, *, cosmetics=None, level_shuffle='vanilla', classic_level_packs='off', classic_stage_count=0, audiovisual=None, pack=None, poison_mushrooms='off', angry_sun='off', offline_fixture=False, special_stage_shuffle='off'):
    verify_base(source)
    if classic_level_packs != 'off' or classic_stage_count != 0 or offline_fixture:
        raise ValueError('release supports original-only live builds; Classics and offline fixtures are excluded')
    if offline_fixture and (not identity.seed.startswith('SMB3-M222-OFFLINE-FIXTURE-')):
        raise ValueError('Dedicated offline identity required')
    from ..planning import stages
    sh = vars(stages)
    from ..planning import audiovisual as av_plan
    avc = vars(av_plan)
    from .initial_hazards import plan as initial_hazards
    shuffle = sh['assignments'](identity.seed, level_shuffle, classic_level_packs, classic_stage_count, special_stage_shuffle)
    hazards = initial_hazards(identity.seed, shuffle, poison_mushrooms, angry_sun)
    av_settings = avc['validate'](audiovisual)
    cosmetic_settings = dict(cosmetics or {})
    for kind in ('level', 'overworld'):
        if av_settings[kind + '_palette_style'] == 'constrained':
            cosmetic_settings[kind + '_palette_shuffle'] = 'constrained'
    cosmetic_plan = cosmetic_assignments(identity.seed, cosmetic_settings)
    if pack is not None:
        from ..native.music.score.pack import verify_pack
        verify_pack(pack)
    av, songs = avc['plan'](identity.seed, shuffle, pack, av_settings, cosmetic_plan)
    contents = []
    certified = sh['CONTENTS']
    rom = bytearray(original)
    ledger = Registry()
    for row in base['allocation']:
        ledger.reserve(**row)
    from .patches.content_dispatch import install as install_content
    external_theme = {**next((t for t in avc['THEMES'] if t['id'] == 'hills-autumn')), 'id': 'hills-autumn-external'}
    external_theme['background'] = list(external_theme['background'])
    external_theme['background'][3] = external_theme['background'][0]
    content_extension = install_content(rom, source, av, ledger, themes=[*avc['THEMES'], external_theme])
    storage = install_areas(rom, source, [], scenery=True)
    for row in shuffle['assignments']:
        physical = certified[row['original_content']]
        entry = row['native_entry']
        replacements = {'ByRowType': bytes([int(physical['original_table_bytes']['ByRowType'], 16) & 240 | entry['tileset']]), 'LevelLayout': entry['layout'].to_bytes(2, 'little'), 'ObjSets': entry['objects'].to_bytes(2, 'little')}
        for key, value in replacements.items():
            offset = physical['table_sites'][key]
            before = bytes.fromhex(physical['original_table_bytes'][key])
            if rom[offset:offset + len(before)] != before:
                raise ValueError('physical entrance source guard')
            rom[offset:offset + len(value)] = value
    by_area = {(c['content_id'], a['id'].rsplit('/', 1)[-1]): a for c in contents for a in c['areas']}
    original_areas = json.loads((ROOT / 'planning/data/original_hazard_areas_m221.json').read_text())['contents']
    for c in original_areas:
        by_area[c['content_id'], 'main'] = c
    for cid, c in certified.items():
        if not cid.startswith('classic/'):
            by_area[cid, 'main'] = c
    poison = [dict(tileset=by_area[p['content_id'], p['area']]['tileset'], layout=by_area[p['content_id'], p['area']]['layout'], x=p['x'] * 16, y=p['y'] * 16, **{k: p[k] for k in ('source_rom_offset', 'source_bytes') if k in p}) for p in hazards['poison']]
    suns = [dict(tileset=by_area[p['content_id'], p['area']]['tileset'], layout=by_area[p['content_id'], p['area']]['layout'], spawn_column=p['spawn_column'], activation_x=p['activation_column'] * 16) for p in hazards['suns']]
    from .patches.hazard_core import install as install_hazards
    native_hazards = install_hazards(rom, source, poison, suns, graphics=True, collision_area=dict(certified['classic/smw/yoshis-island-2']['areas'][0]))
    from .patches.stage_context import install as install_context
    context_rows = []
    for row in shuffle['assignments']:
        donor = certified[row['assigned_content']]
        host = certified[row['original_content']]
        if donor['source_family'] != 'smb3-prg1':
            continue
        e = host['physical_entry']
        context_rows.append(dict(world=host['original_world'] - 1, hi=int(e['x_hi'], 16), x=int(e['x'], 16), y=int(e['y'], 16), source_world=donor['original_world'] - 1))
    special_rows = None
    if special_stage_shuffle != 'off':
        from .patches.special_stages import bindings
        special_rows = bindings(shuffle['special_stage_shuffle'], special_stages.CONTENTS)
        context_rows += special_rows['context']
        if special_stage_shuffle == 'mixed_fortresses':
            from .patches.special_stages import add_mixed
            add_mixed(special_rows, shuffle['assignments'], certified, mixed_fortresses.CONTRACT)
    native_context = install_context(rom, source, context_rows)
    native_special = None
    if special_rows is not None:
        from .patches.special_stages import install as install_special
        native_special = install_special(rom, source, special_rows)
    graphics = {'version': 'm23-original-only-1', 'classic_graphics_installed': False}
    from .patches.title import install as install_title
    title = install_title(rom, source)
    for bank in (30, 62):
        off = 16 + bank * 8192 + 7952
        if rom[off:off + 8] != b'SMB3APL\x00':
            raise ValueError('marker source guard')
        rom[off:off + 8] = b'SMB3APP\x00'
        if offline_fixture:
            rom[off + 11] = rom[off + 11] & ~3 | 2
    if rom[16 + 30 * 8192:16 + 32 * 8192] != rom[16 + 62 * 8192:16 + 64 * 8192]:
        raise ValueError('Fixed mirror mismatch')
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, architecture='mmc3-512k-prg-256k-chr-m222', offline_fixture=bool(offline_fixture), engineering_only=False, level_shuffle=shuffle, audiovisual=av, song_pack=pack, content_extension=content_extension, hazards=hazards, native_hazards=native_hazards, m222_context=native_context, m222_special=native_special, m222_title=title, m222_storage=storage, m222_graphics=graphics, m222_sources={'native/contexts.py': digest(Path(__file__).read_bytes())['sha256']})
    config['allocation'] = [r.__dict__ for r in ledger.rows] + [{'owner': 'preserved-external-generator-data', 'bank': b, 'start': 0, 'size': 8192} for b in (49, 50)] + [{'owner': 'hazards-source-context-dpcm', 'bank': 51, 'start': 0, 'size': 8192}]
    if native_special is not None:
        config['allocation'].append({'owner': 'special-host-terminal-context-dpcm', 'bank': 52, 'start': 0, 'size': 8192})
    target = bytes(rom)
    return (target, config)

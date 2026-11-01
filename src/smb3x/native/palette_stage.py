# SPDX-License-Identifier: MPL-2.0
from ..planning import hazards as hazard_plan
'Apply palette selection to the preceding guarded native build.'
from pathlib import Path
from .patches.palettes import install
from .bps import make_bps, apply_bps
from .rom import digest
from ..shared.resources import RESOURCE_ROOT as ROOT
PATCH_VERSION = 'm242-native-2'
from ..planning import palettes as palette_plan
PALETTES = vars(palette_plan)
from ..shared import locations as location_registry
REGISTRY = vars(location_registry)

def palette_stage(source, identity, original, base, *args, palette_mode='atmospheric', world_pass_placement='unrestricted', placement_policy=None, **kwargs):
    if world_pass_placement not in ('unrestricted', 'staggered') or (world_pass_placement == 'staggered' and (not placement_policy)):
        raise ValueError('Missing/invalid final placement policy identity')
    progression = dict(kwargs.get('progression') or {})
    if progression.get('inventory_mode', 'stacked') != 'stacked':
        raise ValueError('New games require Stacked inventory')
    progression['inventory_mode'] = 'stacked'
    kwargs['progression'] = progression
    av = kwargs.get('audiovisual') or {}
    cosmetic = kwargs.get('cosmetics') or {}
    if kwargs.get('pack') is not None or av.get('music_policy', 'vanilla') != 'vanilla':
        raise ValueError('supports original SMB3 music only')
    for kind in ('level', 'overworld'):
        if av.get(kind + '_palette_style', 'vanilla') != 'vanilla' or cosmetic.get(kind + '_palette_shuffle', 'off') != 'off':
            raise ValueError('Use palette_mode instead of legacy palette controls')
    selection = PALETTES['plan'](identity.seed, palette_mode)
    poison = kwargs.get('poison_mushrooms', 'off')
    kwargs['poison_mushrooms'] = 'off'
    hazards = hazard_plan._base_plan(identity.seed, base['level_shuffle'], poison, kwargs.get('angry_sun', 'off'))
    assert hazards['suns'] == base['hazards']['suns'], 'Sun independence'
    rom = bytearray(original)
    from .patches.hazard_tables import install as install_hazards
    hazard_extension = install_hazards(rom, source, hazards)
    import json
    previous_count = sum((r['enabled'] for r in json.loads((ROOT / 'planning/data/locations_m191.json').read_text())))
    for bank in (30, 62):
        offset = 16 + bank * 8192 + 7962
        if rom[offset] != previous_count:
            raise ValueError('Native enabled count source guard')
        rom[offset] = len(REGISTRY['ACTIVE'])
    old_rows = json.loads((ROOT / 'planning/data/locations_m191.json').read_bytes())
    totals = bytes((sum((r['enabled'] and r['world'] == w for r in old_rows)) for w in range(1, 9))) * 2
    revised = bytes((sum((r['world'] == w for r in REGISTRY['ACTIVE'])) for w in range(1, 9))) * 2
    offset = 16 + 25 * 8192 + base['assembly']['symbols']['ProgressionWorldTotals'] - 40960
    if rom[offset:offset + 16] != totals:
        raise ValueError('Native per-world tracker totals source guard')
    rom[offset:offset + 16] = revised
    map_music = base['cosmetics']['overworld_music']
    if map_music:
        for bank, address, origin in ((30, 34451, 32768), (62, 34451, 32768), (10, 50142, 49152)):
            off = 16 + bank * 8192 + address - origin
            if rom[off:off + 2] != bytes.fromhex('a009'):
                raise ValueError('World5 native sky music source guard')
            rom[off + 1] = map_music['5']
    extension = None if palette_mode == 'original' else install(rom, base, selection)
    rom = bytes(rom)
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(world_pass_placement=world_pass_placement, placement_policy=placement_policy, hazards=hazards, m242_hazard_extension=hazard_extension, patch_version=PATCH_VERSION, m242_palettes=selection, m242_extension=extension, location_profile='m242', location_contract=REGISTRY['VERSION'], enabled_location_ids=REGISTRY['IDS'], map_music_contract='m242-physical-world-music-1', m242_sources={__file__.replace('\\', '/').rsplit('/', 1)[-1]: digest(Path(__file__).read_bytes())['sha256']})
    return (rom, config)

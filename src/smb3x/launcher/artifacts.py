# SPDX-License-Identifier: MPL-2.0
"""Construct and independently verify the owned player patch and canonical ROM."""

from .paths import ROM_FILENAME
from pathlib import Path
import argparse, json
from ..shared.resources import RESOURCE_ROOT as ROOT
from .artifact_files import fresh, dump, sha


def prepare(args):
    from ..shared.identity import Identity
    from ..native.pipeline import build
    from ..native.rom import verify_base

    source = args.rom.read_bytes()
    verify_base(source)
    slot = json.loads(args.slot.read_text(encoding='utf-8-sig'))
    if slot.get('format') != 'smb3-m23-slot-1' or slot.get('release') != '23.0.0-core-rc3':
        raise ValueError(
            'Select the .smb3.json from this release APWorld, extracted from the seed ZIP.'
        )
    data = slot['slot_data']
    sh = data['level_shuffle']
    if data.get('release') != 'm27-1':
        raise ValueError('Fresh SMB3X player file required')
    if data['location_profile'] != 'm242' or data['bridge_protocol'] != 35:
        raise ValueError('Unsupported APWorld profile or protocol.')
    if sh['classic_level_packs'] != 'off' or sh['classic_stage_count'] != 0:
        raise ValueError('core requires original-only content.')
    out = fresh(args.output)
    music = data['r3_music']
    private_pack = None
    if music['selected']:
        from ..native.music.private_provider import locate

        private_pack = locate()
    rom, patch, manifest = build(
        source,
        Identity(slot['seed_name'], slot['team'], slot['slot']),
        effects=data['effects'],
        trap_warning=data['trap_warning'],
        goal=data['goal'],
        progression=data['progression'],
        cosmetics=data['cosmetics']['settings'],
        level_shuffle=sh['mode'],
        special_stage_shuffle=sh['special_stage_shuffle']['setting'],
        audiovisual=data['audiovisual']['settings'],
        music_mode=music['mode'],
        music_reserves=music['reserves'],
        music_tracks=music['requested_tracks'],
        private_pack=private_pack,
        palette_mode=data['m242_palettes']['release_mode'],
        world_pass_placement=data['world_pass_placement'],
        placement_policy=data['placement_policy'],
        **data['hazards']['settings']
    )
    for key in (
        'cosmetics',
        'level_shuffle',
        'audiovisual',
        'hazards',
        'm242_palettes',
        'special_palette_selection',
        'r3_music',
        'location_contract',
        'enabled_location_ids',
        'interface_contract',
        'foundation_contract',
        'sfx_restoration_contract',
        'trap_warning',
        'presentation_contract',
        'effects',
        'world_pass_placement',
        'placement_policy',
    ):
        if data[key] != manifest[key]:
            raise ValueError('APWorld/build identity mismatch: ' + key)
    (out / 'smb3-m23.bps').write_bytes(patch)
    dump(out / 'build.json', manifest)
    # Historical purpose is serialized and integrity-bound; it is not a UI label.
    dump(
        out / 'session.json',
        dict(
            purpose='m222-manual-test',
            airship_test=False,
            seed_name=slot['seed_name'],
            slot_name=slot['slot_name'],
            slot=slot['slot'],
            team=slot['team'],
            slot_data=data,
        ),
    )
    dump(out / 'integrity.json', {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    from ..shared.archives import write_zip

    if not music['selected']:
        write_zip(
            out / 'Player-Patch.zip', {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
        )
    if music['selected']:
        (out / 'PRIVATE-MUSIC.txt').write_text(
            'Private R3 score-derived ROM/BPS. Keep local; no redistribution rights established.\n'
        )
    (out / ROM_FILENAME).write_bytes(rom)
    print(
        'Prepared '
        + slot['slot_name']
        + ' / seed '
        + slot['seed_name']
        + '. Private preparation complete.'
    )


def verify_game(folder, original):
    from ..native.rom import verify_base
    from ..native.bps import apply_bps
    from ..native.verification import verify_build

    source = original.read_bytes()
    verify_base(source)
    inventory = json.loads((folder / 'integrity.json').read_text())
    if set(inventory) != {'smb3-m23.bps', 'build.json', 'session.json'}:
        raise ValueError('Unsupported player patch inventory.')
    for name, digest in inventory.items():
        if sha(folder / name) != digest:
            raise ValueError('Player patch integrity mismatch: ' + name)
    manifest = json.loads((folder / 'build.json').read_text())
    session = json.loads((folder / 'session.json').read_text())
    rom = apply_bps(source, (folder / 'smb3-m23.bps').read_bytes())
    verify_build(rom, manifest, session['seed_name'], source)
    if (
        session.get('slot') != manifest['identity']['slot']
        or session.get('team') != manifest['identity']['team']
    ):
        raise ValueError('Player slot/team differs from ROM identity.')
    for key in (
        'goal',
        'progression',
        'cosmetics',
        'level_shuffle',
        'audiovisual',
        'hazards',
        'm242_palettes',
        'special_palette_selection',
        'r3_music',
        'location_contract',
        'enabled_location_ids',
        'interface_contract',
        'foundation_contract',
        'sfx_restoration_contract',
        'trap_warning',
        'presentation_contract',
        'effects',
        'world_pass_placement',
        'placement_policy',
    ):
        if session['slot_data'][key] != manifest[key]:
            raise ValueError('Player session/build mismatch: ' + key)
    return (rom, manifest, session)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare'])
    p.add_argument('--slot', type=Path, required=True)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    prepare(p.parse_args())

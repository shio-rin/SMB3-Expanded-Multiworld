# SPDX-License-Identifier: MPL-2.0
"""Exact production rebuild; no historical build or checkpoint reinterpretation."""
from .pipeline import build as reconstruct, PATCH_VERSION
from ..shared.identity import Identity

def verify_build(rom, build, seed, source):
    if build.get('patch_version') != PATCH_VERSION or build.get('protocol') != 9:
        raise ValueError('Unsupported foundation build; use the matching player file')
    identity = Identity(**build['identity'])
    if identity.seed != seed or identity.key != build.get('session'):
        raise ValueError('Build seed/session mismatch')
    if build.get('engineering_only') or build.get('offline_fixture'):
        raise ValueError('Engineering/offline build cannot connect')
    sh = build['level_shuffle']
    music = build['r3_music']
    payloads = {r['id']: rom[16 + r['bank'] * 8192:16 + r['bank'] * 8192 + 6144] for r in music['selected']}
    expected, _, manifest = reconstruct(source, identity, effects=build['effects'], trap_warning=build['trap_warning'], goal=build['goal'], progression=build['progression'], cosmetics=build['cosmetics']['settings'], level_shuffle=sh['mode'], special_stage_shuffle=sh['special_stage_shuffle']['setting'], audiovisual=build['audiovisual']['settings'], pack=build['song_pack'], music_mode=music['mode'], music_reserves=music['reserves'], music_tracks=music['requested_tracks'], music_payloads=payloads, palette_mode=build['m242_palettes']['release_mode'], world_pass_placement=build['world_pass_placement'], placement_policy=build['placement_policy'], **build['hazards']['settings'])
    if rom != expected or build != manifest:
        raise ValueError('ROM or manifest differs from reproducible foundation build')

# SPDX-License-Identifier: MPL-2.0
"""Build, verify and publish one session-owned game; construct its Resume binding."""

from .paths import ROM_FILENAME
import uuid
from ..shared.resources import RESOURCE_ROOT as ROOT
from ..client.persistence.atomic import save_json as atomic, publish_directory
from ..shared.serialization import fingerprint, read, sha


def prepare(root, record, original):
    """Prepare in a retained candidate directory; publish only a complete verified game."""
    from types import SimpleNamespace
    from .artifacts import prepare as build_game, verify_game

    candidate = root / ('prepare-' + uuid.uuid4().hex)
    candidate.mkdir()
    slot = dict(record, format='smb3-m23-slot-1', release='23.0.0-core-rc3')
    slotfile = candidate / 'slot.json'
    atomic(slotfile, slot)
    game = candidate / 'game'
    build_game(SimpleNamespace(slot=slotfile, rom=original, output=game))
    verify_game(game, original)
    build = read(game / 'build.json')
    atomic(
        candidate / 'session.json',
        dict(
            schema=1,
            record_sha256=fingerprint(record),
            resource_id=record['resource_id'],
            session=build['session'],
            build_sha256=sha(game / 'build.json'),
            rom_sha256=sha(game / ROM_FILENAME),
        ),
    )
    publish_directory(candidate, root / 'prepared')


def binding(root, game, build, session, emulator, lua, resource_id):
    from ..shared.location_signals import state_binding

    return dict(
        schema=3,
        effects=build['effects'],
        identity=build['identity'],
        player=session['slot_name'],
        game='Super Mario Bros. 3: Expanded Multiworld',
        session=build['session'],
        rom_sha256=build['output']['sha256'],
        prg_sha256=build['prg_sha256'],
        chr_sha256=build['chr_sha256'],
        game_files={
            n: sha(game / n)
            for n in ('build.json', 'session.json', 'integrity.json', 'smb3-m23.bps')
        },
        registry=state_binding(session['slot_data']),
        location_ids=sorted(session['slot_data']['location_ids']),
        progression=build['progression'],
        goal=build['goal'],
        native=9,
        wire=40,
        ap=35,
        ending=1,
        patch=build['patch_version'],
        checkpoint_schema=3,
        assignments={
            k: build[k]
            for k in (
                'cosmetics',
                'level_shuffle',
                'audiovisual',
                'hazards',
                'm241_palettes',
                'm242_palettes',
                'special_palette_selection',
                'r3_music',
            )
            if k in build
        },
        emulator=emulator,
        package_sha256=resource_id,
        controller_sources={
            p.relative_to(root).as_posix(): sha(p)
            for folder in ('client', 'bizhawk')
            for p in (root / folder).rglob('*')
            if p.suffix in ('.py', '.lua')
        },
        lua_support={
            n: sha(lua / n)
            for n in ('json.lua', 'x64/socket-windows-5-1.dll', 'x64/socket-windows-5-4.dll')
        },
    )

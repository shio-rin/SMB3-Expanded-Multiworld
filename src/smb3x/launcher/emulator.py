# SPDX-License-Identifier: MPL-2.0
from .paths import ROM_FILENAME
'launcher / emulator implementation for managed SMB3X sessions.'
from pathlib import Path
import asyncio, json, logging, os, socket, subprocess, uuid
from ..shared.resources import RESOURCE_ROOT as ROOT
from .preferences import CONFIG_SCHEMA, collect_preferences, configuration, managed_configuration, validate_configuration
from ..client.persistence.atomic import save_json as atomic
from .preparation import binding
from .windows import close_owned_emulator, process_identity, retire_orphan
from .dialogs import confirm
from .connection import connected
from ..shared.serialization import fingerprint, sha
from ..shared.emulators import identify, profile, EmulatorCompatibilityError, verify_frontend
from ..shared.serialization import read

def lua_strings(v):
    return '{' + ','.join(('[' + json.dumps(k) + ']=' + json.dumps(value) for k, value in v.items())) + '}'

def emulator_identity(exe, config=None):
    selected = identify(exe)
    config = configuration(selected['version']) if config is None else config
    return dict(profile=selected['version'], revision=selected['revision'], core='NesHawk',
                config_schema=CONFIG_SCHEMA,
                settings_sha256=fingerprint(validate_configuration(config, selected['version'])),
                files=selected['files'])


def require_session_emulator(session_root, identity):
    """Refuse version/core changes before creating a run or restoring native State."""
    path = session_root / 'emulator-identity.json'
    if path.exists():
        previous = read(path)
        if previous != identity:
            raise EmulatorCompatibilityError('This session is bound to BizHawk ' + str(previous.get('profile', 'unknown'))
                             + ' and its exact core/configuration. Reopen with that installation. '
                             'Cross-version Resume is unsupported; existing saves were retained.')
    elif (session_root / 'saves/EPOCH.json').exists() or (session_root / 'saves/LATEST.json').exists():
        raise EmulatorCompatibilityError('Session emulator ownership record is missing; preserve this session and its matching runtime.')


def play(cache, resource_id, session_root, game, original, emulator, server, password):
    import Utils
    from ..client.persistence.checkpoints import CheckpointStore, RecoveryConfirmationNeeded, write_new
    from .artifacts import verify_game
    rom, build, session = verify_game(game, original)
    if (game / ROM_FILENAME).read_bytes() != rom:
        raise ValueError('Prepared ROM differs from verified patch')
    emu_id = emulator_identity(emulator)
    version = emu_id['profile']
    config = configuration(version)
    require_session_emulator(session_root, emu_id)
    logging.getLogger('SMB3X').info('Verified BizHawk %s / NesHawk', version)
    existing_config = session_root / 'bizhawk/config.ini'
    if existing_config.exists():
        validate_configuration(json.loads(existing_config.read_text(encoding='utf-8-sig')), version)
    lua = Path(Utils.local_path('data', 'lua')).resolve()
    for name in ('json.lua', 'x64/socket-windows-5-1.dll', 'x64/socket-windows-5-4.dll'):
        if not (lua / name).is_file():
            raise ValueError('Official Archipelago Lua support missing: ' + str(lua / name))
    # Validate the selected audio backend before opening a new epoch or resuming.
    config_path, config = managed_configuration(session_root, emulator)
    verify_frontend(emulator, config)
    bind = binding(cache, game, build, session, emu_id, lua, resource_id)
    identity_path = session_root / 'emulator-identity.json'
    if not identity_path.exists():
        write_new(identity_path, emu_id)
    store = CheckpointStore(session_root / 'saves', bind)
    components = None
    folder = None
    marker = None
    if (store.root / 'LATEST.json').exists():
        try:
            run, live, folder, manifest, components = store.resume()
        except RecoveryConfirmationNeeded as exc:
            if not confirm(str(exc)):
                return
            run, live, folder, manifest, components = store.resume(allow_loss=True)
        marker = manifest['marker']
    elif (store.root / 'EPOCH.json').exists():
        run, live = store.restart_unstarted()
    else:
        run, live = store.new_run()
    retire_orphan(session_root, session_root.name, close=True)
    ctl = dict(schema=3, run=run, token=uuid.uuid4().hex, location_ids=bind['location_ids'], resume=folder.as_posix() if folder else None, marker=marker, restored_at=(store.recovery or {}).get('saved'), recovery_kind=(store.recovery or {}).get('kind'), user_start_paused=config['StartPaused'], emulator_version=version, lua_version=profile(version)['lua'])
    write_new(live / 'control.json', ctl)
    write_new(live / 'emulator.json', config)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    options = dict(emulator_version=version, lua_version=profile(version)['lua'], project=cache.as_posix(), build=(game / 'build.json').as_posix(), ap_lua=lua.as_posix(), control=(live / 'control.json').as_posix())
    script = 'local options=' + lua_strings(options) + '\noptions.port=' + str(port) + '\nassert(loadfile(' + json.dumps((cache / 'bizhawk/bridge.lua').as_posix()) + '))(options)\n'
    (live / 'Start-SMB3.lua').write_text(script, encoding='utf-8')
    env = dict(os.environ, SMB3_AP_PROJECT=str(cache), SMB3_SESSION_ROOT=str(session_root), PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    env.pop('SMB3_AP_CORE', None)
    with (live / 'emulator.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(emulator), '--config=' + str(config_path), '--lua=' + str(live / 'Start-SMB3.lua'), str(game / ROM_FILENAME)], cwd=live, env=env, stdout=log, stderr=subprocess.STDOUT)
        write_new(live / 'launch.json', dict(pid=process.pid, backend_pid=os.getpid(), run=run, mode='resume' if components else 'new'))
        atomic(session_root / 'owner.json', dict(schema=2, session_key=session_root.name, emulator=process_identity(process.pid), backend=process_identity(os.getpid()), run=run))
        try:
            clean = asyncio.run(connected(store, run, live, ctl, components, build, session, server, password, port, process))
            if clean and process.poll() is None:
                close_owned_emulator(process)
        finally:
            if process.poll() is not None:
                try:
                    collect_preferences(session_root)
                except (ValueError, OSError) as exc:
                    logging.getLogger('SMB3X').warning('Emulator preferences retained locally but not shared: %s', exc)

# SPDX-License-Identifier: MPL-2.0
"""Managed player entry: validate ownership, prepare once, connect and Resume."""
from pathlib import Path
import logging, os
from ..shared.resources import RESOURCE_ROOT as ROOT
from ..client.persistence.atomic import save_json as atomic
from .preparation import prepare
from .history import cached_runtime
from .preferences import configuration
from .dialogs import confirm, question, select
from .player_file import container
from .emulator import emulator_identity, play, require_session_emulator
from ..shared.serialization import fingerprint, read, sha
from .paths import home
from .windows import optional_association, protect, retire_orphan
from .runtime import verify as verify_resources

def select_emulator(root, remembered):
    """Offer a profile choice for new games, retain exact ownership for Resume."""
    emulator = Path(remembered or '')
    owner_path = root / 'emulator-identity.json'
    try:
        identity = emulator_identity(emulator)
        require_session_emulator(root, identity)
    except (ValueError, OSError):
        title = ('Select this session\'s BizHawk ' + str(read(owner_path).get('profile', 'unknown'))
                 + ' / NesHawk installation') if owner_path.exists() else 'Select a supported BizHawk / NesHawk installation'
    else:
        if owner_path.exists() or confirm('Use verified BizHawk ' + identity['profile']
                + ' / NesHawk for this new game? Choose No to select another supported installation. '
                'This game will remain bound to the selected version.'):
            return emulator
        title = 'Select a supported BizHawk / NesHawk installation'
    emulator = select(title, [('BizHawk', ('.exe',))])
    require_session_emulator(root, emulator_identity(emulator))
    return emulator

def main(args, cache, resource_id):
    import Utils
    from ..client.persistence.locking import session_lock
    base = home()
    base.mkdir(parents=True, exist_ok=True)
    try:
        path = Path(args[0]) if args else select('Open your SMB3X player file', [('SMB3X player', ('.apsmb3x',))])
        manifest, record = container(path)
        if manifest['resource_id'] != resource_id:
            return cached_runtime((str(path),), manifest['resource_id'])
        verify_resources(cache, resource_id)
        if manifest['patch'] != 'm26-native-2' or record['slot_data'].get('release') != 'm27-1':
            raise ValueError('This runtime requires a fresh SMB3X player file; older games require their matching cached resources')
        key = fingerprint(record)
        root = base / 'sessions' / key[:24]
        from .paths import preflight_session
        preflight_session(root)
        root.mkdir(parents=True, exist_ok=True)
        with session_lock(root / 'owner.lock'):
            retire_orphan(root, key[:24])
            os.environ['SMB3_SESSION_ROOT'] = str(root)
            logging.getLogger().addHandler(logging.FileHandler(root / 'client.log', encoding='utf-8'))
            settings_path = base / 'settings.json'
            settings = read(settings_path) if settings_path.exists() else {}
            from ..native.rom import verify_base
            original = Path(settings.get('rom', ''))
            try:
                verify_base(original.read_bytes())
            except (ValueError, OSError):
                original = select('Select your clean SMB3 USA Rev A ROM', [('NES ROM', ('.nes',))])
                verify_base(original.read_bytes())
            emulator = select_emulator(root, settings.get('emulator'))
            settings.update(rom=str(original), emulator=str(emulator))
            if os.name == 'nt' and (not settings.get('association_asked')):
                if confirm('Open future .apsmb3x player files with Archipelago? This optional convenience registers only the SMB3X file type for your Windows account.'):
                    optional_association(Path(Utils.local_path('ArchipelagoLauncher.exe')))
                settings['association_asked'] = True
            atomic(settings_path, settings)
            prepared = root / 'prepared'
            if not prepared.exists():
                prepare(root, record, original)
            descriptor = prepared / 'session.json'
            if not descriptor.is_file():
                raise ValueError('Internal session preparation metadata missing. Preserve this session folder: ' + str(root))
            metadata = read(descriptor)
            if metadata.get('schema') != 1 or metadata.get('record_sha256') != key or metadata.get('resource_id') != resource_id or (metadata.get('build_sha256') != sha(prepared / 'game/build.json')):
                raise ValueError('Internal session metadata mismatch; no save was replaced: ' + str(root))
            connection = root / 'connection.json'
            saved = read(connection) if connection.exists() else {}
            server = (saved.get('server') if saved.get('override_server') else None) or manifest.get('server') or saved.get('server') or question('SMB3 room', 'Room address (host:port)')
            if not server:
                raise ValueError('A room address is required')
            password = protect(saved.get('password', ''), True) if saved else question('SMB3 room', 'Room password (leave blank if none)', secret=True)
            atomic(connection, dict(server=server, password=protect(password), override_server=bool(saved.get('override_server'))))
            play(cache, resource_id, root, prepared / 'game', original, emulator, server, password or None)
    except Exception as exc:
        logging.exception('SMB3 stopped; original files retained')
        if str(exc).startswith(('Room password required', 'Room connection refused')) and 'root' in locals() and confirm(str(exc) + '\n\nUpdate the remembered room details for the next time you open this player file?'):
            try:
                old = read(root / 'connection.json') if (root / 'connection.json').is_file() else {}
                address = question('SMB3 room', 'Room address (host:port)', old.get('server', ''))
                if not address:
                    raise ValueError('A room address is required')
                password = question('SMB3 room', 'Room password (leave blank if none)', secret=True)
                atomic(root / 'connection.json', dict(server=address, password=protect(password), override_server=True))
                Utils.messagebox('SMB3X', 'Room details saved. Reopen the same player file to reconnect. Your checkpoint is retained.')
                return
            except Exception:
                logging.exception('Room details were not updated')
        Utils.messagebox('SMB3X - Action needed', str(exc) + '\n\nExisting saves are retained. Logs: ' + str(base / 'sessions'), error=True)
        raise

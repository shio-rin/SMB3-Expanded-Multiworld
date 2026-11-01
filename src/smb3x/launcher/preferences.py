# SPDX-License-Identifier: MPL-2.0
"""launcher / preferences implementation for managed SMB3X sessions."""
from pathlib import Path
import json, time, uuid
from copy import deepcopy
from contextlib import contextmanager
from ..shared.resources import RESOURCE_ROOT as ROOT
from ..client.persistence.atomic import save_json as atomic
from .dialogs import confirm, select
from ..shared.serialization import fingerprint, read, sha
from .paths import home
from ..shared.emulators import profile, identify, EmulatorCompatibilityError
NES_CORE = 'BizHawk.Emulation.Cores.Nintendo.NES.NES'
CONFIG_SCHEMA = 'm233-core-config-1'
NES_PRESENTATION_KEYS = frozenset(('APU_vol', 'BackgroundColor', 'ClipLeftAndRight', 'DispBackground', 'DispSprites', 'NTSC_BottomLine', 'NTSC_TopLine', 'PAL_BottomLine', 'PAL_TopLine', 'Palette'))
PREFERENCE_KEYS = frozenset(('AllTrollers', 'AllTrollersAnalog', 'AllTrollersAutoFire', 'AllTrollersFeedbacks', 'AcceptBackgroundInput', 'AcceptBackgroundInputControllerOnly', 'HandleAlternateKeyboardLayouts', 'MergeLAndRModifierKeys', 'InputConfigAutoTab', 'HotkeyConfigAutoTab', 'MainWindowMaximized', 'MainWindowPosition', 'MainWindowSize', 'SaveWindowPosition', 'MainFormStayOnTop', 'StartFullscreen', 'ResizeWithFramebuffer', 'TargetDisplayFilter', 'TargetScanlineFilterIntensity', 'TargetZoomFactors', 'SoundBufferSizeMs', 'SoundDevice', 'SoundEnabled', 'SoundEnabledNormal', 'SoundEnabledRWFF', 'SoundOutputMethod', 'SoundVolume', 'SoundVolumeRWFF', 'MuteFrameAdvance', 'VSync', 'VSyncThrottle', 'SoundThrottle', 'ClockThrottle', 'SpeedPercent', 'SpeedPercentAlternate', 'Unthrottled', 'PauseWhenMenuActivated', 'RunInBackground', 'StartPaused', 'FrameSkip', 'OSDMessageDuration', 'MessagesColor', 'AlertMessageColor'))
SAFE_HOTKEYS = frozenset(('Pause', 'Fullscreen', 'Volume Down', 'Volume Up', 'Sound', 'Toggle Sound', 'Display FPS', 'Input Display', 'Frame Counter', 'Lag Counter', 'Toggle Display Nothing'))

def configuration(version='2.10'):
    value = read(ROOT / 'launcher/config' / profile(version)['config'])
    value['PathEntries']['LastRomPath'] = '.'
    value['UpdateAutoCheckEnabled'] = False
    return value

def required_configuration(config, version='2.10'):
    """Versioned checkpoint-critical projection; host preferences are excluded."""
    try:
        return dict(schema=CONFIG_SCHEMA, core=config['PreferredCores']['NES'], core_settings={k: v for k, v in config['CoreSettings'][NES_CORE].items() if k not in NES_PRESENTATION_KEYS}, sync_settings=config['CoreSyncSettings'][NES_CORE], safety={k: config[k] for k in ('AutoLoadLastSaveSlot', 'SingleInstanceMode', 'RunLuaDuringTurbo')}, rewind=config['Rewind']['Enabled'], autoload={k: config[k]['AutoLoad'] for k in ('RecentLua', 'RecentLuaSession', 'RecentRoms', 'RecentMovies')})
    except (KeyError, TypeError, AttributeError) as exc:
        raise EmulatorCompatibilityError('Managed BizHawk core configuration is incomplete at ' + str(exc) + '; original settings and saves were retained') from exc

def validate_configuration(config, version='2.10'):
    if config.get('LastWrittenFrom') != version or config.get('LastWrittenFromDetailed') != 'Version ' + version:
        raise EmulatorCompatibilityError('Managed configuration version differs from BizHawk ' + version + '; keep the original settings and saves')
    required = required_configuration(config, version)
    expected = required_configuration(configuration(version), version)
    if required != expected:
        changes = []

        def differences(a, b, path):
            if isinstance(a, dict) and isinstance(b, dict):
                for key in sorted(a.keys() | b.keys()):
                    differences(a.get(key), b.get(key), path + [key])
            elif a != b:
                changes.append(path)
        differences(required, expected, [])

        def field(path):
            first, *rest = path
            if first == 'core':
                return 'PreferredCores.NES'
            if first in ('core_settings', 'sync_settings'):
                return '.'.join(['CoreSettings' if first == 'core_settings' else 'CoreSyncSettings', NES_CORE, *rest])
            if first == 'rewind':
                return 'Rewind.Enabled'
            if first == 'autoload':
                return '.'.join([*rest, 'AutoLoad'])
            return '.'.join(rest if first == 'safety' else path)
        raise EmulatorCompatibilityError('Managed BizHawk core/sync setting differs: ' + ', '.join((field(x) for x in changes[:5])) + '. Restore these supported settings before reopening; saves and preferences were retained.')
    return required

def preference_values(config, version='2.10'):
    default = configuration(version)
    values = {}
    for key in PREFERENCE_KEYS | {k for k in default if k.startswith('Disp')}:
        if key not in default:
            continue
        value = deepcopy(config.get(key, default[key]))
        if type(value) is not type(default[key]):
            raise ValueError('Invalid BizHawk preference: ' + key)
        values[key] = value
    hotkeys = config.get('HotkeyBindings', {})
    if not isinstance(hotkeys, dict):
        raise ValueError('Invalid BizHawk hotkey preferences')
    values['HotkeyBindings'] = {k: hotkeys.get(k, v) for k, v in default['HotkeyBindings'].items() if k in SAFE_HOTKEYS}
    core = config.get('CoreSettings', {}).get(NES_CORE, {})
    values['CoreSettings'] = {NES_CORE: {k: deepcopy(core.get(k, default['CoreSettings'][NES_CORE][k])) for k in NES_PRESENTATION_KEYS}}
    for key, value in values['CoreSettings'][NES_CORE].items():
        if key != 'Palette' and type(value) is not type(default['CoreSettings'][NES_CORE][key]):
            raise ValueError('Invalid BizHawk presentation setting: CoreSettings.' + NES_CORE + '.' + key)
    palette = values['CoreSettings'][NES_CORE]['Palette']
    # None asks the verified emulator to supply its built-in colors. Explicit
    # palettes remain local user preferences; their bytes are never shipped here.
    if palette is not None and (not isinstance(palette, list) or len(palette) != 64 or any((not isinstance(row, list) or len(row) != 3 or any((type(v) is not int or not 0 <= v <= 255 for v in row)) for row in palette))):
        raise ValueError('Invalid BizHawk presentation setting: CoreSettings.' + NES_CORE + '.Palette')

    def plain(v):
        if isinstance(v, dict):
            return all((isinstance(k, str) and k != '$type' and plain(x) for k, x in v.items()))
        if isinstance(v, list):
            return all((plain(x) for x in v))
        return v is None or type(v) in (str, int, float, bool)
    if not plain(values):
        raise ValueError('Unsupported typed object in BizHawk preferences')
    return values

def apply_preferences(config, values):
    config = deepcopy(config)
    for key, value in values.items():
        if key == 'HotkeyBindings':
            config[key].update(deepcopy(value))
        elif key == 'CoreSettings':
            config[key][NES_CORE].update(deepcopy(value[NES_CORE]))
        else:
            config[key] = deepcopy(value)
    return config

def profile_root(exe):
    selected = identify(exe)
    key = fingerprint(dict(path=str(Path(exe).resolve()).casefold(), revision=selected['revision']))
    return home() / 'bizhawk-profiles' / key

@contextmanager
def profile_lock(root):
    from ..client.persistence.locking import session_lock
    from contextlib import ExitStack
    with ExitStack() as stack:
        for attempt in range(20):
            try:
                stack.enter_context(session_lock(root / 'preferences.lock'))
                break
            except ValueError:
                if attempt == 19:
                    raise ValueError('BizHawk preferences are busy in another game. Existing preferences were retained; reopen shortly.')
                time.sleep(0.05)
        yield

def choose_configuration(exe):
    default = Path(exe).resolve().parent / 'config.ini'
    if default.exists():
        if confirm('Import your BizHawk controller, video and audio preferences from ' + str(default) + '? Choose No if your shortcut uses a different --config file.'):
            return default
    elif confirm('No default BizHawk config.ini was found. Start with supported defaults? Choose No to select your existing configuration.'):
        return None
    return select('Select your existing BizHawk configuration', [('BizHawk configuration', ('.ini', '.json'))])

def initialize_preferences(exe, source):
    root = profile_root(exe)
    root.mkdir(parents=True, exist_ok=True)
    version = identify(exe)['version']
    value = configuration(version) if source is None else json.loads(Path(source).read_text(encoding='utf-8-sig'))
    if value.get('LastWrittenFrom') != version:
        raise ValueError('Import preferences from BizHawk ' + version + ' or choose supported defaults; other versions are retained unchanged')
    values = preference_values(value, version)
    with profile_lock(root):
        path = root / 'preferences.json'
        if not path.exists():
            atomic(path, dict(schema=1, values=values, source=str(source) if source else None, source_sha256=sha(source) if source else None))
    return root

def merge_preferences(root, baseline, working):
    """Three-way leaf merge: a late-closing game cannot overwrite newer edits."""
    conflicts = []

    def merge(before, after, current, path=()):
        if isinstance(before, dict) and isinstance(after, dict) and isinstance(current, dict):
            result = deepcopy(current)
            for key in before.keys() | after.keys():
                if key not in before:
                    if key not in current or current[key] == after[key]:
                        result[key] = deepcopy(after[key])
                    else:
                        conflicts.append('.'.join(path + (key,)))
                elif key not in after:
                    if key in current and current[key] == before[key]:
                        result.pop(key)
                    elif key in current:
                        conflicts.append('.'.join(path + (key,)))
                elif key in current:
                    result[key] = merge(before[key], after[key], current[key], path + (key,))
                elif after[key] != before[key]:
                    conflicts.append('.'.join(path + (key,)))
            return result
        if after == before:
            return current
        if current == before or current == after:
            return deepcopy(after)
        conflicts.append('.'.join(path))
        return current
    with profile_lock(root):
        path = root / 'preferences.json'
        profile = read(path)
        if profile.get('schema') != 1:
            raise ValueError('Unsupported managed BizHawk preferences; original file retained')
        profile['values'] = merge(baseline, working, profile['values'])
        atomic(path, profile)
        if conflicts:
            atomic(root / ('conflict-' + uuid.uuid4().hex + '.json'), dict(conflicts=conflicts, baseline=baseline, attempted=working))
    return conflicts

def collect_preferences(session_root):
    folder = Path(session_root) / 'bizhawk'
    meta = folder / 'launch-preferences.json'
    path = folder / 'config.ini'
    if not meta.exists() or not path.exists():
        return
    previous = read(meta)
    key = previous.get('profile', '')
    if len(key) != 64 or any((c not in '0123456789abcdef' for c in key)):
        raise ValueError('Invalid managed preference profile identity')
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    version = previous.get('emulator_version')
    profile(version)  # Missing/unknown ownership must not be guessed from config.ini.
    validate_configuration(config, version)
    values = preference_values(config, version)
    merge_preferences(home() / 'bizhawk-profiles' / key, previous['baseline'], values)
    atomic(meta, {**previous, 'baseline': values})

def managed_configuration(session_root, exe):
    version = identify(exe)['version']
    root = profile_root(exe)
    if not (root / 'preferences.json').exists():
        initialize_preferences(exe, choose_configuration(exe))
    collect_preferences(session_root)
    with profile_lock(root):
        profile = read(root / 'preferences.json')
        if profile.get('schema') != 1:
            raise ValueError('Unsupported managed BizHawk preferences; original file retained')
        values = preference_values(apply_preferences(configuration(version), profile['values']), version)
    config = apply_preferences(configuration(version), values)
    validate_configuration(config, version)
    folder = Path(session_root) / 'bizhawk'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'config.ini'
    atomic(path, config)
    atomic(folder / 'launch-preferences.json', dict(schema=1, profile=root.name, emulator_version=version, baseline=values))
    return (path, config)

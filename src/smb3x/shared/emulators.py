# SPDX-License-Identifier: MPL-2.0
"""Reviewed emulator contracts, shared by launch and checkpoint validation.

Profile values come from packaged resources, never a State file or a reported
version string. Historical runtimes retain their own original contracts.
"""
from pathlib import Path
import json
import hashlib
import xml.etree.ElementTree as ET
from .resources import RESOURCE_ROOT
from .serialization import sha


def profiles():
    return json.loads((RESOURCE_ROOT / 'launcher/config/emulators.json').read_text())


def profile(version):
    try:
        return profiles()[version]
    except (KeyError, TypeError) as exc:
        raise ValueError('Unsupported emulator profile; verified versions: ' + ', '.join(profiles())) from exc


class EmulatorCompatibilityError(ValueError):
    """An actionable, known installation/session compatibility failure."""


def loader_policy(raw):
    """Pin CLR startup/loading policy, not appSettings or GC preferences."""
    def node(element):
        return [element.tag, sorted(element.attrib.items()),
                (element.text or '').strip(), [node(child) for child in element]]
    root = ET.fromstring(raw)
    policy = [root.tag, sorted(root.attrib.items()), []]
    for element in root:
        if element.tag in ('startup', 'runtime'):
            value = node(element)
            if element.tag == 'runtime':
                value[3] = [child for child in value[3] if not child[0].startswith('gc')]
            policy[2].append(value)
    return hashlib.sha256(json.dumps(policy, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def _verify_files(exe, selected, names):
    missing, modified, collisions = [], [], []
    for name in names:
        expected = selected['files'][name]
        path = exe if name == 'EmuHawk.exe' else exe.parent / name
        if not path.is_file():
            missing.append(name)
        elif sha(path) != expected:
            modified.append(name)
        if name.startswith('dll/'):
            # CLR application-base probing precedes AssemblyResolve's dll/ path;
            # Win32 native DLL search also checks the executable directory first.
            # Check only names capable of shadowing a dependency, never all extras.
            base = Path(name).name
            stem = Path(base).stem
            probes = [base]
            if name in selected['managed_files']:
                probes += [stem + '/' + base, stem + '.exe', stem + '/' + stem + '.exe']
            for relative in probes:
                candidate = exe.parent / relative
                if candidate.is_file() and sha(candidate) != expected:
                    collisions.append(relative)
    return [('Missing critical files', missing), ('Modified critical files', modified),
            ('Conflicting dependency copies', collisions)]


def identify(exe):
    """Verify the reviewed NES/client/Lua closure; unrelated files are not inputs.

    `files` remains the immutable historical profile fingerprint for sessions.
    `validation_files` is the separately reviewed execution dependency set.
    """
    exe = Path(exe).resolve()
    try:
        executable_hash = sha(exe)
    except OSError as exc:
        raise EmulatorCompatibilityError('Cannot read the selected BizHawk executable: ' + str(exe)
                                        + '. Supported versions: ' + ', '.join(profiles())) from exc
    found = next((p for p in profiles().values() if p['files']['EmuHawk.exe'] == executable_hash), None)
    if found is None:
        raise EmulatorCompatibilityError('Unrecognized or modified BizHawk executable. Supported Windows x64 versions: '
                                          + ', '.join(profiles()) + '. Existing files and saves are retained.')
    try:
        differences = _verify_files(exe, found, found['validation_files'])
        config = Path(str(exe) + '.config')
        if not config.is_file() or loader_policy(config.read_bytes()) != found['loader_config_sha256']:
            differences.append(('Incompatible CLR loader configuration', [config.name]))
    except (OSError, ET.ParseError) as exc:
        raise EmulatorCompatibilityError('Cannot verify a critical BizHawk dependency or loader configuration: '
                                        + str(exc) + '. Supported versions: ' + ', '.join(profiles())) from exc
    details = [label + ' (' + str(len(paths)) + '): ' + ', '.join(paths)
               for label, paths in differences if paths]
    if details:
        raise EmulatorCompatibilityError('BizHawk ' + found['version'] + ' critical runtime integrity mismatch.\n'
                         + '\n'.join(details)
                         + '\nSupported versions: ' + ', '.join(profiles())
                         + '. Select an installation with matching critical components. '
                           'Unrelated cores, plugins and language files may remain. Existing saves are retained.')
    return found


def verify_frontend(exe, config):
    """Check OpenAL only when selected, not when the player uses XAudio2.

    These are specific load targets of OpenALSoundOutput, not an extras allowlist.
    """
    if config.get('SoundOutputMethod') != 2:
        return
    exe = Path(exe).resolve()
    selected = identify(exe)
    try:
        differences = _verify_files(exe, selected, selected['frontend_files'])
    except OSError as exc:
        raise EmulatorCompatibilityError('Cannot read a selected OpenAL audio dependency: ' + str(exc)) from exc
    details = [label + ': ' + ', '.join(paths) for label, paths in differences if paths]
    if details:
        raise EmulatorCompatibilityError('Selected OpenAL audio dependencies failed verification.\n'
                                        + '\n'.join(details) + '\nUse matching OpenAL components or select '
                                        'XAudio2 in your audio preferences. Existing saves are retained.')


def bound_profile(emulator):
    """Resolve only the trusted launcher binding, not claims inside a savestate."""
    selected = profile(emulator.get('profile'))
    if emulator.get('revision') != selected['revision'] or emulator.get('core') != 'NesHawk':
        raise ValueError('Checkpoint emulator profile/revision/core mismatch')
    return selected

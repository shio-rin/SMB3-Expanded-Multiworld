# SPDX-License-Identifier: MPL-2.0
"""Reviewed emulator contracts, shared by launch and checkpoint validation.

Profile values come from packaged resources, never a State file or a reported
version string. Historical runtimes retain their own original contracts.
"""
from pathlib import Path
import json
from .resources import RESOURCE_ROOT
from .serialization import sha


def profiles():
    return json.loads((RESOURCE_ROOT / 'launcher/config/emulators.json').read_text())


def profile(version):
    try:
        return profiles()[version]
    except (KeyError, TypeError) as exc:
        raise ValueError('Unsupported emulator profile; verified versions: ' + ', '.join(profiles())) from exc


def identify(exe):
    """Verify official executable and complete DLL set before using its settings."""
    exe = Path(exe).resolve()
    executable_hash = sha(exe)
    found = next((p for p in profiles().values() if p['files']['EmuHawk.exe'] == executable_hash), None)
    if found is None:
        raise ValueError('Unrecognized or modified BizHawk executable. Verified Windows x64 releases: '
                         + ', '.join(profiles()) + '. Select a complete unmodified official installation; keep existing saves.')
    actual = {'EmuHawk.exe': executable_hash}
    actual.update({p.relative_to(exe.parent).as_posix(): sha(p)
                   for p in sorted((exe.parent / 'dll').rglob('*')) if p.is_file()})
    if actual != found['files']:
        differing = sorted(k for k in actual.keys() | found['files'].keys()
                           if actual.get(k) != found['files'].get(k))
        raise ValueError('BizHawk ' + found['version'] + ' core/runtime integrity mismatch: '
                         + ', '.join(differing[:3]) + '. Select its complete official installation; keep existing saves.')
    return found


def bound_profile(emulator):
    """Resolve only the trusted launcher binding, not claims inside a savestate."""
    selected = profile(emulator.get('profile'))
    if emulator.get('revision') != selected['revision'] or emulator.get('core') != 'NesHawk':
        raise ValueError('Checkpoint emulator profile/revision/core mismatch')
    return selected

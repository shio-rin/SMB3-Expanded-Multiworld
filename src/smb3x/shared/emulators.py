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
    """Verify required runtime files and any explicitly approved language resources.

    Optional assemblies are exact path/hash pairs for this profile's dependency
    version. A resources.dll filename alone never grants an integrity exemption.
    They do not alter the required-file identity stored in existing sessions.
    """
    exe = Path(exe).resolve()
    executable_hash = sha(exe)
    found = next((p for p in profiles().values() if p['files']['EmuHawk.exe'] == executable_hash), None)
    if found is None:
        raise ValueError('Unrecognized or modified BizHawk executable. Verified Windows x64 releases: '
                         + ', '.join(profiles()) + '. Select a complete unmodified official installation; keep existing saves.')
    actual = {'EmuHawk.exe': executable_hash}
    actual.update({p.relative_to(exe.parent).as_posix(): sha(p)
                   for p in sorted((exe.parent / 'dll').rglob('*')) if p.is_file()})
    required = found['files']
    optional = found.get('optional_files', {})
    differences = {
        'Missing required files': sorted(required.keys() - actual.keys()),
        'Modified required files': sorted(k for k in required.keys() & actual.keys()
                                          if actual[k] != required[k]),
        'Modified optional language resources': sorted(k for k in optional.keys() & actual.keys()
                                                       if actual[k] != optional[k]),
        'Unapproved additional files': sorted(actual.keys() - required.keys() - optional.keys()),
    }
    details = [label + ' (' + str(len(paths)) + '): ' + ', '.join(paths)
               for label, paths in differences.items() if paths]
    if details:
        raise ValueError('BizHawk ' + found['version'] + ' core/runtime integrity mismatch.\n'
                         + '\n'.join(details)
                         + '\nSelect a complete official installation in a separate folder; do not mix versions.'
                           ' Only hash-verified language resources are optional. Keep existing saves.')
    return found


def bound_profile(emulator):
    """Resolve only the trusted launcher binding, not claims inside a savestate."""
    selected = profile(emulator.get('profile'))
    if emulator.get('revision') != selected['revision'] or emulator.get('core') != 'NesHawk':
        raise ValueError('Checkpoint emulator profile/revision/core mismatch')
    return selected

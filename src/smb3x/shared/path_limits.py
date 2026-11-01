# SPDX-License-Identifier: MPL-2.0
"""Conservative Windows paths shared by Python and pinned BizHawk 2.10.

The emulator is not assumed to support extended-length paths just because a
Python process might. Count UTF-16 units, including surrogate pairs. Refuse
before creating session state; never relocate or shorten an existing identity.
"""
import os
from pathlib import Path

def validate_file_path(path):
    path = Path(path).resolve()
    if os.name != 'nt':
        return path
    units = lambda value: len(str(value).encode('utf-16-le')) // 2
    if units(path) >= 260 or units(path.parent) > 247:
        raise ValueError('The managed SMB3X path is too long for supported Windows/BizHawk operation: ' + str(path) + '. Use a shorter managed root for a new session before launch. Existing sessions and saves were retained; do not move them or shorten their identities.')
    if any((units(part) > 255 for part in path.parts)):
        raise ValueError('A managed path component exceeds the Windows limit: ' + str(path))
    return path

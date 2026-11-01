# SPDX-License-Identifier: MPL-2.0
"""launcher / paths implementation for managed SMB3X sessions."""
from pathlib import Path
import os
from ..shared.resources import RESOURCE_ROOT as ROOT

def home():
    return Path(os.environ.get('SMB3X_MANAGED_HOME', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'SMB3XAP')))
ROM_FILENAME = 'SMB3X - Expanded Multiworld.nes'

def preflight_session(root):
    """Check the longest real layouts before preparation or native activation.

    UUIDs have 32 characters and receipt keys have 64. Checking their full sizes
    makes the result independent of a random run/generation identifier.
    """
    from ..shared.path_limits import validate_file_path
    token = 'x' * 32
    receipt = 'x' * 64 + '.json'
    paths = [root / 'prepare-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/game' / ROM_FILENAME, root / 'prepared/game' / ROM_FILENAME, root / 'bizhawk/launch-preferences.json', root / 'saves/runs' / token / 'deliveries' / receipt, root / 'saves/runs' / token / 'worlds' / receipt, root / 'saves/runs' / token / 'Start-SMB3.lua', root / 'saves/candidates' / token / 'controller.json', root / 'saves/candidates' / token / 'native.State', root / 'saves/checkpoints' / token / 'native.State', root / 'saves/epoch-history' / (token + '.json'), home() / 'bizhawk-profiles' / ('x' * 64) / ('conflict-' + token + '.json')]
    for path in paths:
        validate_file_path(path)
        validate_file_path(path.parent / ('j-' + 'x' * 8 + '.pending'))

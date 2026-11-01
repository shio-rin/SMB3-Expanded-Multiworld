# SPDX-License-Identifier: MPL-2.0
"""launcher / player_file implementation for managed SMB3X sessions."""
from zipfile import ZipFile
import hashlib, json
from ..shared.resources import RESOURCE_ROOT as ROOT

def container(path):
    with ZipFile(path) as z:
        if len(z.namelist()) != 2 or set(z.namelist()) != {'archipelago.json', 'session.json'}:
            raise ValueError('Invalid SMB3X player file members; download the complete player file again')
        if any((i.file_size > 2000000 for i in z.infolist())):
            raise ValueError('Oversized SMB3X player file')
        m = json.loads(z.read('archipelago.json'))
        raw = z.read('session.json')
        v = json.loads(raw)
    if (v.get('slot_data', {}).get('game'), v.get('slot_data', {}).get('namespace'), v.get('slot_data', {}).get('identity_contract')) != ('Super Mario Bros. 3: Expanded Multiworld', 'smb3x', 'smb3x-fresh-1'):
        raise ValueError('Historical SMB3 files cannot be opened or migrated by SMB3X')
    if m.get('game') != 'Super Mario Bros. 3: Expanded Multiworld' or m.get('smb3x_container') != 1 or m.get('patch') != 'm26-native-2' or (m.get('persistence') != 3):
        raise ValueError('Unsupported SMB3X player/build version; install its matching APWorld')
    if m.get('session_sha256') != hashlib.sha256(raw).hexdigest() or v.get('format') != 'smb3x-player-1':
        raise ValueError('SMB3X player data integrity mismatch')
    if m.get('resource_id') != v.get('resource_id') or not isinstance(m.get('resource_id'), str) or len(m['resource_id']) != 64 or any((c not in '0123456789abcdef' for c in m['resource_id'])):
        raise ValueError('Invalid SMB3 resource identity')
    if m.get('player') != v.get('slot') or m.get('player_name') != v.get('slot_name'):
        raise ValueError('SMB3X player identity mismatch')
    from ..shared.identity import Identity
    Identity(v['seed_name'], v['team'], v['slot'])
    return (m, v)

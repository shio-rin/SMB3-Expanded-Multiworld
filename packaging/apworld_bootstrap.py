"""Load verified resources from one conventional smb3 APWorld directory."""
from pathlib import Path as _Path
from zipfile import ZipFile as _ZipFile
import hashlib as _hashlib
import json as _json
import os as _os
import sys as _sys
import uuid as _uuid
import time as _time
import Utils as _Utils

if tuple(_Utils.version_tuple) != (0, 6, 8):
    raise RuntimeError('This SMB3X APWorld targets official Archipelago 0.6.8')
_archive = _Path(__loader__.archive)
with _ZipFile(_archive) as _z:
    _inventory_bytes = _z.read('smb3x/resources.json')
    _inventory = _json.loads(_inventory_bytes)
    RESOURCE_ID = _hashlib.sha256(_inventory_bytes).hexdigest()
    _home = _Path(_os.environ.get('SMB3X_MANAGED_HOME', str(_Path(_os.environ.get('LOCALAPPDATA', _Path.home()))/'SMB3XAP')))
    _cache = _home/'cache';_cache.mkdir(parents=True,exist_ok=True)
    _root = _cache/RESOURCE_ID[:20]
    if not _root.exists():
        _pending = _cache/('pending-'+_uuid.uuid4().hex);_pending.mkdir()
        for _name,_digest in _inventory.items():
            _dest=(_pending/_name).resolve()
            if not _dest.is_relative_to(_pending.resolve()):raise RuntimeError('Unsafe SMB3X resource path')
            _data=_z.read('smb3x/resources/'+_name)
            if _hashlib.sha256(_data).hexdigest()!=_digest:raise RuntimeError('SMB3X resource hash mismatch: '+_name)
            _dest.parent.mkdir(parents=True,exist_ok=True);_dest.write_bytes(_data)
        (_pending/'resource-manifest.json').write_bytes(_inventory_bytes)
        # Retry only the same fully written sibling directory rename. Never
        # remove/replace a destination. Every published member is verified below.
        for _attempt in range(5):
            try:
                _pending.rename(_root)
                break
            except FileExistsError:
                break # A concurrent publisher must pass complete verification.
            except OSError as _error:
                if _root.exists():
                    break # Verify a concurrently published destination below.
                if getattr(_error,'winerror',None) not in (5,32,33) or _attempt==4:
                    raise
                _time.sleep((.05,.10,.20,.40)[_attempt])
    for _name,_digest in _inventory.items():
        _dest=(_root/_name).resolve()
        if not _dest.is_relative_to(_root.resolve()) or not _dest.is_file() or _hashlib.sha256(_dest.read_bytes()).hexdigest()!=_digest:
            raise RuntimeError('SMB3X cached resource missing or changed: '+_name+'; preserve saves and reinstall the matching APWorld')

RESOURCE_ROOT = _root
__path__ = [str(_root)]
from .world.registration import SMB3World, register_resources
register_resources(RESOURCE_ID, RESOURCE_ROOT)

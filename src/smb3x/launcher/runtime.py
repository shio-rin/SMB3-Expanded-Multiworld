# SPDX-License-Identifier: MPL-2.0
"""Resource-owned Python packages and isolated execution of older exact caches."""
from pathlib import Path
import hashlib
import importlib
import importlib.util
import importlib.machinery
import json
import sys
LAYOUT = 'smb3x-python-1'

def verify(root, resource_id):
    root = Path(root).resolve()
    if not isinstance(resource_id, str) or len(resource_id) != 64 or any((c not in '0123456789abcdef' for c in resource_id)):
        raise ValueError('Invalid SMB3X cached resource identity')
    raw = (root / 'resource-manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != resource_id:
        raise ValueError('Matching SMB3X cache identity changed')
    inventory = json.loads(raw)
    for name, digest in inventory.items():
        target = (root / name).resolve()
        if not target.is_relative_to(root) or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('Matching SMB3X cached resource missing/changed: ' + name + '; preserve saves and install its matching APWorld')
    return (root, inventory)

def load_player(root, resource_id):
    root, inventory = verify(root, resource_id)
    if '__init__.py' not in inventory:
        raise ValueError('This cache requires its original historical runtime')
    name = 'smb3x_runtime_' + resource_id
    package = sys.modules.get(name)
    if package is None:
        spec = importlib.util.spec_from_file_location(name, root / '__init__.py', submodule_search_locations=[str(root)])
        package = importlib.util.module_from_spec(spec)
        sys.modules[name] = package
        spec.loader.exec_module(package)
        package._smb3x_resource_id = resource_id
    elif Path(getattr(package, '__file__', '')).resolve() != root / '__init__.py' or getattr(package, '_smb3x_resource_id', None) != resource_id:
        raise ValueError('Foreign module owns this SMB3X resource namespace; restart Launcher')
    if getattr(package, 'RUNTIME_LAYOUT', None) != LAYOUT:
        raise ValueError('Unsupported SMB3X Python runtime layout')
    entry = getattr(package, 'PLAYER_MODULE', 'tools.player_m233')
    if entry not in ('tools.player_m233', 'launcher.player'):
        raise ValueError('Unsupported SMB3X player entry point')
    player = importlib.import_module(name + '.' + entry)
    if Path(player.__file__).resolve() != root / (entry.replace('.', '/') + '.py'):
        raise ValueError('SMB3X player module ownership mismatch')
    return player

def _historical_worker_impl(args, root, resource_id):
    root, inventory = verify(root, resource_id)
    if '__init__.py' in inventory:
        raise ValueError('Historical dispatch refused a new-layout cache')
    for name, module in tuple(sys.modules.items()):
        if name in ('tools', 'client') or name.startswith(('tools.', 'client.')):
            file = getattr(module, '__file__', None)
            paths = list(getattr(module, '__path__', ()))
            if not (file and Path(file).resolve().is_relative_to(root)) and (not (paths and all((Path(p).resolve().is_relative_to(root) for p in paths)))):
                raise ValueError('Another world owns a historical runtime module. Open this older player with its matching APWorld in a separate installation; saves are retained.')
    for name in ('tools', 'client'):
        if name not in sys.modules:
            spec = importlib.machinery.PathFinder.find_spec(name, [str(root)])
            if spec is None:
                raise ValueError('Matching historical cache lacks ' + name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            if spec.loader:
                spec.loader.exec_module(module)
    player = importlib.import_module('tools.player_m233')
    if Path(player.__file__).resolve() != root / 'tools/player_m233.py':
        raise ValueError('Historical SMB3X player ownership mismatch')
    return player.main(args, root, resource_id)

def _historical_worker(args, root, resource_id):
    try:
        return _historical_worker_impl(args, root, resource_id)
    except Exception as exc:
        import logging
        import Utils
        logging.exception('SMB3X historical runtime stopped; original files retained')
        Utils.messagebox('SMB3X - Action needed', str(exc) + "\n\nExisting saves are retained. Use this older player's matching APWorld and cache; do not migrate it.", error=True)
        raise

def launch_historical(args, root, resource_id):
    verify(root, resource_id)
    from worlds.LauncherComponents import launch_subprocess
    return launch_subprocess(_historical_worker, name='SMB3X matching historical runtime', args=(tuple(args), str(root), resource_id))

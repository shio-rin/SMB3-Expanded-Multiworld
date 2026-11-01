# SPDX-License-Identifier: MPL-2.0
"""launcher / history implementation for managed SMB3X sessions."""
import json
from ..shared.resources import RESOURCE_ROOT as ROOT
from .paths import home
from .runtime import verify as verify_resources

def cached_runtime(args, resource_id):
    """An APWorld update must not change the code bound to an existing save."""
    import importlib
    if not isinstance(resource_id, str) or len(resource_id) != 64 or any((c not in '0123456789abcdef' for c in resource_id)):
        raise ValueError('Invalid SMB3 resource identity')
    cache = (home() / 'cache').resolve()
    root = cache / resource_id[:20]
    if not root.resolve().is_relative_to(cache):
        raise ValueError('Unsafe cached runtime path')
    if not root.exists():
        raise ValueError('Matching saved-game resources are unavailable. Install the APWorld version for this player file; existing saves are retained.')
    verify_resources(root, resource_id)
    from .runtime import load_player, launch_historical
    if '__init__.py' in json.loads((root / 'resource-manifest.json').read_bytes()):
        return load_player(root, resource_id).main(args, root, resource_id)
    return launch_historical(tuple(args), root, resource_id)

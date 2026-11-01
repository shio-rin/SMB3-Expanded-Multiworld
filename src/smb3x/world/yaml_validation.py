# SPDX-License-Identifier: MPL-2.0
"""Pinned AP0.6.8 option adapter for keys the framework otherwise ignores.

Generate has no per-world raw-YAML hook. Import its named module explicitly so
worlds-first loading also installs validation. The frozen executable may own a
second Generate namespace; patch its own handler as well. No import hooks, option
fields or random draws are introduced. Linked/triggered mappings reach this same
handler after AP has expanded them.
"""
from functools import wraps
from importlib import import_module
import inspect
import sys
GAME = 'Super Mario Bros. 3: Expanded Multiworld'
REMOVED = frozenset(('shuffle_pool', 'balanced_policy'))
MESSAGE = 'Legacy12 and Strict Difficulty were removed. Delete shuffle_pool and balanced_policy from this YAML; choose level_shuffle: vanilla, balanced, or compatible.'

def install_guard():
    generate = import_module('Generate')
    candidates = [generate]
    for module in tuple(sys.modules.values()):
        namespace = getattr(module, '__dict__', {})
        roll = namespace.get('roll_settings')
        if not callable(roll):
            continue
        code = getattr(inspect.unwrap(roll), '__code__', None)
        if code and code.co_filename.replace('\\', '/').rsplit('/', 1)[-1] == 'Generate.py':
            candidates.append(module)
    for module in candidates:
        original = getattr(module, 'handle_option', None)
        if not callable(original) or getattr(original, '_smb3x_removed_keys', False):
            continue

        @wraps(original)
        def handle(ret, game_weights, *args, _original=original, **kwargs):
            if ret.game == GAME and REMOVED.intersection(game_weights):
                raise ValueError(MESSAGE)
            return _original(ret, game_weights, *args, **kwargs)
        handle._smb3x_removed_keys = True
        module.handle_option = handle

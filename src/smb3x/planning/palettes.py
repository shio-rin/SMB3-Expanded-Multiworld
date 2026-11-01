# SPDX-License-Identifier: MPL-2.0
"""Approved palette selector and guarded fortress contrast corrections."""
import copy
from . import palette_library as P
CORRECTIONS = {'fortress-indigo': {'index': 5, 'old': 15, 'new': 33}, 'fortress-ember': {'index': 5, 'old': 15, 'new': 39}, 'fortress-moss': {'index': 5, 'old': 15, 'new': 43}}

def corrected(themes):
    result = copy.deepcopy(themes)
    for theme in result:
        if theme['id'] in CORRECTIONS:
            edit = CORRECTIONS[theme['id']]
            if theme['background'][edit['index']] != edit['old']:
                raise ValueError('fortress definition source mismatch')
            theme['background'][edit['index']] = edit['new']
    return result

def plan(seed, mode='atmospheric'):
    if mode not in ('original', 'atmospheric', 'full'):
        raise ValueError('Unsupported palette_mode')
    subset = [t['id'] for t in P.THEMES if t.get('kind', 'atmospheric') == 'atmospheric']
    result = P.plan(seed, original_percent=100 if mode == 'original' else 20, theme_subset=subset if mode == 'atmospheric' else None)
    result.pop('sha256')
    result['release_mode'] = mode
    for row in result['areas']:
        row['human_approval'] = 'M20 accepted / M24 approved by user' if row['theme'] else 'native'
        row['technical_status'] = 'M24 native evidence retained; integrated source verified'
    result['sha256'] = P.fingerprint(result)
    result.pop('sha256')
    result['definition_revision'] = 'm242-fortress-contrast-1'
    result['definition_corrections'] = CORRECTIONS
    result['sha256'] = P.fingerprint(result)
    return result

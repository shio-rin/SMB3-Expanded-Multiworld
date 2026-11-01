# SPDX-License-Identifier: MPL-2.0
"""Boss-only muted scenery applications; approved/shared definitions stay exact."""
from pathlib import Path
import copy
from . import special_palettes
P = vars(special_palettes)
VERSION = 'm24-koopaling-muted-1'
DARK = {'fortress-indigo': 1, 'fortress-ember': 6, 'military-crimson': 6, 'fortress-moss': 11}
THEMES = []
for parent, color in DARK.items():
    t = copy.deepcopy(P['BY_ID'][parent])
    t.update(id='koopaling-muted-' + parent, parent=parent, name=t['name'] + ' (muted boss scenery)')
    t['background'][5:8] = [15, color, 15]
    THEMES.append(t)
BY_PARENT = {t['parent']: t for t in THEMES}

def render_id(theme, category):
    return BY_PARENT[theme]['id'] if category == 'airship-boss' and theme in BY_PARENT else theme

def background(theme, category):
    if category == 'airship-boss' and theme in BY_PARENT:
        return list(BY_PARENT[theme]['background'])
    return list(P['BY_ID'][theme]['background'])

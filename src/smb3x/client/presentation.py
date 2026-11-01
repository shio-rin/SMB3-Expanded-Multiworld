# SPDX-License-Identifier: MPL-2.0
"""Read-only receipt-derived view. No journal mutation or native commands."""
from ..shared.progression import validate
from ..shared.location_signals import profile_rows

def snapshot(state, config, goal, connected):
    config = validate(config)
    rows = profile_rows('m242', config)
    return dict(version=1, session=state.identity.key, binding=state.registry, connected=bool(connected), unlock_mask=state.unlock_mask, hammers=state.progression['hammers'], stars=state.progression['stars'], pending=len(state.pending), checks=state.check_counts(), totals=[sum((r['world'] == w for r in rows)) for w in range(1, 9)], required=config['star_fragments_required'] if config['star_hunt_mode'] != 'off' else 0, gate=config['star_hunt_mode'], hammer_mode=config['hammer_mode'], goal=goal)

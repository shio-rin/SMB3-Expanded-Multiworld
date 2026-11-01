# SPDX-License-Identifier: MPL-2.0
from ..shared.progression import validate

def settings(world):
    o = world.options
    return validate(dict(hammer_mode=o.hammer_mode.current_key, star_hunt_mode=o.star_hunt_mode.current_key, star_fragments_required=o.star_fragments_required.value, star_fragments_total=o.star_fragments_total.value, fortress_keys=o.fortress_keys.current_key, reward_visual_style=o.reward_visual_style.current_key, inventory_mode=o.inventory_mode.current_key))

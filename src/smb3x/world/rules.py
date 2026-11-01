# SPDX-License-Identifier: MPL-2.0
from .regions import event_name, checked_event


def set_rules(world):
    player = world.player
    goal = world.options.goal.current_key

    def complete(state):
        if not state.has('M19.1 confirmed ending', player):
            return False
        if goal == 'all_koopalings':
            return all((state.has(event_name(w, 'airship'), player) for w in range(1, 8)))
        if goal == 'all_locations':
            return all((state.has(checked_event(r), player) for r in world.locations))
        return goal == 'standard'

    world.multiworld.completion_condition[player] = complete

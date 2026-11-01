# SPDX-License-Identifier: MPL-2.0
"""Pure goal predicate. Inputs are native durable evidence and SERVER checks.

Inventory insertion acknowledgments are deliberately absent from this API.
The caller must bind goal/enabled IDs into its immutable slot/build identity.
"""
GOALS = ('standard', 'all_koopalings', 'all_locations')

def validate_goal(value):
    if not isinstance(value, str) or value not in GOALS:
        raise ValueError('Unknown victory setting')
    return value

def satisfied(goal, ending, checked, enabled, airships):
    validate_goal(goal)
    if ending != {'version': 1, 'phase': 3}:
        return False
    enabled, checked, airships = (set(enabled), set(checked), set(airships))
    if goal == 'standard':
        return True
    if goal == 'all_koopalings':
        if len(airships) != 7 or not airships <= enabled:
            raise ValueError('All Koopalings requires seven distinct enabled airships')
        return airships <= checked
    return enabled <= checked

# SPDX-License-Identifier: MPL-2.0
"""Pure configuration contract, shared by APWorld and the local client."""
DEFAULTS = dict(hammer_mode='legacy', star_hunt_mode='off', star_fragments_required=12, star_fragments_total=20, fortress_keys='off', reward_visual_style='mystery', inventory_mode='vanilla')
HAMMERS = {2: 'Desert Hammer', 3: 'Water Hammer', 4: 'Giant Hammer', 6: 'Ice Hammer'}

def validate(config=None, location_count=None):
    result = dict(DEFAULTS)
    if config is not None:
        if not isinstance(config, dict) or set(config) - set(DEFAULTS):
            raise ValueError('Unknown progression settings')
        result.update(config)
    if result['inventory_mode'] not in ('vanilla', 'stacked'):
        raise ValueError('Inventory mode must be vanilla or stacked')
    if result['reward_visual_style'] not in ('vanilla', 'mystery'):
        raise ValueError('Reward visuals must be vanilla or mystery')
    if result['hammer_mode'] not in ('legacy', 'regional'):
        raise ValueError('Hammer mode must be legacy or regional')
    if result['star_hunt_mode'] not in ('off', 'world_8', 'bowser'):
        raise ValueError('Star Hunt must be off, world_8 or bowser')
    if result['fortress_keys'] != 'off':
        raise ValueError('Fortress Keys are not yet supported by verified native routes')
    required, total = (result['star_fragments_required'], result['star_fragments_total'])
    if type(required) is not int or type(total) is not int or (not 1 <= required <= total <= 255):
        raise ValueError('Star Fragments require 1 <= required <= total <= 255')
    mandatory = 7 + (4 if result['hammer_mode'] == 'regional' else 1)
    if location_count is None:
        location_count = 126
    if result['star_hunt_mode'] != 'off' and total + mandatory > location_count:
        raise ValueError(f'Star Fragment total exceeds pool capacity: maximum {location_count - mandatory}')
    if result['star_hunt_mode'] == 'world_8' and required > 100:
        raise ValueError('World8 gate requires at most100 fragments: reserve seven Passes outside its eleven checks')
    return result

def native_bytes(config=None):
    c = validate(config)
    return bytes([int(c['hammer_mode'] == 'regional'), ('off', 'world_8', 'bowser').index(c['star_hunt_mode']), c['star_fragments_required'] if c['star_hunt_mode'] != 'off' else 0, c['star_fragments_total'] if c['star_hunt_mode'] != 'off' else 0])

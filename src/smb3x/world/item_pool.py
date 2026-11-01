# SPDX-License-Identifier: MPL-2.0
from ..shared.resources import DATA
from ..shared.progression import validate, HAMMERS
from ..shared.locations import ACTIVE
from BaseClasses import ItemClassification, Region
from .types import SMB3Item, SMB3Location
from hashlib import sha256
import json
from .settings import settings
from ..shared.effects import SPECS, replacement_plan
ITEMS = {r['name']: r for r in json.loads((DATA / 'items_m191.json').read_bytes())}
ITEM_IDS = {name: int(row['id'], 16) for name, row in ITEMS.items()}
PASSES = tuple((f'World {w} Pass' for w in range(2, 9)))
EFFECT_ITEMS = {value[0]: (code, value[2]) for code, value in SPECS.items()}

def create_item(world, name):
    if name in EFFECT_ITEMS:
        code, trap = EFFECT_ITEMS[name]
        return SMB3Item(name, ItemClassification.trap if trap else ItemClassification.useful, code, world.player)
    if name not in ITEMS:
        raise ValueError('Unknown item')
    classification = ItemClassification.progression if name in (*PASSES, *HAMMERS.values(), 'Star Fragment') else ItemClassification.filler if name == '1-Up' else ItemClassification.useful
    return SMB3Item(name, classification, ITEM_IDS[name], world.player)

def create_items(world):
    start = len(world.multiworld.itempool)
    c = settings(world)
    mandatory = list(PASSES) + list(HAMMERS.values()) if c['hammer_mode'] == 'regional' else [*PASSES, 'Overworld Hammer']
    if c['star_hunt_mode'] != 'off':
        mandatory += ['Star Fragment'] * c['star_fragments_total']
    if world.options.reward_pool.value == 1:
        if c['star_hunt_mode'] != 'off' and c['star_fragments_total'] > 8:
            raise ValueError('The short fixed development route supports at most8 fragments; use weighted rewards for larger hunts')
        early = ['World 2 Pass'] + (['Desert Hammer'] if c['hammer_mode'] == 'regional' else []) + ['World 8 Pass']
        early += ['Star Fragment'] * (c['star_fragments_total'] if c['star_hunt_mode'] != 'off' else 0)
        rewards = early + [n for n in mandatory if n not in early]
        rewards += ['Super Leaf'] * (len(world.locations) - len(rewards))
        targets = {next((i for i, r in enumerate(world.locations) if r['world'] == 1 and r['stage'] == stage)): name for stage, name in [('house-1', 'Super Leaf'), ('encounter-2', 'Super Leaf'), ('1-1', 'Super Leaf'), ('house-2', 'Fire Flower'), ('1-2', 'Super Leaf')]}
        for target, name in targets.items():
            spare = next((i for i, r in enumerate(rewards) if r == 'Super Leaf' and i not in targets))
            rewards[spare] = rewards[target]
            rewards[target] = name
        entry = next((i for i, r in enumerate(world.locations) if r['world'] == 1 and r['stage'] == '1-2'))
        origin = rewards.index('World 2 Pass')
        rewards[entry], rewards[origin] = (rewards[origin], rewards[entry])
        for row, reward in zip(world.locations, rewards):
            world.multiworld.get_location(row['name'], world.player).place_locked_item(create_item(world, reward))
    else:
        names = [n for n, r in ITEMS.items() if r['weight'] and (n != 'Overworld Hammer' or c['hammer_mode'] == 'legacy')]
        rewards = mandatory + world.random.choices(names, weights=[ITEMS[n]['weight'] for n in names], k=len(world.locations) - len(mandatory))
        world.multiworld.itempool.extend((create_item(world, n) for n in rewards))
    pool = world.multiworld.itempool[start:]
    positions, world.effect_pool_report = replacement_plan([item.name for item in pool], {i for i, item in enumerate(pool) if item.advancement or item.player != world.player}, world.options.trap_frequency.current_key, bool(world.options.blessings.value), world.multiworld.seed_name, world.player)
    for position, name in positions.items():
        world.multiworld.itempool[start + position] = create_item(world, name)

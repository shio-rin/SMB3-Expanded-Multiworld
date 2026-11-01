# SPDX-License-Identifier: MPL-2.0
"""The six supported effects and independent, deterministic filler substitution.

This module has no AP imports and is shared with the managed client.
"""
from collections import Counter
from hashlib import sha256
from random import Random
CONTRACT = 'm25-effects-1'
PERCENT = {'off': 0, 'light': 10, 'normal': 20, 'heavy': 30, 'chaos': 40}
SPECS = {1397568512: ('Forced Small Trap', 'small', True), 1397568514: ('Walking Only Trap', 'walking', True), 1397568515: ('Micro-Goomba Infestation', 'micro', True), 1397568516: ('Icy Feet Trap', 'icy', True), 1397568528: ('Starman (Effect)', 'star', False), 1397568529: ('Emergency Mushroom (Effect)', 'mushroom', False)}
RESERVED = frozenset((1397568513, 1397568530, 1397568531))
WEIGHTS = {'walking': 4, 'icy': 4, 'micro': 1, 'small': 1}
BY_KIND = {v[1]: (k, v[0]) for k, v in SPECS.items()}

def settings(frequency='off', blessings=False, death_link=False):
    if frequency not in PERCENT or type(blessings) is not bool or type(death_link) is not bool:
        raise ValueError('Invalid effect settings')
    return dict(contract=CONTRACT, trap_frequency=frequency, blessings=blessings, death_link=death_link, delay='SMB3/trap-delay/1', selection='oldest-compatible-1')

def validate_settings(value):
    if not isinstance(value, dict) or value != settings(value.get('trap_frequency'), value.get('blessings'), value.get('death_link')):
        raise ValueError('Unknown effects contract')
    return value

def rng(seed, slot, domain):
    return Random(int.from_bytes(sha256(f'SMB3/m25/{domain}/1\x00{seed}\x00{slot}'.encode()).digest(), 'big'))

def delay_frames(seed, team, slot, index, entry):
    h = 0
    for b in f'SMB3/trap-delay/1|{seed}|{team}|{slot}|{index}|{entry}'.encode('utf-8'):
        h = (h * 131 + b) % 2147483647
    return 60 * (4 + h % 15)

def replacement_plan(names, protected, frequency, blessings, seed, slot):
    settings(frequency, blessings)
    mushrooms = [i for i, n in enumerate(names) if n == 'Super Mushroom' and i not in protected]
    leaves = [i for i, n in enumerate(names) if n == 'Super Leaf' and i not in protected]
    denominator = len(mushrooms) + len(leaves)
    requested = denominator * PERCENT[frequency] // 100
    reserve = (3 * len(leaves) + 3) // 4
    available_leaves = len(leaves) - reserve
    order = rng(seed, slot, 'trap-pool')
    order.shuffle(mushrooms)
    order.shuffle(leaves)
    positions = mushrooms + leaves[:available_leaves]
    blessing_count = 2 if blessings else 0
    if len(positions) < blessing_count:
        raise ValueError('Blessings require two eligible nonprogression filler rewards')
    count = min(requested, len(positions) - blessing_count)
    cycle = [BY_KIND[k][1] for k, weight in WEIGHTS.items() for _ in range(weight)]
    rng(seed, slot, 'trap-types').shuffle(cycle)
    replacements = {i: cycle[k % len(cycle)] for k, i in enumerate(positions[:count])}
    if blessings:
        replacements.update(zip(positions[count:count + 2], (BY_KIND['star'][1], BY_KIND['mushroom'][1])))
    after = [replacements.get(i, n) for i, n in enumerate(names)]
    return (replacements, dict(contract=CONTRACT, frequency=frequency, target_percent=PERCENT[frequency], eligible=denominator, requested_traps=requested, traps=count, blessings=blessing_count, leaf_reserve=reserve, before=dict(Counter(names)), after=dict(Counter(after)), distribution=dict(Counter(replacements.values())), total=len(names)))

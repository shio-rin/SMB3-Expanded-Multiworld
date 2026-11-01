# SPDX-License-Identifier: MPL-2.0
"""Bounded, final-fill pacing repair using AP location rules and real spheres.

Runs in the supported pre_output stage, after progression balancing. Never changes
access rules. Explicit precollected or locked Hammers take precedence.
"""
import hashlib
import json
VERSION = 'm242-staggered-1'
HAMMERS = {2: 'Desert Hammer', 3: 'Water Hammer', 4: 'Giant Hammer', 6: 'Ice Hammer'}
LIMIT = 512

def measure(mw):
    spheres = {}
    sizes = []
    for number, sphere in enumerate(mw.get_sendable_spheres(), 1):
        if not sphere:
            return None
        sizes.append(len(sphere))
        for loc in sphere:
            spheres[loc] = number
    items = {(item.player, item.name): 0 for group in mw.precollected_items.values() for item in group}
    for loc, sphere in spheres.items():
        key = (loc.item.player, loc.item.name)
        items[key] = min(sphere, items.get(key, sphere))
    return (spheres, items, sizes)

def run(mw):
    from BaseClasses import CollectionState, LocationProgressType
    worlds = [w for w in mw.worlds.values() if w.game == 'Super Mario Bros. 3: Expanded Multiworld']
    selected = [w for w in worlds if w.options.world_pass_placement.value == 1]
    if not selected:
        return
    current = measure(mw)
    if current is None:
        raise ValueError('Staggered requires a fully reachable starting fill')
    locations = sorted(current[0], key=lambda loc: (loc.player, loc.address))
    lookup = {(loc.item.player, loc.item.name): loc for loc in locations}
    precollected = {(i.player, i.name) for group in mw.precollected_items.values() for i in group}
    pairs = []
    exceptions = []
    for world in selected:
        if world.options.hammer_mode.current_key != 'regional':
            continue
        for number, hammer in HAMMERS.items():
            key = (world.player, hammer)
            if key in precollected or (key in lookup and lookup[key].locked):
                exceptions.append(dict(player=world.player, item=hammer, reason='explicit starting inventory or locked placement'))
            else:
                pairs.append((world.player, number, hammer))

    def score(data):
        _, items, _ = data
        debt = sum((max(0, 1 + items[p, f'World {w} Pass'] - items[p, h]) for p, w, h in pairs))
        inversions = sum((max(0, items[world.player, f'World {a} Pass'] - items[world.player, f'World {b} Pass']) for world in selected for a in (2, 3) for b in (4, 5, 6, 7, 8)))
        inversions += sum((max(0, items[world.player, f'World {a} Pass'] - items[world.player, f'World {b} Pass']) for world in selected for a in (4, 5, 6) for b in (7, 8)))
        early = sum((max(0, 3 - items[w.player, f'World {n} Pass']) for w in selected for n in (7, 8) if (w.player, f'World {n} Pass') not in precollected))
        return (debt, inversions + early)

    def swap(a, b):
        a.item, b.item = (b.item, a.item)
        a.item.location = a
        b.item.location = b
    state = CollectionState(mw)
    attempts = swaps = 0
    initial = score(current)

    def order(loc):
        return hashlib.sha256(f'{VERSION}:{mw.seed_name}:{loc.player}:{loc.address}'.encode()).digest()
    while attempts < LIMIT:
        improved = False
        old_score = score(current)
        targets = []
        for p, n, h in pairs:
            if current[1][p, h] <= current[1][p, f'World {n} Pass']:
                targets.append((lookup[p, h], 'later'))
                key = (p, f'World {n} Pass')
                if key not in precollected and key in lookup:
                    targets.append((lookup[key], 'earlier'))
        if not targets:
            for world in selected:
                for number in (2, 3, 7, 8, 4, 5, 6):
                    key = (world.player, f'World {number} Pass')
                    if key not in precollected and key in lookup:
                        targets.append((lookup[key], 'earlier' if number <= 3 else 'later'))
        for source, direction in targets:
            if source.locked or source.progress_type == LocationProgressType.PRIORITY:
                continue
            candidates = [loc for loc in locations if not loc.locked and (not loc.item.advancement) and (loc.progress_type != LocationProgressType.PRIORITY) and (current[0][loc] > current[0][source] if direction == 'later' else current[0][loc] < current[0][source])]
            candidates.sort(key=order)
            for target in candidates[:32]:
                if attempts >= LIMIT:
                    break
                if not source.can_fill(state, target.item, False) or not target.can_fill(state, source.item, False):
                    continue
                attempts += 1
                moving = (source.item.player, source.item.name)
                displaced = (target.item.player, target.item.name)
                swap(source, target)
                proposal = measure(mw)
                accept = proposal is not None and score(proposal) < old_score
                if accept:
                    try:
                        accept = mw.fulfills_accessibility() and mw.can_beat_game()
                    except Exception:
                        accept = False
                if accept:
                    lookup[moving] = target
                    lookup[displaced] = source
                    current = proposal
                    swaps += 1
                    improved = True
                    break
                swap(source, target)
            if improved:
                break
        if not improved:
            break
    final = score(current)
    if final[0]:
        raise ValueError(f'Staggered could not satisfy Pass-before-Hammer within {attempts} bounded candidates; use Unrestricted or revise explicit constraints. No unrestricted fallback was used.')
    if not mw.fulfills_accessibility() or not mw.can_beat_game():
        raise ValueError('Staggered final accessibility/completion validation failed')
    assignment = sorted(((l.player, l.address, l.item.player, l.item.code) for l in locations))
    digest = hashlib.sha256(json.dumps(assignment, separators=(',', ':')).encode()).hexdigest()
    report = dict(version=VERSION, attempts=attempts, swaps=swaps, initial_score=initial, final_score=final, exceptions=exceptions, assignment_sha256=digest, sphere_sizes=current[2], after_progression_balancing=True)
    for world in worlds:
        world.placement_report = report

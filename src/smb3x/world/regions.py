# SPDX-License-Identifier: MPL-2.0
from ..shared.resources import DATA
from ..shared.progression import validate, HAMMERS
from ..shared.locations import ACTIVE
from BaseClasses import ItemClassification, Region
from .types import SMB3Item, SMB3Location
from hashlib import sha256
import json
from .settings import settings

ROWS = json.loads((DATA / 'locations_m191.json').read_bytes())
ROUTES = {
    1: ['1-1', '1-2', '1-3', '1-4', 'fortress', '1-5', '1-6', 'airship'],
    2: ['2-1', '2-2', '2-3', 'fortress', '2-4', '2-5', 'desert', 'pyramid', 'airship'],
    3: [
        '3-1',
        '3-2',
        '3-3',
        'fortress-1',
        '3-4',
        '3-5',
        '3-6',
        '3-7',
        '3-8',
        '3-9',
        'fortress-2',
        'airship',
    ],
    4: ['4-1', '4-2', '4-3', 'fortress-1', '4-4', '4-5', '4-6', 'fortress-2', 'airship'],
    5: [
        '5-1',
        '5-2',
        '5-3',
        'fortress-1',
        'tower',
        '5-4',
        '5-5',
        '5-6',
        '5-7',
        '5-8',
        '5-9',
        'fortress-2',
        'airship',
    ],
    6: [
        '6-1',
        '6-2',
        '6-3',
        'fortress-1',
        '6-4',
        '6-5',
        '6-6',
        '6-7',
        'fortress-2',
        '6-8',
        '6-9',
        '6-10',
        'fortress-3',
        'airship',
    ],
    7: [
        '7-1',
        '7-2',
        '7-3',
        '7-4',
        'fortress-1',
        '7-5',
        '7-6',
        '7-7',
        '7-8',
        '7-9',
        'fortress-2',
        'airship',
    ],
    8: ['big-tanks', 'battleships', 'air-force', '8-1', '8-2', 'fortress', 'super-tank', 'bowser'],
}


def event_name(world, stage):
    """Stable AP logical item/location key; spelling is included in generation output."""
    return f'M19.1 native clear W{world} {stage}'


def create_regions(world):
    """Build physical check hosts and the event gates that make their routes reachable."""
    player = world.player
    multiworld = world.multiworld
    config = settings(world)
    menu = Region('Menu', player, multiworld)
    regions = {
        world_number: Region(f'World {world_number}', player, multiworld)
        for world_number in range(1, 9)
    }
    multiworld.regions.extend([menu, *regions.values()])
    for world_number, region in regions.items():
        menu.connect(
            region,
            rule=lambda state, world_number=world_number: (
                world_number == 1 or state.has(f'World {world_number} Pass', player)
            )
            and (
                world_number != 8
                or config['star_hunt_mode'] != 'world_8'
                or state.has('Star Fragment', player, config['star_fragments_required'])
            ),
        )
    sky = Region('World 5 Sky', player, multiworld)
    multiworld.regions.append(sky)
    regions[5].connect(sky, rule=lambda state: state.has(event_name(5, 'tower'), player))
    tower = SMB3Location(player, event_name(5, 'tower'), None, regions[5])
    tower.access_rule = lambda state: state.has(event_name(5, 'fortress-1'), player)
    tower.place_locked_item(
        SMB3Item(event_name(5, 'tower'), ItemClassification.progression, None, player)
    )
    regions[5].locations.append(tower)
    graph = json.loads((DATA / 'routes_m12.json').read_text())
    nodes = {
        tuple(p): Region(f'World 7 map {p[0]}:{p[1]}', player, multiworld) for p in graph['nodes']
    }
    multiworld.regions.extend(nodes.values())
    regions[7].connect(nodes[tuple(graph['start'])])

    def point(row):
        entry = row.get('entry', {'x': '0x80', 'x_hi': '0x01', 'y': '0x90'})
        return (int(entry['x'], 16) // 16 + 16 * int(entry['x_hi'], 16), int(entry['y'], 16) // 16)

    blockers = {
        point(r): r['stage'] for r in ROWS if r['world'] == 7 and r['kind'] in ('stage', 'plant')
    }
    for edge in graph['edges']:
        source = tuple(edge['source'])
        target = tuple(edge['target'])
        gates = tuple((event_name(7, g) for g in (blockers.get(source), edge['fortress']) if g))
        nodes[source].connect(
            nodes[target],
            rule=lambda state, gates=gates: all((state.has(g, player) for g in gates)),
        )
    # A shuffled stage changes contents, never the physical host or its numeric ID.
    for row in world.locations:
        world_number = row['world']
        stage = row['stage']
        if world_number == 7:
            region = nodes[point(row)]
        elif world_number == 5 and row.get('map_section') == 'sky':
            region = sky
        else:
            region = regions[world_number]
        location = SMB3Location(player, row['name'], int(row['id'], 16), region)
        location.item_rule = lambda item, world_number=world_number: not (
            item.player == player and item.name == f'World {world_number} Pass'
        )
        route = ROUTES[world_number]
        previous = (
            route[route.index(stage) - 1] if stage in route and route.index(stage) > 0 else None
        )
        if stage not in route:
            previous = route[-2]
        if row['kind'] == 'hand':
            previous = 'battleships'
        if previous and world_number != 7:
            location.access_rule = lambda state, world_number=world_number, p=previous: state.has(
                event_name(world_number, p), player
            )
        if world_number == 8 and stage == 'bowser' and (config['star_hunt_mode'] == 'bowser'):
            route_rule = location.access_rule
            location.access_rule = lambda state, route_rule=route_rule: route_rule(
                state
            ) and state.has('Star Fragment', player, config['star_fragments_required'])
        if row.get('regional_hammer_required') and config['hammer_mode'] == 'regional':
            route_rule = location.access_rule
            tool = row['regional_hammer_required']
            location.access_rule = lambda state, route_rule=route_rule, tool=tool: route_rule(
                state
            ) and state.has(tool, player)
        if row.get('hammer_required'):
            route_rule = location.access_rule
            location.access_rule = lambda state, route_rule=route_rule, name=row[
                'hammer_required'
            ]: route_rule(state) and state.has(name, player)
        region.locations.append(location)
        if stage in route or (world_number == 7 and row['kind'] == 'plant'):
            event = SMB3Location(player, event_name(world_number, stage), None, region)
            event.access_rule = location.access_rule
            event.place_locked_item(
                SMB3Item(
                    event_name(world_number, stage), ItemClassification.progression, None, player
                )
            )
            region.locations.append(event)
        checked = SMB3Location(player, checked_event(row), None, region)
        checked.access_rule = location.access_rule
        checked.place_locked_item(
            SMB3Item(checked_event(row), ItemClassification.progression, None, player)
        )
        region.locations.append(checked)
    # These names are AP graph identities, not display-only diagnostic messages.
    ending = SMB3Location(player, 'M19.1 ending transition', None, regions[8])
    ending.access_rule = lambda state: state.has(event_name(8, 'bowser'), player)
    ending.place_locked_item(
        SMB3Item('M19.1 confirmed ending', ItemClassification.progression, None, player)
    )
    regions[8].locations.append(ending)
    config = settings(world)
    player = world.player
    region = world.multiworld.get_region('World 8', player)
    event = SMB3Location(player, event_name(8, 'bowser'), None, region)
    event.access_rule = lambda state: state.has(event_name(8, 'super-tank'), player) and (
        config['star_hunt_mode'] != 'bowser'
        or state.has('Star Fragment', player, config['star_fragments_required'])
    )
    event.place_locked_item(
        SMB3Item(event_name(8, 'bowser'), ItemClassification.progression, None, player)
    )
    region.locations.append(event)


def checked_event(row):
    return 'M19.1 checked ' + row['id']

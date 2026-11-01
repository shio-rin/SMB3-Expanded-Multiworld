# SPDX-License-Identifier: MPL-2.0
"""The current SMB3X World: lifecycle methods are explicit and direct."""
from BaseClasses import Tutorial
from worlds.AutoWorld import World, WebWorld
from worlds.LauncherComponents import Component, Type, SuffixIdentifier, components, launch
from .types import GAME
from .options import SMB3Options, OPTION_GROUPS, generate_early
from .regions import create_regions
from .rules import set_rules
from .item_pool import create_item, create_items
from .placement import run as place_progression
from . import output
from ..shared.locations import ACTIVE
from ..shared.ids import ITEM_IDS, LOCATION_IDS

class SMB3Web(WebWorld):
    theme = 'grass'
    option_groups = OPTION_GROUPS
    rich_text_options_doc = True
    tutorials = [Tutorial('Multiworld Setup Guide', 'Install and play SMB3X with safe checkpoints.', 'English', 'setup_en.md', 'setup/en', ['SMB3 Archipelago contributors'])]

class SMB3World(World):
    """125 reward checks, original-stage randomization and automatic safe checkpoints."""
    game = GAME
    settings_key = 'smb3x_options'
    web = SMB3Web()
    options_dataclass = SMB3Options
    origin_region_name = 'Menu'
    locations = ACTIVE
    item_name_to_id = ITEM_IDS
    location_name_to_id = LOCATION_IDS
    generate_early = generate_early
    create_regions = create_regions
    create_item = create_item
    create_items = create_items
    set_rules = set_rules
    fill_slot_data = output.slot_data
    generate_output = output.generate_output
    stage_pre_output = staticmethod(place_progression)

    def get_filler_item_name(self):
        return '1-Up'

def run_player(*args):
    from ..launcher.runtime import load_player
    load_player(output.RESOURCE_ROOT, output.RESOURCE_ID).main(args, output.RESOURCE_ROOT, output.RESOURCE_ID)

def launch_player(*args):
    launch(run_player, name='SMB3X', args=args)

def register_resources(resource_id, root):
    output.RESOURCE_ID, output.RESOURCE_ROOT = (resource_id, root)
    if not any((c.game_name == GAME and c.func is launch_player for c in components)):
        components.append(Component(GAME, component_type=Type.CLIENT, func=launch_player, file_identifier=SuffixIdentifier('.apsmb3x'), game_name=GAME, cli=False, description='Open an SMB3X player file; prepares, starts and resumes its managed session automatically.'))
    from .yaml_validation import install_guard
    install_guard()

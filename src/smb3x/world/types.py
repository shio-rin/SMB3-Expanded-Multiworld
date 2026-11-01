# SPDX-License-Identifier: MPL-2.0
"""Archipelago item/location types. Pure game data does not import this module."""
from BaseClasses import Item, Location
GAME = 'Super Mario Bros. 3: Expanded Multiworld'

class SMB3Item(Item):
    game = GAME

class SMB3Location(Location):
    game = GAME

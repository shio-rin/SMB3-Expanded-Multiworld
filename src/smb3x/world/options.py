# SPDX-License-Identifier: MPL-2.0
"""Final option declarations, in the accepted AP0.6.8 parsing order.

Internal fixed fields are retained only for explicit diagnostics and deterministic
weighted YAML. The removed Legacy12 selectors are not registered options.
"""

from dataclasses import dataclass
import Options as framework
from Options import OptionGroup, Visibility, PerGameCommonOptions


class _DefaultVanilla(int):
    """The integer default also records omission before music normalization."""


class _ExplicitChoice:

    @classmethod
    def from_any(cls, data):
        omitted = isinstance(data, _DefaultVanilla)
        value = super().from_any(int(data) if omitted else data)
        value.explicit = not omitted
        value.value = int(value.value)
        return value


class ProgressionBalancing(framework.ProgressionBalancing):
    """Help players avoid long waits for important items.
    Archipelago may move those items earlier in multiplayer games.
    0 disables it; 50 is Normal; 99 is Maximum. Solo is unaffected."""

    rich_text_doc = 1


class Accessibility(framework.Accessibility):
    """Choose whether all checks or only your goal must be reachable.
    Full ensures all checks; Minimal ensures you can win.
    Minimal may need Unrestricted World Pass Placement."""

    rich_text_doc = 1


Accessibility.name_lookup = {0: 'full', 2: 'minimal'}


class LocalItems(framework.LocalItems):
    """Forces these items to be in their native world."""


class NonLocalItems(framework.NonLocalItems):
    """Forces these items to be outside their native world."""


class StartInventory(framework.StartInventory):
    """Start with the specified amount of these items. Example: {Bomb: 1, Arrow: 3}"""


class StartHints(framework.StartHints):
    """Start with these item's locations prefilled into the ``!hint`` command."""


class StartLocationHints(framework.StartLocationHints):
    """Start with these locations and their item prefilled into the ``!hint`` command."""


class ExcludeLocations(framework.ExcludeLocations):
    """Prevent these locations from having an important item."""


class PriorityLocations(framework.PriorityLocations):
    """Prevent these locations from having an unimportant item."""


class ItemLinks(framework.ItemLinks):
    """Share part of your item pool with other players."""


class PlandoItems(framework.PlandoItems):
    """Generic items plando."""


class RewardPool(framework.Choice):
    None
    display_name = 'Reward Pool'
    option_weighted = 0
    option_verification = 1
    default = 0
    visibility = Visibility(0)


RewardPool.name_lookup = {0: 'weighted', 1: 'verification'}


class LocationProfile(framework.Choice):
    """Hidden parse contract. Only value 19 passes current generation.

    Historical choice spellings/numbers preserve parsing and RNG consumption;
    they are not selectable gameplay implementations. Keep declaration order.
    """

    display_name = 'Location Set'
    option_m6 = 0
    option_m7 = 1
    option_m7_airship_test = 2
    option_m9 = 3
    option_m10 = 4
    option_m11 = 5
    option_m12 = 6
    option_m13 = 7
    option_m14 = 8
    option_m15 = 9
    option_m16 = 10
    option_m17 = 11
    option_m18 = 12
    option_m19 = 13
    option_m191 = 14
    option_m20 = 15
    option_m21 = 16
    option_m22 = 17
    option_m221 = 18
    option_m222 = 19
    default = 19
    visibility = Visibility(0)


LocationProfile.name_lookup = {
    0: 'm6',
    1: 'm7',
    2: 'm7_airship_test',
    3: 'm9',
    4: 'm10',
    5: 'm11',
    6: 'm12',
    7: 'm13',
    8: 'm14',
    9: 'm15',
    10: 'm16',
    11: 'm17',
    12: 'm18',
    13: 'm19',
    14: 'm191',
    15: 'm20',
    16: 'm21',
    17: 'm22',
    18: 'm221',
    19: 'm222',
}


class Goal(framework.Choice):
    """Choose what you must finish to win.
    Standard: the ending. All Koopalings: seven bosses and ending.
    All Locations: all 125 reward checks and the ending."""

    display_name = 'Victory Condition'
    option_standard = 0
    option_all_koopalings = 1
    option_all_locations = 2
    default = 0
    rich_text_doc = 1


Goal.name_lookup = {0: 'standard', 1: 'all_koopalings', 2: 'all_locations'}


class HammerMode(framework.Choice):
    """Choose reusable world-specific or consumable Hammers.
    Regional removes that world's rocks without using up a Hammer.
    Legacy spends Hammers from your inventory.
    World Pass requirements still apply."""

    display_name = 'Hammer Mode'
    option_legacy = 0
    option_regional = 1
    default = 1
    rich_text_doc = 1


HammerMode.name_lookup = {0: 'legacy', 1: 'regional'}


class StarHuntMode(framework.Choice):
    """Require Star Fragments before World 8 or the final battle.
    Off adds no requirement. World 8 gates that world; Bowser gates
    the final fight. Your goal and World Pass rules still apply."""

    display_name = 'Star Fragment Access Gate'
    option_off = 0
    option_world_8 = 1
    option_bowser = 2
    default = 0
    rich_text_doc = 1


StarHuntMode.name_lookup = {0: 'off', 1: 'world_8', 2: 'bowser'}


class StarFragmentsRequired(framework.Range):
    """Set how many Star Fragments your chosen gate needs.
    Cannot exceed Total. Ignored when Star Hunt is Off."""

    display_name = 'Star Fragments Required'
    range_start = 1
    range_end = 255
    default = 12
    rich_text_doc = 1


class StarFragmentsTotal(framework.Range):
    """Set how many Star Fragments are placed in the multiworld.
    Must be at least Required. Ignored when Star Hunt is Off."""

    display_name = 'Star Fragments Total'
    range_start = 1
    range_end = 255
    default = 20
    rich_text_doc = 1


class FortressKeys(framework.Choice):
    None
    display_name = 'Fortress Keys'
    option_off = 0
    default = 0
    visibility = Visibility(0)


FortressKeys.name_lookup = {0: 'off'}


class RewardVisualStyle(framework.Choice):
    """Choose how reward objects look before you collect them.
    Mystery uses a neutral look; Vanilla keeps the original art.
    Neither reveals or changes the item you receive."""

    display_name = 'Treasure Appearance'
    option_vanilla = 0
    option_mystery = 1
    default = 1
    rich_text_doc = 1


RewardVisualStyle.name_lookup = {0: 'vanilla', 1: 'mystery'}


class InventoryMode(framework.Choice):
    None
    display_name = 'Inventory Mode'
    option_vanilla = 0
    option_stacked = 1
    default = 1
    visibility = Visibility(0)


InventoryMode.name_lookup = {0: 'vanilla', 1: 'stacked'}


class LevelMusicShuffle(framework.Choice):
    None
    display_name = 'Level Music Shuffle'
    option_vanilla = 0
    option_compatible = 1
    default = 0
    visibility = Visibility(0)


LevelMusicShuffle.name_lookup = {0: 'vanilla', 1: 'compatible'}


class LevelPaletteShuffle(framework.Choice):
    None
    display_name = 'Level Palette Shuffle'
    option_off = 0
    option_constrained = 1
    default = 0
    visibility = Visibility(0)


LevelPaletteShuffle.name_lookup = {0: 'off', 1: 'constrained'}


class OverworldPaletteShuffle(framework.Choice):
    None
    display_name = 'Overworld Palette Shuffle'
    option_off = 0
    option_constrained = 1
    default = 0
    visibility = Visibility(0)


OverworldPaletteShuffle.name_lookup = {0: 'off', 1: 'constrained'}


class PlayerAppearance(framework.Choice):
    """Choose Mario or Luigi's appearance.
    Movement and abilities stay the same."""

    display_name = 'Player Appearance'
    option_mario = 0
    option_luigi = 1
    default = 0
    rich_text_doc = 1


PlayerAppearance.name_lookup = {0: 'mario', 1: 'luigi'}


class LevelShuffle(framework.Choice):
    """Keep original stage placement or shuffle 53 eligible stages.
    Balanced uses the same or neighboring original worlds.
    Compatible uses the full technically eligible pool.
    Required entry, exit and route safety restrictions always apply."""

    display_name = 'Level Shuffle'
    option_vanilla = 0
    option_compatible = 1
    option_balanced = 2
    default = 0
    rich_text_doc = 1

    @classmethod
    def from_text(cls, text):
        if text.lower() == 'random':
            from random import choice

            return cls(choice((0, 1, 2)))
        return super().from_text(text)


LevelShuffle.name_lookup = {0: 'vanilla', 2: 'balanced', 1: 'compatible'}


class SpecialStageShuffle(framework.Choice):
    """Keep special stages in place or mix their contents.
    Off keeps originals. By Type mixes stages of the same kind.
    Mixed Fortresses can exchange regular stages and fortresses.
    Requires Level Shuffle to be enabled."""

    display_name = 'Special Stage Shuffle'
    option_off = 0
    option_by_type = 1
    option_mixed_fortresses = 2
    default = 0
    rich_text_doc = 1


SpecialStageShuffle.name_lookup = {0: 'off', 1: 'by_type', 2: 'mixed_fortresses'}


class ClassicLevelPacks(framework.Choice):
    None
    display_name = 'Classic Level Pack'
    option_off = 0
    option_smb1 = 1
    option_lost_levels = 2
    option_all = 3
    option_smw = 4
    option_world_e = 5
    default = 0
    visibility = Visibility(0)


ClassicLevelPacks.name_lookup = {
    0: 'off',
    1: 'smb1',
    2: 'lost_levels',
    3: 'all',
    4: 'smw',
    5: 'world_e',
}


class ClassicStageCount(framework.Range):
    None
    display_name = 'Classic Stage Count'
    range_start = 0
    range_end = 12
    default = 0
    visibility = Visibility(0)


class MusicPolicy(framework.Choice):
    None
    display_name = 'Soundtrack Policy'
    option_vanilla = 0
    option_contextual = 1
    option_mixed = 2
    option_anything_goes = 3
    default = 0
    visibility = Visibility(0)


MusicPolicy.name_lookup = {0: 'vanilla', 1: 'contextual', 2: 'mixed', 3: 'anything_goes'}


class OriginalMusicPercent(framework.Range):
    None
    display_name = 'Original Music Percent'
    range_start = 25
    range_end = 75
    default = 33
    visibility = Visibility(0)


class CustomTrackBudget(framework.Range):
    None
    display_name = 'Custom Track Budget'
    range_start = 0
    range_end = 16
    default = 8
    visibility = Visibility(0)


class MusicPack(framework.FreeText):
    None
    display_name = 'Local Soundtrack Pack'
    default = ''
    visibility = Visibility(0)


class MusicFamilies(framework.OptionSet):
    None
    display_name = 'Enabled Music Families'
    valid_keys = frozenset(('development', 'local', 'mario-classics', 'nes-classics'))
    default = frozenset(('local',))
    visibility = Visibility(0)


class DevelopmentMusic(framework.Choice):
    None
    display_name = 'Development Music Fixtures'
    option_off = 0
    option_on = 1
    default = 0
    visibility = Visibility(0)


DevelopmentMusic.name_lookup = {0: 'off', 1: 'on'}


class SecondaryMusic(framework.Choice):
    None
    display_name = 'Secondary Area Music'
    option_inherit = 0
    option_independent = 1
    default = 1
    visibility = Visibility(0)


SecondaryMusic.name_lookup = {0: 'inherit', 1: 'independent'}


class LevelPaletteStyle(framework.Choice):
    None
    display_name = 'Level Palette Style'
    option_vanilla = 0
    option_constrained = 1
    option_themed = 2
    default = 0
    visibility = Visibility(0)


LevelPaletteStyle.name_lookup = {0: 'vanilla', 1: 'constrained', 2: 'themed'}


class OverworldPaletteStyle(framework.Choice):
    None
    display_name = 'Overworld Palette Style'
    option_vanilla = 0
    option_constrained = 1
    option_themed = 2
    default = 0
    visibility = Visibility(0)


OverworldPaletteStyle.name_lookup = {0: 'vanilla', 1: 'constrained', 2: 'themed'}


class PaletteThemes(framework.OptionSet):
    None
    display_name = 'Preferred Certified Theme Subset'
    valid_keys = frozenset(
        ('hills-autumn', 'map-midnight', 'plains-dusk', 'plains-midnight', 'plains-sunset')
    )
    default = frozenset(
        ('hills-autumn', 'map-midnight', 'plains-dusk', 'plains-midnight', 'plains-sunset')
    )
    visibility = Visibility(0)


class PoisonMushrooms(framework.Choice):
    """Choose whether some power-ups become harmful Poison Mushrooms.
    Off / Rare / Normal / Chaos: 0 / 5 / 15 / 35% chances.
    Only some blocks can change; essential power-ups stay safe."""

    display_name = 'Poison Mushrooms'
    option_off = 0
    option_rare = 1
    option_normal = 2
    option_chaos = 3
    default = 0
    rich_text_doc = 1


PoisonMushrooms.name_lookup = {0: 'off', 1: 'rare', 2: 'normal', 3: 'chaos'}


class AngrySun(framework.Choice):
    """Add extra Angry Suns to some stages.
    Rare, Normal and Chaos increase how often they appear.
    Off adds none. A stage gets at most one extra Sun.
    Off is recommended for a first game."""

    display_name = 'Angry Sun'
    option_off = 0
    option_rare = 1
    option_normal = 2
    option_chaos = 3
    default = 0
    rich_text_doc = 1


AngrySun.name_lookup = {0: 'off', 1: 'rare', 2: 'normal', 3: 'chaos'}


class MusicShuffle(_ExplicitChoice, framework.Choice):
    """Advanced YAML music mode; requires deliberate player coordination.
    Custom modes require the exact compatible pack. None is provided.
    See the complete options reference before enabling custom music."""

    display_name = 'Advanced Music Mode'
    option_vanilla = 0
    option_shuffled = 1
    option_custom_mixed = 2
    option_custom_only = 3
    default = _DefaultVanilla(0)
    visibility = Visibility(0)


MusicShuffle.name_lookup = {0: 'vanilla', 1: 'shuffled', 2: 'custom_mixed', 3: 'custom_only'}


class OverworldMusicShuffle(framework.Choice):
    """Keep each world's map theme or shuffle the eight themes.
    Vanilla keeps originals. Shuffled mixes the original themes.
    No external music pack is needed."""

    display_name = 'World Map Music'
    option_vanilla = 0
    option_shuffled = 1
    default = 0
    rich_text_doc = 1


OverworldMusicShuffle.name_lookup = {0: 'vanilla', 1: 'shuffled'}


class NativeMapMusic(framework.Choice):
    """Internal native-plan vocabulary; the public selector says Shuffled."""

    option_vanilla = 0
    option_compatible = 1
    default = 0


class PaletteMode(framework.Choice):
    """Choose color themes for levels and world maps.
    Original: classic SMB3 colors.
    Atmospheric: classic colors mixed with environment themes.
    Full: the widest range, including bolder color styles."""

    display_name = 'Palette Mode'
    option_original = 0
    option_atmospheric = 1
    option_full = 2
    default = 0
    rich_text_doc = 1


PaletteMode.name_lookup = {0: 'original', 1: 'atmospheric', 2: 'full'}


class WorldPassPlacement(framework.Choice):
    """Choose how World Passes and Hammers are spread through the game.
    Staggered favors earlier-world access; Unrestricted does not.
    Starting items and fixed placements can override the order.
    See the reference for Hammer timing and accessibility limits."""

    display_name = 'World Pass Placement'
    option_unrestricted = 0
    option_staggered = 1
    default = 1
    rich_text_doc = 1


WorldPassPlacement.name_lookup = {0: 'unrestricted', 1: 'staggered'}


class MusicReserves(framework.Choice):
    """Advanced YAML-only: also allow the three accepted reserve arrangements in custom seed selection."""

    display_name = 'Include R3 Reserves'
    option_off = 0
    option_on = 1
    default = 0
    visibility = Visibility(0)


MusicReserves.name_lookup = {0: 'off', 1: 'on'}


class MusicTracks(framework.OptionSet):
    """Advanced YAML-only: optional accepted track IDs to include in the 16-slot subset. Empty selects automatically."""

    valid_keys = frozenset(())
    default = frozenset(())
    display_name = 'Requested R3 Tracks'
    visibility = Visibility(0)


class TrapFrequency(framework.Choice):
    """Choose how often some regular rewards become traps.
    Off / Light / Normal / Heavy / Chaos: 0 / 10 / 20 / 30 / 40%.
    Traps can activate during jumps or combat and cause death.
    Activation may briefly stutter."""

    display_name = 'Trap Frequency'
    option_off = 0
    option_light = 1
    option_normal = 2
    option_heavy = 3
    option_chaos = 4
    default = 0
    rich_text_doc = 1


TrapFrequency.name_lookup = {0: 'off', 1: 'light', 2: 'normal', 3: 'heavy', 4: 'chaos'}


class Blessings(framework.Toggle):
    """Add one Starman effect and one Emergency Mushroom effect.
    The Mushroom turns Small into Super and keeps stronger suits.
    Effects activate later and may briefly stutter."""

    display_name = 'Blessings'
    default = 0
    rich_text_doc = 1


Blessings.name_lookup = {0: 'false', 1: 'true'}


class DeathLink(framework.DeathLink):
    """Share deaths with other players who enable DeathLink.
    An incoming death can cost you a life.
    Off keeps deaths separate."""

    rich_text_doc = 1


DeathLink.name_lookup = {0: 'false', 1: 'true'}


class TrapWarning(framework.Choice):
    """Show trap notices early or hide them until activation.
    Hide affects SMB3X only; other clients may reveal traps.
    Blessings, ordinary rewards and save errors stay visible."""

    display_name = 'Trap Warning'
    option_show = 0
    option_hide = 1
    default = 0
    rich_text_doc = 1


TrapWarning.name_lookup = {0: 'show', 1: 'hide'}


class LevelMusic(_ExplicitChoice, framework.Choice):
    """Keep the original level music or shuffle its tracks.
    Both choices work without an external music pack."""

    display_name = 'Level Music'
    option_vanilla = 0
    option_shuffled = 1
    default = _DefaultVanilla(0)


LevelMusic.name_lookup = {0: 'vanilla', 1: 'shuffled'}


@dataclass
class SMB3Options(PerGameCommonOptions):
    progression_balancing: ProgressionBalancing
    accessibility: Accessibility
    local_items: LocalItems
    non_local_items: NonLocalItems
    start_inventory: StartInventory
    start_hints: StartHints
    start_location_hints: StartLocationHints
    exclude_locations: ExcludeLocations
    priority_locations: PriorityLocations
    item_links: ItemLinks
    plando_items: PlandoItems
    reward_pool: RewardPool
    location_set: LocationProfile
    goal: Goal
    hammer_mode: HammerMode
    star_hunt_mode: StarHuntMode
    star_fragments_required: StarFragmentsRequired
    star_fragments_total: StarFragmentsTotal
    fortress_keys: FortressKeys
    reward_visual_style: RewardVisualStyle
    inventory_mode: InventoryMode
    level_music_shuffle: LevelMusicShuffle
    level_palette_shuffle: LevelPaletteShuffle
    overworld_palette_shuffle: OverworldPaletteShuffle
    player_appearance: PlayerAppearance
    level_shuffle: LevelShuffle
    special_stage_shuffle: SpecialStageShuffle
    classic_level_packs: ClassicLevelPacks
    classic_stage_count: ClassicStageCount
    music_policy: MusicPolicy
    original_music_percent: OriginalMusicPercent
    custom_track_budget: CustomTrackBudget
    music_pack: MusicPack
    music_families: MusicFamilies
    development_music: DevelopmentMusic
    secondary_music: SecondaryMusic
    level_palette_style: LevelPaletteStyle
    overworld_palette_style: OverworldPaletteStyle
    palette_themes: PaletteThemes
    poison_mushrooms: PoisonMushrooms
    angry_sun: AngrySun
    music_shuffle: MusicShuffle
    overworld_music_shuffle: OverworldMusicShuffle
    palette_mode: PaletteMode
    world_pass_placement: WorldPassPlacement
    music_reserves: MusicReserves
    music_tracks: MusicTracks
    trap_frequency: TrapFrequency
    blessings: Blessings
    death_link: DeathLink
    trap_warning: TrapWarning
    level_music: LevelMusic


OPTION_GROUPS = [
    OptionGroup(
        'Goal & Logic',
        [
            ProgressionBalancing,
            Accessibility,
            RewardPool,
            LocationProfile,
            Goal,
            StarHuntMode,
            StarFragmentsRequired,
            StarFragmentsTotal,
            FortressKeys,
            InventoryMode,
            CustomTrackBudget,
        ],
        False,
    ),
    OptionGroup('World Progression', [HammerMode, WorldPassPlacement], False),
    OptionGroup(
        'Level Randomization',
        [LevelShuffle, SpecialStageShuffle, ClassicLevelPacks, ClassicStageCount],
        False,
    ),
    OptionGroup(
        'Hazards & Effects',
        [PoisonMushrooms, AngrySun, TrapFrequency, Blessings, DeathLink, TrapWarning],
        False,
    ),
    OptionGroup(
        'Music',
        [
            LevelMusicShuffle,
            MusicPolicy,
            OriginalMusicPercent,
            MusicPack,
            MusicFamilies,
            DevelopmentMusic,
            SecondaryMusic,
            MusicShuffle,
            OverworldMusicShuffle,
            MusicReserves,
            MusicTracks,
            LevelMusic,
        ],
        False,
    ),
    OptionGroup(
        'Visual',
        [
            RewardVisualStyle,
            LevelPaletteShuffle,
            OverworldPaletteShuffle,
            PlayerAppearance,
            LevelPaletteStyle,
            OverworldPaletteStyle,
            PaletteThemes,
            PaletteMode,
        ],
        False,
    ),
    OptionGroup(
        'Item & Location Options',
        [
            LocalItems,
            NonLocalItems,
            StartInventory,
            StartHints,
            StartLocationHints,
            ExcludeLocations,
            PriorityLocations,
            ItemLinks,
            PlandoItems,
        ],
        True,
    ),
]
FIXED = {
    'reward_pool': 0,
    'location_set': 19,
    'inventory_mode': 1,
    'fortress_keys': 0,
    'classic_level_packs': 0,
    'classic_stage_count': 0,
    'level_music_shuffle': 0,
    'level_palette_shuffle': 0,
    'overworld_palette_shuffle': 0,
    'music_policy': 0,
    'original_music_percent': 33,
    'custom_track_budget': 8,
    'music_pack': '',
    'music_families': frozenset(('local',)),
    'development_music': 0,
    'secondary_music': 1,
    'level_palette_style': 0,
    'overworld_palette_style': 0,
    'palette_themes': PaletteThemes.default,
}


def generate_early(world):
    public, advanced = (world.options.level_music, world.options.music_shuffle)
    public_explicit = getattr(public, 'explicit', True)
    advanced_explicit = getattr(advanced, 'explicit', True)
    if public_explicit and advanced_explicit and (public.value != advanced.value):
        raise ValueError(
            'Conflicting music settings: level_music and advanced music_shuffle select different modes. Use only one field, or matching vanilla/shuffled values. Custom modes require level_music to be omitted.'
        )
    mode = advanced.value if advanced_explicit else public.value
    world.options.music_shuffle = MusicShuffle(mode)
    for key, value in FIXED.items():
        if getattr(world.options, key).value != value:
            raise ValueError(
                f'{key} is internal in this release; use its fixed value {value!r} or remove it from your YAML'
            )
    if len(world.options.music_tracks.value) > 16:
        raise ValueError('At most 16 requested R3 tracks')
    from .settings import settings
    from ..shared.locations import ACTIVE
    from ..shared.progression import validate

    validate(settings(world), location_count=len(ACTIVE))
    world.options.level_music_shuffle = LevelMusicShuffle(1 if mode == 1 else 0)
    world.options.overworld_music_shuffle = NativeMapMusic(
        world.options.overworld_music_shuffle.value
    )

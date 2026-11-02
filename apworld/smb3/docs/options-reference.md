<!-- SPDX-License-Identifier: MPL-2.0 -->
# Options reference

Choose these settings in Options Creator before your host generates the room.
Omitted YAML settings use their defaults. The game name and YAML section are
`Super Mario Bros. 3: Expanded Multiworld`. See the
[player guide](../../../docs/beta/player-guide.md) for setup and controls.

## Levels and progression

| Setting / YAML key | Default | What it changes |
| --- | --- | --- |
| Level Shuffle / `level_shuffle` | `vanilla` | Vanilla keeps original levels in place. Balanced shuffles 53 eligible ordinary stages within the same or neighboring original worlds. Compatible uses the whole eligible pool, including distant worlds. Required entrances, exits and routes stay compatible; some stages remain fixed. Balanced refers to world proximity, not equal difficulty. |
| Special Stage Shuffle / `special_stage_shuffle` | `off` | `by_type` mixes supported special stages within their kind. `mixed_fortresses` also exchanges regular stages and fortresses. Both require Balanced or Compatible Level Shuffle. |
| World Pass Placement / `world_pass_placement` | `staggered` | Favors earlier-world access and later placement of a Regional Hammer than its matching Pass. Starting items and fixed placements can override this pacing. `unrestricted` removes that pacing preference. Minimal Accessibility may require Unrestricted. |
| Hammer Mode / `hammer_mode` | `regional` | Regional gives reusable world-specific rock-breaking permissions. `legacy` uses consumable Hammers from inventory. World Pass access is still required. |
| Victory Condition / `goal` | `standard` | Standard requires the ending. `all_koopalings` adds all seven Koopaling bosses. `all_locations` adds all 125 reward checks. Bowser is victory-only in every mode. |
| Star Fragment Access Gate / `star_hunt_mode` | `off` | `world_8` requires Fragments plus the World 8 Pass to travel there. `bowser` gates the final castle instead. Neither changes your selected victory condition. |
| Star Fragments Required / `star_fragments_required` | `12` | Number needed by the enabled Star gate, 1–255; cannot exceed Total. Ignored when the gate is Off. |
| Star Fragments Total / `star_fragments_total` | `20` | Number placed in the multiworld, 1–255; must be at least Required and fit the available reward pool. Ignored when the gate is Off. |

Use the [map progression pages](../../../docs/beta/player-guide.md#progression-pages)
to see received Passes, Hammers, Fragments and checks during play.

## Hazards, traps and helpful effects

**Optional hazards — limited coverage in this beta:** Poison Mushrooms affect
selected eligible blocks; Angry Sun adds encounters only in supported stages.
Both default to Off, and neither affects every block or level. Placement feedback
is welcome. Read the [player explanation](../../../docs/beta/player-guide.md#optional-hazards--limited-coverage-in-this-beta).

| Setting / YAML key | Default | What it changes |
| --- | --- | --- |
| Poison Mushrooms / `poison_mushrooms` | `off` | `rare`, `normal`, `chaos` give eligible blocks 5%, 15%, 35% chances of harmful mushrooms. Only selected blocks can change; essential power-ups stay safe. |
| Angry Sun / `angry_sun` | `off` | `rare`, `normal`, `chaos` increasingly add Suns to supported stages, at most one extra Sun per stage. Off adds none. |
| Trap Frequency / `trap_frequency` | `off` | `light`, `normal`, `heavy`, `chaos` target 10%, 20%, 30%, 40% replacement of eligible regular rewards, subject to item reserves and available filler. Traps include Forced Small, Walking Only, Micro-Goomba Infestation and Icy Feet. They can trigger during jumps/combat and cause death. |
| Blessings / `blessings` | `false` | Adds one Starman effect and one Emergency Mushroom effect. The latter turns Small into Super while preserving stronger suits. Effects activate later rather than becoming selectable inventory items; activation can briefly stutter. |
| DeathLink / `death_link` | `false` | Shares deaths with other participants who enable it. An incoming death can cost a life. |
| Trap Warning / `trap_warning` | `show` | `hide` conceals advance trap notices inside SMB3X until activation. Other clients may reveal the item. Blessings, normal rewards and save errors remain visible. |

## Appearance and music

| Setting / YAML key | Default | What it changes |
| --- | --- | --- |
| Treasure Appearance / `reward_visual_style` | `mystery` | Neutral reward-object appearance. `vanilla` uses original art. Neither reveals or changes the assigned reward. |
| Player Appearance / `player_appearance` | `mario` | `luigi` changes appearance only; movement and abilities are unchanged. |
| Palette Mode / `palette_mode` | `original` | Atmospheric mixes original colors with environment themes; Full allows a wider and bolder range. YAML: `atmospheric` or `full`. |
| Level Music / `level_music` | `vanilla` | `shuffled` rearranges original SMB3 level music. |
| World Map Music / `overworld_music_shuffle` | `vanilla` | `shuffled` permutes the eight original map themes independently of Level Music. |

This release supports original or shuffled SMB3 music.

## Example: shuffled stages and music

This changes a few settings; everything else uses its default:

```yaml
name: ColorShuffle
game: "Super Mario Bros. 3: Expanded Multiworld"

"Super Mario Bros. 3: Expanded Multiworld":
  level_shuffle: balanced
  hammer_mode: regional
  palette_mode: atmospheric
  level_music: shuffled
```

## Shared Archipelago settings

Progression Balancing helps multiplayer players receive useful items sooner; it
does not change solo play. Accessibility chooses all checks (**Full**, default)
or only the goal (**Minimal**). Review World Pass Placement if choosing Minimal.

Options Creator also offers standard starting inventory, starting hints, local/
non-local items, excluded/priority locations, item links and item placement tools.
These can constrain generation; coordinate unusual combinations with your host.
They do not make an already-generated room change when you edit the YAML later.

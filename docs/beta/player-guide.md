<!-- SPDX-License-Identifier: MPL-2.0 -->
# Player guide

This is the current guide for playing SMB3X. Hosts can use the
[host guide](host-guide.md); generation choices are in the
[options reference](../../apworld/smb3/docs/options-reference.md).

## Requirements and installation

- Windows x64 and official **Archipelago 0.6.8**.
- **BizHawk 2.10, 2.11 or 2.11.1**. Keep your existing installation, including
  unrelated cores, plugins and language files. SMB3X verifies the executable and
  critical dependencies and configures **NesHawk** automatically.
- Your own clean **SMB3 USA Revision A** ROM. See [ROM compatibility](#rom-compatibility)
  if it is refused. No game ROM or emulator is included.

These files have different jobs:

| File | What you do with it |
| --- | --- |
| `smb3x.apworld` | Install the SMB3X integration through Archipelago Launcher. |
| Player `.yaml` | Send your name and generation choices to the room host. |
| Player `.apsmb3x` | Open your own generated game; keep it to continue later. |
| Original SMB3 `.nes` ROM | Supply it locally when asked; it is used to build your game. |

Download `smb3x.apworld` from the [0.36.2 beta release](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.2-beta.1).
Open it with Archipelago Launcher and complete installation, then **restart Launcher**.

## Creating options and joining a room

Open **Options Creator** in Launcher and choose
**Super Mario Bros. 3: Expanded Multiworld**. Enter your player name, choose your
settings and export a YAML. Send it to your host, who generates the room using
the matching APWorld. Choose a name distinct from the other players' names.

For a minimal hand-written YAML, save the following as `YourPlayerName.yaml`.
Settings omitted from it use their defaults:

```yaml
name: YourPlayerName
game: "Super Mario Bros. 3: Expanded Multiworld"

"Super Mario Bros. 3: Expanded Multiworld":
  level_shuffle: vanilla
```

After generation, download **your own** `.apsmb3x` from the room or ask your host
for it. Keep the file. The host also supplies the room address and any password.
Generating a game and starting its server are separate steps; see
[hosting](host-guide.md) if you are doing both.

Level and world-map music can each use original or shuffled SMB3 tracks.

## Starting the game and connecting

1. Choose **Open Patch** in Archipelago Launcher and select your `.apsmb3x`.
2. Select your clean ROM and your existing BizHawk `EmuHawk.exe` when prompted.
   The launcher remembers valid selections and can offer the previous emulator
   for a new game. It manages the NES core and required settings for you.
3. On first setup you can import your BizHawk controller/audio/video preferences
   or use supported defaults. An optional Windows file-association prompt only
   changes how future `.apsmb3x` files open; it is not required for play.
4. Enter the room address and password if asked. The address may already be in
   the player file or remembered locally. **Your player/slot name is read from
   the player file**; the managed launcher does not ask you to type it again.
5. When BizHawk reaches the title screen, press the NES **Start** button to begin.
   Continue the normal start sequence to the world map. The initial checkpoint
   cannot be made while you are waiting at the title screen.
6. The game may pause automatically while connecting. On the settled world map,
   wait for the connection and successful save notification before playing.

Keyboard and gamepad mappings are configured in **BizHawk's controller settings**.
The button names below are NES buttons, not universal PC keyboard shortcuts.

## Controls and menus

Map menus require Mario/Luigi to be standing still, outside inventory and other
animations. If a save or item delivery is in progress, wait for it to finish.

| Where | Button | Action |
| --- | --- | --- |
| Settled world map | Start | Open progression pages. |
| Progression pages | Left / Right | Previous / next page. |
| Progression pages | B / Start | Close and return to the map. |
| World Passes page | A | Open world travel. |
| Settled world map | Select | Open world travel directly. |
| World travel | Left / Right, then A | Select a world and confirm travel. |
| World travel | B | Cancel; return to the map, or to Passes if opened from that page. |
| World travel | Start | Close to the map. |
| Hammer page | A: Try Rock | Attempt an adjacent rock using the current world's Regional Hammer. |
| Settled world map | B | Open stored-item inventory. |
| Item inventory | Left / Right; Up / Down | Select an item in the row; change rows. |
| Item inventory | A | Use the selected stored item. |
| Item inventory | B / Start | Close inventory. |
| Ordinary level | Start | Pause / resume the level. |
| Supported paused level | Select | Show / hide read-only status. |
| Paused status | Left / Right | Change status page. |
| Paused status | B / Select | Hide the panel; the game stays paused. |
| Paused status | Start | Hide the panel and resume. |

### Progression pages

**Start** opens World Passes. Cycle with Left/Right through **World Passes →
Hammers → Star Hunt → Item Checks**. Star Hunt is skipped when the Star Fragment
gate is Off, leaving three pages instead of four.

- **World Passes** shows your current world, access to all eight worlds, and total
  reward checks completed. `Y` means owned; `-` means missing. These are ownership
  markers, not instructions to press a Y button. Press A here for travel.
- **Hammers** shows ownership for Desert (W2), Water (W3), Giant (W4) and Ice (W6),
  plus the current world's permission. Other worlds have no Regional Hammer.
  With Legacy Hammers selected, this page directs you to the item inventory.
- **Star Hunt** shows Fragments received / required, whether the threshold is met,
  and whether it gates World 8 travel or Bowser's Castle. Fragments are permanent.
- **Item Checks** shows completed / total reward checks for the current physical
  world and all worlds. With shuffled stages, a check belongs to the map position
  you entered, not the original world of the level inside. Bowser is not an item
  check, and releasing remaining items through the server does not clear levels.

The paused read-only display has Checks, Passes, Hammers and, if enabled, Stars.
It shows the last confirmed status and may be stale while disconnected; updates
come from the map. It cannot travel or use Hammers. Some special scenes do not
support this display even when the game is paused.

## World travel, progression items and inventory

### World Passes and travel

World 1 is available initially. Receiving a **World Pass** gives access to its
world. On the settled map press Select, use Left/Right to move the `>` selection
arrow, then A to travel. A on the current world simply closes the menu.
B cancels; Start closes it. You can also enter travel from the Passes page.

A missing Pass locks its destination. Completing an airship **does not substitute
for receiving the next world's Pass**. Your next useful progression item may be
in another player's game. If Star Hunt gates World 8, travel there requires both
its Pass and the required Fragments. The Bowser-only Star gate leaves travel
unchanged and instead restricts the final castle.

### Regional Hammers: try a rock

Regional Hammers are reusable permissions for W2, W3, W4 and W6. They do not
remove every rock automatically when received.

1. In the matching world, stand still on a walkable map position **immediately
   next to a breakable rock**: above, below, left or right of it.
2. Press Start, then Right to reach Hammers.
3. If you own that world's Hammer, press **A: Try Rock**. The menu closes and the
   native rock-breaking action runs. The permission remains available afterward.

If **MOVE ON MAP FOR HAMMER** appears, close the menu and move to another
settled map position before opening the Hammer page again.

You do not aim by holding a direction or by facing the rock. The native action
checks **above, below, left, then right** and breaks the first suitable adjacent
rock. Move to another adjacent map position if the intended rock is not targeted.
An attempt can do nothing if no breakable rock is next to you, the region's Hammer
is missing, the world has no Regional Hammer, or the map is busy. Wait for movement,
menus, saving or effects to settle before retrying.

With **Legacy Hammers**, select a Hammer in the ordinary item inventory and press
A next to a rock. A successful use consumes a Hammer. Regional permissions and
consumable Legacy Hammers are different settings; neither replaces World Passes.

### Stored items

On the settled map, press **B**. Use Left/Right to select an item and Up/Down to
change rows; press A to use it. Close with B or Start. Items are used from the
map, not from the paused read-only display. Some items can be refused if their
effect is not usable in the current situation.

Repeated items share a slot with a quantity beneath it. The displayed `99!` means
**100 or more**, not exactly 99. Using one reduces the stored quantity; the slot
remains while any are left. Progression Passes, Regional Hammers and Fragments
are shown on progression pages rather than spent from this inventory.

For example, open B inventory and use a Leaf before entering a level. After
receiving a World 3 Pass, use Select travel to visit Water Land. After receiving
its Regional Hammer, stand next to a Water Land rock and try it from Hammers.

## Optional hazards — limited coverage in this beta

Poison Mushrooms can replace power-ups in selected eligible blocks, while the
Angry Sun option adds extra Suns to supported stages. These options do not affect
every block or level. Coverage and placement are areas for future improvement;
reports of unexpected behavior or problematic placements are welcome. Both
options are off by default. These add hazards to the original game; they do not
replace its ordinary enemies. Their probability settings apply only to eligible
blocks or supported stages; see the [options reference](../../apworld/smb3/docs/options-reference.md#hazards-traps-and-helpful-effects).

## Saving and continuing

After progress, return to a settled world map, close menus and **wait for the
successful save notification**. Moving around the map or opening a menu does not
necessarily create a save. Closing the emulator **does not guarantee another
save**; unsaved mid-level progress may be lost.

To continue, reopen the **same `.apsmb3x`** with Launcher. It restores the latest
verified checkpoint and reconnects. Keep the same supported BizHawk version used
for that game. There is no Save & Quit button or exact crash-time recovery.

Avoid emulator reset, rewind and arbitrary manual savestate loading. Do not copy
saves between games or manually migrate a session. If an error appears, preserve
your player file and save data and [report it](troubleshooting.md#report-a-bug)
instead of deleting data to force a restart.

## Hints and chat

The managed SMB3X connection handles game items and checks; it does not offer the
full Archipelago chat/hint interface. For that, optionally open **Text Client**
in official Archipelago Launcher alongside SMB3X:

1. Connect to the same room with `/connect host:port` (use the host's actual
   address and port). Enter your slot name and room password when requested.
   Use the same generated player name as SMB3X; the Text Client can coexist with
   the game connection.
2. Type ordinary text to chat. `/help` lists client commands; `!help` lists room
   commands. `!hint` shows your hints/points; `!hint World 3 Pass` requests an item
   hint subject to the room's hint cost. `!hint_location World 1-1 Clear` requests
   a location hint. `/received` lists received items.

This client is optional. External clients may reveal incoming trap names even
when SMB3X's **Trap Warning: Hide** conceals advance notices. See official
[AP 0.6.8 client](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/CommonClient.py)
and [room commands](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/MultiServer.py)
for command definitions.

## Troubleshooting and updates

Use [troubleshooting and update instructions](troubleshooting.md) for connection,
emulator, ROM and save errors. [Known limitations](known-limitations.md) lists the
current boundaries. Keep the APWorld version used by your host in mind when
joining a new room; updating an installation does not rewrite an existing game.

SMB3X (`smb3x`, `.apsmb3x`) and the independent SMB3 proof of concept (`smb3`,
`.apsmb3`) can coexist. Their player files and clients are separate. Install only
one implementation of the older `worlds.smb3` namespace at a time.

### ROM compatibility

Supply SMB3 **USA Revision A** in iNES1 format: mapper 4, 393232 bytes, with no
trainer, battery flag or trailing data. Payload SHA1:
`BB894D104C796F69BA16587EB66C0275F5C2FC02`; CRC32: `2E6301ED`.
These are payload checks, not the whole-file SHA256. SMB3X checks the image during
local preparation. It neither provides nor downloads ROMs. Prepared ROMs and BPS
stay local and must not be shared as release or room downloads.

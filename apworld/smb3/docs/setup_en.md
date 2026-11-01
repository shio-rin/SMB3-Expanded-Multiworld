# Player guide

Use official Archipelago 0.6.8 and the supported Windows BizHawk 2.10/NesHawk
build. SMB3X verifies the emulator and core files before startup. Other revisions
may be refused even if their window says 2.10.

## Original ROM

You supply the original USA Revision A image: an iNES1 mapper-4 file of 393232
bytes, with no trainer, battery flag or extra trailer. Its payload SHA1 is
`BB894D104C796F69BA16587EB66C0275F5C2FC02` (CRC32 `2E6301ED`).
Unsupported images fail validation; the project does not provide or download ROMs.
The modified ROM is constructed locally. Keep ROMs and saves private.

## Installation and generation

Open the APWorld with Archipelago Launcher, allow its ordinary APWorld install,
and restart Launcher. Generate a template for Super Mario Bros. 3: Expanded
Multiworld; set your name and options, then generate with your room's other YAMLs.
The room host needs the APWorld but no SMB3 ROM. Open your generated `.apsmb3x`
with Launcher, select the ROM and EmuHawk executable, and enter the room address,
slot name and password if requested. A server-waiting message means the client
has not yet received a valid room connection; check the address and room status.

## Checkpoints and Resume

The client coordinates native progress, inventory and indexed reward history.
After meaningful progress, return to a settled overworld, close menus and wait
for the saved notice. Opening menus or merely moving on the map does not force
another save. Ordinary window close does not promise an extra checkpoint.
Reopen the **same player file** to Resume from the latest verified checkpoint.
There is no Save & Quit controller shortcut, rewind, reset, manual State loading,
or exact recovery at the instant of a mid-level crash.

Existing games keep their exact hash-bound runtime. Never copy journals between
games, remove ownership records to bypass errors, or transplant checkpoints into
a new release. A mismatched player/runtime/save stops safely and retains files.

## Features and limits

All eight worlds, World Passes, Regional or consumable Hammers, optional Star
Fragments, victory goals, original level shuffle (53 certified stages),
reviewed special-stage and Mixed Fortress shuffle, Poison Mushrooms, Angry Suns,
six item effects, DeathLink and native inventory/movement are supported.
Some uncertified rooms stay native. Original is the default palette; Atmospheric
and Full are optional. Level and overworld music each offer Vanilla or Shuffled
original SMB3 music. Private soundtrack modes are unavailable in this build;
unsupported custom YAML refuses instead of silently substituting native music.

SMB3X uses `.apsmb3x`. The separately tested SMB3 proof of concept uses `.apsmb3`;
they are different games with different clients. Only one implementation of the
older `worlds.smb3` namespace can be installed at a time. No historical room
or checkpoint migration is supported.

## Troubleshooting

Managed data is under `%LOCALAPPDATA%\SMB3XAP`: settings, hash-bound `cache`,
and `sessions`. A session's `runs` directories contain client/emulator logs and
`lua-diagnostics.log` with bounded backups. Keep these files when reporting a
problem; redact server addresses, player/room details and personal paths first.

If the world is absent, confirm the official AP version and restart Launcher.
If a ROM is refused, check the exact revision/container above. If an emulator is
refused, use the supported core build. A resource error requires reinstalling
the matching APWorld; do not edit the cache. If a second open is refused, close
the existing client/error window normally. Do not delete locks while it is live.
If startup stops at an identity or native marker check, keep the logs and player
file and report it. Never bypass the check. First-launch dialogs/controller setup
and every third-party APWorld combination are not exhaustively certified.

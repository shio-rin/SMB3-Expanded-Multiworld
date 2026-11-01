<!-- SPDX-License-Identifier: MPL-2.0 -->
# Host guide — beta 0.36.2

Use official Archipelago **0.6.8** and install the same verified `smb3x.apworld`
as your SMB3X players. Restart Launcher. Hosts need no SMB3 ROM or emulator to
generate or host a room.

Generate fresh 0.36.2 player files for the corrected launcher; existing rooms and
saved sessions retain their original runtime and must not be migrated manually.

1. Ask each player to export fresh YAML from Options Creator. The SMB3X game name
   and YAML section key are exactly `Super Mario Bros. 3: Expanded Multiworld`.
2. Place the YAMLs in your Archipelago `Players` folder (or select the intended
   player directory in your normal generation workflow). Install the correct
   APWorld for every other game in the room too.
3. Run Archipelago Generate. Keep its standard `AP_....zip` output and verify that
   generation succeeds before distributing player files.
4. Host its `.archipelago` with Archipelago Server, or upload the standard generation
   ZIP to an appropriate Archipelago host. Share the room address and assigned
   slot names privately with the participants.
5. Give each SMB3X player their own `.apsmb3x` from that output or the room's download
   page. They use [Launcher/Open Patch](player-guide.md#install-and-play).

Vanilla is the default level shuffle; Balanced and Compatible are supported.
Removed legacy selectors are not valid substitutes. Prefer Options Creator exports
and ordinary native Vanilla/Shuffled music; private external music packs are absent.
See [options](../options.md) for progression, optional effects and victory settings.

A generated SMB3X player container has AP/session metadata, not a ROM, BPS, emulator
or State. Generation needs no ROM. A local prepared-game folder is different:
it contains locally built ROM/BPS and managed runtime/save data and must never
be uploaded as a room or release download. Prepared BPS files include original
CHR data and must remain local.

Do not distribute private diagnostic rooms or historical sessions as sample seeds.
Do not modify played room settings or migrate saved games to this beta. SMB3X and
the independent SMB3 proof of concept can coexist under their distinct namespaces;
that does not certify every third-party APWorld combination.

Report SMB3X issues through [GitHub Issues](https://github.com/shio-rin/SMB3-Expanded-Multiworld/issues)
with [redacted diagnostics](troubleshooting.md#report-a-bug).

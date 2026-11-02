<!-- SPDX-License-Identifier: MPL-2.0 -->
# Host guide

A host collects player choices, generates the multiworld, and runs or arranges
its server. You need **official Archipelago 0.6.8** and the matching SMB3X APWorld
for generation. You do not need another player's ROM or BizHawk installation.

## Generate the room

1. Install `smb3x.apworld` through Launcher and restart it. Install the matching
   integrations for other games in the room as well.
2. Collect one YAML per player. SMB3X players can export from Options Creator or
   use the [minimal example](player-guide.md#creating-options-and-joining-a-room).
   The game and section name are **Super Mario Bros. 3: Expanded Multiworld**.
3. Put the YAMLs in your chosen `Players` directory and run **Generate** through
   Launcher. Use the normal player-directory selection if you keep rooms separate.
4. Check that generation succeeds. Keep the resulting `AP_....zip` output and
   give each player their own `.apsmb3x`; it identifies their generated slot.

Use the same SMB3X APWorld version for the host and players starting this room.
The [options reference](../../apworld/smb3/docs/options-reference.md) explains defaults
and dependencies. Changing YAML after generation does not change that room.

## Host and connect

Open the generated `.archipelago` server data using **Archipelago Server**, or
upload the standard generated ZIP to a compatible Archipelago hosting service.
A local server must stay running for players to connect. Share its actual port,
room address and any password privately with participants.

On the same PC, a client can use `localhost:port` or `127.0.0.1:port`. Remote
players need an address that reaches the host, such as the hosting service's
room address or a correctly configured public host address. **Do not give remote
players localhost**: it refers to their own PC. Direct home hosting may require
firewall/router setup; use a hosted room if that is unfamiliar.

Players open their assigned `.apsmb3x` through Launcher/Open Patch and supply
their own ROM locally. Their slot name comes from that file. If a downloaded file
has no usable server address, give them the room's address for the prompt.

## Which files to share

| Output | Use |
| --- | --- |
| Each player's `.apsmb3x` | Give it to that player or let them download it from the room. |
| `.archipelago` | Server data for the host/hosting service; keep the host's data private. |
| Generated `AP_....zip` | Standard input for a compatible hosting service; it can include spoiler information. |
| Spoiler text | Share only if the group wants spoilers. |
| Local prepared ROM/BPS, States, managed sessions | Never distribute these as room or release files. |

A player container contains metadata, not a ROM or emulator. Generation needs no
ROM. Do not use private test rooms or already-played sessions as sample rooms.
For updating an existing room, read [updates](troubleshooting.md#updating) before
changing anything. For player setup, use the [player guide](player-guide.md).

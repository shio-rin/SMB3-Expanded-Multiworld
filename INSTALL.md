<!-- SPDX-License-Identifier: MPL-2.0 -->
# Install SMB3X

Follow the current [step-by-step player guide](docs/beta/player-guide.md).

Requirements: Windows x64, official Archipelago **0.6.8**, complete BizHawk
**2.10 / 2.11 / 2.11.1** with **NesHawk**, and your own verified clean SMB3 USA
Revision A ROM. Install `smb3x.apworld`, restart Launcher, export YAML through
Options Creator, and obtain your room's player-specific `.apsmb3x`.
Open it with **Launcher → Open Patch**, choose the ROM and EmuHawk, connect,
and wait for the initial verified checkpoint. Keep the same player file and
emulator/core version for Resume.

The exact YAML game key is `Super Mario Bros. 3: Expanded Multiworld`.
SMB3X uses namespace `smb3x` and `.apsmb3x`; the independent SMB3 proof of concept
uses `smb3` and `.apsmb3`. They can coexist in the same AP installation. Do not
install two different implementations of the older `smb3` namespace together.

No Python/Lua development setup is required. No downloadable full ROM is supplied.
Normal close does not guarantee an additional save. See the player guide before
resuming or changing emulator installations.

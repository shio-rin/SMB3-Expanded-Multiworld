<!-- SPDX-License-Identifier: MPL-2.0 -->
# Super Mario Bros. 3: Expanded Multiworld

SMB3X connects Super Mario Bros. 3 to Archipelago. Clear levels and other
locations to send rewards, receive progression and items from your room, and
explore all eight original worlds. There are 125 reward locations; Bowser is
victory-only. No Nintendo ROM or private soundtrack is included.

**Local release candidate: publication holds remain; original project code uses MPL-2.0.**
This source tree is a new repository with no private development history.
See [NOTICE.md](NOTICE.md) for the exact remaining material-specific questions.

## Play

Requires Windows, official **Archipelago 0.6.8** and **BizHawk 2.10, 2.11 or 2.11.1 / NesHawk** (M35 compatibility matrix in [docs/emulator-qualification.md](docs/emulator-qualification.md)).
Supply your own verified SMB3 USA Revision A ROM. Packaging needs no ROM.

1. Install `smb3x.apworld` by opening it with Archipelago Launcher. Restart Launcher.
2. Generate the game's YAML template through Launcher, edit your player name and
   settings, and generate your Archipelago game normally. The host needs no ROM.
3. Host the generated room by your usual Archipelago method. Give each player
   their own `.apsmb3x` file from the generated ZIP.
4. Open your `.apsmb3x` with Launcher. Select your original ROM, supported
   EmuHawk executable and room address when prompted. Keep this player file.
5. Wait for the client to connect and finish its initial checkpoint before playing.

[Player guide](docs/player-guide.md) covers setup, saving and troubleshooting.
[Options](docs/options.md) describes supported settings.
[Architecture](ARCHITECTURE.md), [codebase walkthrough](CODEBASE_GUIDE.md),
[development setup](DEVELOPMENT.md), [testing](TESTING.md), [build from source](BUILDING.md) and [contributing](CONTRIBUTING.md) cover development.

## Development and testing disclosure

Substantial implementation, testing, investigation and documentation were produced
with **OpenAI Codex and ChatGPT assistance under human direction**. Human input
includes design decisions and targeted gameplay testing. Automated native fixtures
sometimes assist navigation or approach positioning; they do not establish a
human full-campaign or every-option certification. This is a free, open-source
release proposal, subject to the outstanding scope and approval decisions in NOTICE.

Unofficial; no affiliation with or endorsement by Nintendo, Archipelago, BizHawk
or OpenAI is implied. Names identify compatibility.

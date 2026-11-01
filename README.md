<!-- SPDX-License-Identifier: MPL-2.0 -->
# Super Mario Bros. 3: Expanded Multiworld (SMB3X)

Explore all eight SMB3 worlds in Archipelago: clear 125 randomized reward checks,
send items to your multiworld, and unlock progress with World Passes and Regional
Hammers. Bowser is victory-only. Choose Vanilla, Balanced or Compatible original
level shuffle, stacked inventory, native menus, optional hazards, traps, Blessings
and DeathLink, original/shuffled native music, palette modes and cosmetic Luigi.

**First beta staged for owner review. This repository stays Private and the
GitHub Release stays an unpublished draft until separately authorized.**
APWorld **0.36.0**, candidate **36.0.0-rc1**, proposed tag **v0.36.0-beta.1**.

## Start playing

You need Windows x64, official **Archipelago 0.6.8**, a complete **BizHawk 2.10,
2.11 or 2.11.1** installation using **NesHawk**, and your own clean SMB3 USA Rev A
ROM. No ROM or emulator is supplied. Game files are built locally from your ROM.

1. Obtain the verified `smb3x.apworld` from the approved beta assets, install it
   with Archipelago Launcher, then restart Launcher.
2. Open Options Creator, choose **Super Mario Bros. 3: Expanded Multiworld**,
   set your player name/options, and export YAML for your host.
3. Download your own `.apsmb3x` from your generated room. Use Launcher's
   **Open Patch**, select that file, then select your clean ROM and supported
   `EmuHawk.exe` when prompted.
4. Connect to the room and wait for the initial verified checkpoint. Play normally.
   Reopen the same player file to Resume from the latest verified checkpoint.

[Installation](INSTALL.md) · [Player guide](docs/beta/player-guide.md) ·
[Host guide](docs/beta/host-guide.md) · [Troubleshooting](docs/beta/troubleshooting.md) ·
[Known limitations](docs/beta/known-limitations.md) · [Options](docs/options.md)

Normal close does not guarantee an extra save. Keep the original emulator/core
version for each existing game; do not transplant States or reset/rewind/load
arbitrary States. SMB3X and the independent SMB3 proof of concept can coexist.

## Development, support and licensing

[Report bugs through GitHub Issues](https://github.com/shio-rin/SMB3-Expanded-Multiworld/issues).
Follow [reporting instructions](docs/beta/troubleshooting.md#report-a-bug) and
[SECURITY.md](SECURITY.md); never attach ROMs, States or private session files.

[Build](BUILDING.md) · [Development](DEVELOPMENT.md) · [Testing](TESTING.md) ·
[Architecture](ARCHITECTURE.md) · [Codebase](CODEBASE_GUIDE.md) ·
[Contributing](CONTRIBUTING.md) · [Beta notes](docs/beta/release-notes.md)

MPL-2.0 covers the established original-code scope only. Read
[NOTICE.md](NOTICE.md), [LICENSE-SCOPE.json](LICENSE-SCOPE.json),
[third-party notices](THIRD_PARTY_NOTICES.md) and the current
[scope/status addendum](docs/beta/licensing.md). Three documented native
adaptation groups have unresolved copyright interpretations; no legal clearance
is claimed. Attribution does not establish permission for third-party expression.

Substantial implementation, testing and documentation used **OpenAI Codex and
ChatGPT assistance under human direction**. Targeted human testing and assisted
automated fixtures do not establish exhaustive multiplayer, every option
combination, or a complete human eight-world campaign.

Free and unofficial; unaffiliated with Nintendo, Archipelago, BizHawk or OpenAI.
Names identify compatibility. See [release provenance](docs/beta/provenance.md)
for the exact packaged source and the separate documentation revision. Historical
package-bound guides remain unchanged for reproduction; the beta guides linked
above are the current installation instructions.

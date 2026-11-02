<!-- SPDX-License-Identifier: MPL-2.0 -->
# SMB3X — First Public Beta

**[APWorld 0.36.2 / v0.36.2-beta.1](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.2-beta.1) — beta prerelease**

Explore all eight SMB3 worlds with 125 randomized reward checks and Archipelago
multiworld delivery. World Passes open travel; reusable Regional Hammers open
rock routes. Choose level and special-stage shuffling, stacked inventory, native
progression menus, optional hazards/traps/Blessings/DeathLink, palettes, original
or shuffled SMB3 music and cosmetic Luigi. Bowser is victory-only.

## Start here

Install the APWorld with official Archipelago 0.6.8 Launcher and restart it.
Windows x64 and an existing BizHawk 2.10, 2.11 or 2.11.1 installation are supported;
the launcher configures NesHawk. Supply your own clean SMB3 USA Rev A ROM.
No ROM or emulator is included, and game files are built locally.

Follow the **[player guide](player-guide.md)** for setup, title-screen Start,
controls, World Pass travel, Regional Hammer positioning, inventory, saving and
optional hints/chat. Hosts use the [host guide](host-guide.md).

## BizHawk compatibility correction

Existing installations can contain unrelated cores, language files and plugins.
Optional unrelated components may be absent. The executable and critical
NES/client/Lua dependencies remain verified, along with core/sync settings and
save compatibility. Genuine mismatches get a specific error and a retry/stop
choice. A pristine folder or emulator reinstall is not required.

To use this correction, start a newly generated 0.36.2 player file. Already-generated
files retain their original runtime. Keep existing saved games and their emulator
versions; do not delete or manually migrate them. See [updating](troubleshooting.md#updating).
The maintainer confirmed the corrected launcher works with their existing installation.

## Saving and limits

Return to the settled map, close menus and wait for a successful save notice.
Normal close does not guarantee an extra checkpoint. Reopen the same player file
to continue with the same BizHawk version. Unsaved mid-level progress may be lost;
reset/rewind/manual State recovery and cross-version saves are unsupported.

See [known limitations](known-limitations.md) for shuffle and testing boundaries.

## Verification and source

The accepted package has 211 maintained tests, independent review, two identical
clean-source builds, seven generation and complete ROM comparisons, and fresh
check/reward/consumption/checkpoint/Resume tests on all three supported BizHawk
versions with mixed installations. Native tests used scripted/assisted navigation
and test-only normal exit; no exhaustive human multiplayer or campaign coverage
is claimed. This documentation update does not rebuild or change that package.

[Provenance](provenance.md) records the source commit and exact artifact hashes.
See [licensing](licensing.md) for MPL scope, attribution and native-material
exceptions. The maintainer's AI disclosure is in the [README](../../README.md).
SMB3X is unofficial and unaffiliated with Nintendo or the named tool projects.

[Report bugs](troubleshooting.md#report-a-bug) with steps and redacted log excerpts.
Never attach ROMs, BPS, States, whole sessions or credentials.

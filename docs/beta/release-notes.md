<!-- SPDX-License-Identifier: MPL-2.0 -->
# SMB3X — First Public Beta

**Prepared prerelease — unpublished draft for owner review.** Beta tag
`v0.36.2-beta.1`; APWorld `0.36.2`, sealed candidate `36.0.2-rc1`.

Explore all eight Super Mario Bros. 3 worlds with **125 randomized reward checks**
and Archipelago multiworld item delivery. Unlock permanent progression with
World Passes and Regional Hammers; choose Vanilla, Balanced or Compatible original
level shuffle. Stacked inventory and native menus support optional hazards, traps,
Blessings, DeathLink, accepted victory modes, palette modes, cosmetic Luigi and
Vanilla/Shuffled native level and overworld music. Bowser is victory-only.

Supported: Windows x64, official Archipelago **0.6.8**, supported BizHawk **2.10,
2.11 or 2.11.1** using **NesHawk**, and a player-supplied SMB3 USA Rev A ROM.
No ROM or emulator is bundled. Game files are constructed locally.

Install `smb3x.apworld` through Launcher and restart it. Export YAML from Options
Creator using **Super Mario Bros. 3: Expanded Multiworld**, generate/join a room,
and open your `.apsmb3x` through Launcher/Open Patch. Select your clean ROM and
supported EmuHawk, connect and wait for the initial verified checkpoint.
See the included `INSTALLATION.md` and the repository's current beta player/host guides.

Managed automatic checkpoints and cold Resume retain verified progress and indexed
items. Normal close does not guarantee an extra save. Reopen the same player file
with its original emulator/core version. No cross-version savestate migration,
arbitrary State loading, reset/rewind recovery or exact mid-level crash restoration.
Private soundtrack modes are unavailable; use native music. Some rooms retain
native content under certified shuffle boundaries.

The launcher now supports existing functional BizHawk installations. Unrelated
cores (including puae), language assemblies and plugins do not cause arbitrary
rejection; optional unrelated components may also be absent. Exact executable,
critical NES/client/Lua dependencies, core/sync settings and session ownership
remain verified. Specific loading collisions and incompatible loader policies
still reject with actionable errors. Known failures retain detailed logs without
a duplicate fatal traceback. No emulator reinstall or directory cleanup is needed.

Generate a **fresh 0.36.2 player file** to use the corrected launcher. Existing
player files remain bound to their original runtime. Preserve old sessions and
caches; never delete or manually migrate them. The owner personally confirmed the
corrected launcher works with their existing BizHawk installation; this is a
scoped startup acceptance, not a complete human campaign certification.

211 maintained tests passed, independently rerun by Sol High. Two clean-source
builds reproduced the exact archive. Fresh real-server check/reward/consumption,
checkpoint and cold Resume passed with mixed installations on BizHawk 2.10,
2.11 and 2.11.1 / NesHawk. The 2.10 run used a complete byte-identical copy of the
owner's 7,100-file installation, retaining every extra file. Seven generation and
seven full ROM comparisons match M36; 59 installation/identity cases, 48 negative/
preservation cases, 21 native effects/DeathLink probes and three OpenAL probes pass.
Native tests use assisted navigation/goal approach and test-only client.exit
closure. They do not certify exhaustive human multiplayer, every option combination,
desktop controller setup or a complete human eight-world campaign. This staging
update reuses that evidence and the sealed candidate without a new runtime build.

Packaged source and tag target: `7a4438a840116d279ff9688ded1c0e1b7f26d3fb`.
APWorld SHA256: `88e4766294c4ed6687229114069d6d4d7d228b6bc6e68b8fd65f1c351f9a60e3`.
Resource SHA256: `eba4e81d449afe232867d4d73d5b5ce27000b99aa623ebe9ea596a4b1f1fc3e4`.
Recipe SHA256: `058cda0522e5e9c6aaadf681b95584c113652a63f010ba6a2b8a9d1c2896631c`.
Python runtime `m36-python-3`; native `m26-native-2`; slot release `m27-1`.
Later main-branch documentation is outside package inputs. The tag preserves exact
build provenance; use current main-branch guides and the attached INSTALLATION.md.
Historical `v0.36.0-beta.1` remains available for traceability.

MPL-2.0 applies only to the established original-source scope. Existing notices
and exceptions remain: the house/inventory, Angry Sun and sound-restoration native
adaptation groups have unresolved copyright interpretations; no legal clearance
is claimed. Attribution does not establish permission. See NOTICE.md,
LICENSE-SCOPE.json, THIRD_PARTY_NOTICES.md and the beta licensing addendum.

Substantial development/testing/documentation used OpenAI Codex and ChatGPT under
human direction. Free and unofficial; unaffiliated with Nintendo, Archipelago,
BizHawk or OpenAI. Report bugs through
[GitHub Issues](https://github.com/shio-rin/SMB3-Expanded-Multiworld/issues), with
versions, reproduction steps and redacted logs. Never attach ROMs, prepared BPS,
States, player files, server saves, private music or session credentials.

<!-- SPDX-License-Identifier: MPL-2.0 -->
# SMB3X â€” First Public Beta

**Prepared prerelease â€” unpublished draft for owner review.** Proposed tag
`v0.36.0-beta.1`; APWorld `0.36.0`, sealed candidate `36.0.0-rc1`.

Explore all eight Super Mario Bros. 3 worlds with **125 randomized reward checks**
and Archipelago multiworld item delivery. Unlock permanent progression with
World Passes and Regional Hammers; choose Vanilla, Balanced or Compatible original
level shuffle. Stacked inventory and native menus support optional hazards, traps,
Blessings, DeathLink, accepted victory modes, palette modes, cosmetic Luigi and
Vanilla/Shuffled native level and overworld music. Bowser is victory-only.

Supported: Windows x64, official Archipelago **0.6.8**, complete BizHawk **2.10,
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

190 maintained tests and clean-source archive reproduction pass. A new isolated
official AP 0.6.8 / BizHawk 2.11.1 NesHawk smoke test passed Options Creator,
generation, a physical check, indexed item/consumption, checkpoint, ordinary
client.exit closure and cold Resume without a duplicate item. Selectors/navigation
were assisted; this is not desktop mouse/controller acceptance. Independent M36
verification covers seven representative generation/ROM comparisons and all three
emulator versions. Tests include assisted native fixtures; exhaustive human
multiplayer, every option combination and a full human campaign are not claimed.

Source commit: `cf90296511a46174e8daf1a634acb3127f457c51`.
APWorld SHA256: `8a67704da88446e48e091b801542fff5bc2c8bb5f6aa7a8f27597bbb22e1afe9`.
Resource SHA256: `65d8d65db3b1f3a30ba5f76d19a5f7800c560604f09175388902fb063afc6e83`.
The display tag does not renumber runtime identities. Later main-branch beta
documentation is outside packaged inputs; see the provenance guide.

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

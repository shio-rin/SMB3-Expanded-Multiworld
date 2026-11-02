<!-- SPDX-License-Identifier: MPL-2.0 -->
# Beta source and artifact provenance

Pending first beta: **v0.36.2-beta.1**, APWorld **0.36.2**, candidate **36.0.2-rc1**.
The tag points exactly to packaged source `7a4438a840116d279ff9688ded1c0e1b7f26d3fb`.
The accepted fix branch ends at `2dfac2dcf5f1dd2de4f41159c6acbf0ba51bc3c6`;
main integrates that history and adds current beta documentation. These subsequent
documentation changes are outside the package recipe. The tag source retains the
historical documentation snapshot; use the current main README/beta guides and
attached installation instructions for the pending beta.

| Identity | Exact value |
| --- | --- |
| APWorld SHA256 | `88e4766294c4ed6687229114069d6d4d7d228b6bc6e68b8fd65f1c351f9a60e3` |
| Resource SHA256 | `eba4e81d449afe232867d4d73d5b5ce27000b99aa623ebe9ea596a4b1f1fc3e4` |
| Recipe SHA256 | `058cda0522e5e9c6aaadf681b95584c113652a63f010ba6a2b8a9d1c2896631c` |
| Python / native / slot | m36-python-3 / m26-native-2 / m27-1 |
| Resources / ZIP entries | 220 / 232 |

The sealed candidate is reused unchanged. Two separate clean-source builds with
Python 3.12.14 / zlib 1.3.2 reproduce every byte. Check out the packaged commit and
follow BUILDING.md; source tests also require lupa. Building at a later documentation
commit changes build-source.json and must not replace the sealed archive under
its existing hash. No production/resource changes are part of this staging update.

The accepted correction has 211 maintained tests, independent Sol High review,
seven deterministic generation/ROM comparisons, mixed-installation native check,
indexed reward, consumption, checkpoint and cold Resume on all three supported
versions, effects/DeathLink and exact session/version ownership checks. See
[bizhawk-practical-installations.md](bizhawk-practical-installations.md) for scope.
The owner also confirmed startup with their existing installation; no exhaustive
human campaign or multiplayer claim follows.

Only four assets are staged: smb3x.apworld, SHA256SUMS.txt, INSTALLATION.md and
RELEASE-NOTES.md. Generated rooms, ROMs, prepared BPS, States, emulator binaries,
private music, credentials and internal evidence are excluded. MPL scope and
third-party disclosures remain intact. See the [README](../../README.md) for current release availability.

The old v0.36.0-beta.1 tag remains at
`cf90296511a46174e8daf1a634acb3127f457c51`; its sealed M36 archive and the sealed
M36.1 correction remain preserved locally. The active draft now uses the new tag.

## Which documents are current?

The authoritative player guide is [beta/player-guide.md](player-guide.md).
[INSTALL.md](../../INSTALL.md), the README and older editable setup pages lead
there. Current host instructions are [host-guide.md](host-guide.md); the current
options reference is [options-reference.md](../../apworld/smb3/docs/options-reference.md).

Four Markdown files remain pinned by the sealed package recipe: `NOTICE.md`,
`docs/player-guide.md`, `docs/host-guide.md` and `docs/options.md`. Their unchanged
bytes preserve the accepted package, including historical wording. They are not
the current setup/navigation entry points. Do not refresh recipe hashes to edit
these snapshots. On the next otherwise-required release, consider updating their
packaged text to point to the current guides and replacing obsolete startup,
slot-name, availability and internal-option descriptions. No new runtime build is
needed for this repository documentation sweep.

Historical correction reports, `docs/m32/stages.md`, `docs/validation.md` and older
CHANGELOG entries record scoped evidence, not a current release checklist.
The working APWorld, resource recipe, tags and existing draft assets stay fixed.
Updated draft-document copies are prepared locally for a separate asset update;
this documentation PR does not upload them.

<!-- SPDX-License-Identifier: MPL-2.0 -->
# SMB3X — Beta 0.36.3

**[APWorld 0.36.3 / v0.36.3-beta.1](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.3-beta.1) — beta prerelease**

## What's fixed

- **Consecutive N-Spade games.** Fixed a potential input lock when another
  matching-card game starts immediately after the previous one. An interrupted
  save opportunity now defers safely so you can finish the next encounter,
  return to the map and save. Legal roaming Hammer Bros. chains were also checked.
- **Fortress traps.** Scheduled traps retain their appropriate delay through
  fortress doorway transitions. Activation still depends on the effect and
  actual gameplay context, including technical and safety restrictions.
- **Earlier victory completion.** Archipelago recognizes and submits victory
  at authenticated credits entry. You can receive confirmation without finishing
  the credits or pressing another button at THE END. Standard, All Koopalings
  and All Locations retain their requirements. Durable completion evidence and
  safe reconnection are preserved, and credits and post-ending play continue normally.

## Existing games

To use these fixes, generate a new SMB3X game using APWorld 0.36.3. Existing games continue using their original runtime and can be finished normally. Do not delete or manually migrate saved sessions.

## Installation and saving

Use official **Archipelago 0.6.8** on Windows x64 and **BizHawk 2.10, 2.11 or
2.11.1 / NesHawk**. Your existing supported BizHawk installation can retain
unrelated cores, plugins and language files. Supply your own clean SMB3 USA
Revision A ROM.

Install `smb3x.apworld` through Launcher, restart Launcher, and generate a new game.
Open your `.apsmb3x` through **Launcher → Open Patch**. Follow the
[player guide](player-guide.md) for setup, Start/Select menus, Regional Hammers,
inventory and saving.

Return to a settled map, close menus and wait for the successful save notice.
Ordinary close does not guarantee another checkpoint. Reopen the same player file
with the same BizHawk version for cold Resume. Unsaved mid-level progress may be
lost. If you close during credits, confirmed completion is retained separately
while gameplay resumes from the latest verified checkpoint. See
[known limitations](known-limitations.md).

## Verification and source

The accepted hotfix passed 235 maintained tests, focused actual native checks on
the three supported BizHawk versions, clean-source reproduction and independent
review. The owner additionally completed a World 8-focused gameplay test with no
issues observed. This covers the tested scenarios, with scripted or assisted
navigation used for native checks. Exhaustive campaign and multiplayer coverage
are not claimed.

The APWorld is the original sealed 36.0.3-rc2 package, reused byte-for-byte.
The release tag identifies packaged source
`a630e1f5a7a56f6da2c94c75185acc34b3333843`. Later documentation commits are separate.
[Provenance](provenance.md) records exact hashes. The
[previous beta](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.2-beta.1)
remains available.

See [licensing](licensing.md) for MPL scope, attribution and native-material
exceptions. The maintainer's AI disclosure is in the [README](../../README.md).
SMB3X is unofficial and unaffiliated with Nintendo or the named tool projects.

[Report bugs](troubleshooting.md#report-a-bug) with steps and redacted log excerpts.
Never attach ROMs, BPS, States, whole sessions or credentials.

<!-- SPDX-License-Identifier: MPL-2.0 -->
# Known limitations

- Supported play uses Windows x64, AP 0.6.8 and BizHawk 2.10, 2.11 or 2.11.1 with
  NesHawk. Existing installations can include unrelated cores, plugins and language
  files; critical dependencies remain verified. Other versions/platforms are untested.
- Saves are made at safe states, not continuously. Normal close does not force a
  save, and unsaved mid-level progress can be lost. There is no Save & Quit button,
  arbitrary savestate recovery or cross-version save migration.
- Some stage entrances and rooms remain in their original arrangement. Shuffling
  keeps the entry/exit and routing restrictions described in the
  [options reference](../../apworld/smb3/docs/options-reference.md).
- Hints/chat require an optional Text Client. External clients may reveal traps
  even when advance warnings are hidden in SMB3X.
- Gameplay tests include scripted navigation and goal approach. They do not cover
  every option combination, controller setup, multiplayer group or full campaign.

## Optional hazards — limited coverage in this beta

Poison Mushrooms only affect selected eligible blocks, and extra Angry Suns only
appear in supported stages. Both options default to Off; neither covers every
block or level. Reports of unexpected behavior or problematic placements are
welcome. See the [player guide](player-guide.md#optional-hazards--limited-coverage-in-this-beta)
for details.

[Player guide](player-guide.md) · [Troubleshooting](troubleshooting.md) ·
[Licensing and material-specific exceptions](licensing.md)

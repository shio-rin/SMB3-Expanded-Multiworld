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
- External soundtracks, World 9 and Classic Level Packs are not supported.
- Hints/chat require an optional Text Client. External clients may reveal traps
  even when advance warnings are hidden in SMB3X.
- Gameplay tests include scripted navigation and goal approach. They do not cover
  every option combination, controller setup, multiplayer group or full campaign.

[Player guide](player-guide.md) · [Troubleshooting](troubleshooting.md) ·
[Licensing and material-specific exceptions](licensing.md)

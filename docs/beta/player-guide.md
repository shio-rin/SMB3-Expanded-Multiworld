<!-- SPDX-License-Identifier: MPL-2.0 -->
# Player guide — beta 0.36.0

## Requirements

- Windows x64; engineering fixtures used Windows 10. The owner separately reports
  a successful BizHawk 2.11.1 check and cold Resume on Windows 11.
- Official Archipelago **0.6.8**.
- A complete supported BizHawk **2.10, 2.11 or 2.11.1** installation with NesHawk.
  Keep its DLLs and supporting files together; other builds may be refused.
- Your own clean **Super Mario Bros. 3 USA Revision A** ROM.
- `smb3x.apworld` and your generated room's player-specific `.apsmb3x`.

The ROM must be an iNES1 mapper-4 file, 393232 bytes, with no trainer, battery flag
or extra trailer. Payload SHA1: `BB894D104C796F69BA16587EB66C0275F5C2FC02`;
payload CRC32: `2E6301ED`. SMB3X validates it during preparation. It does not
provide or download ROMs. The patched ROM and BPS are created **locally only**.

## Install and play

1. Obtain the beta `smb3x.apworld` and compare its SHA256 with `SHA256SUMS.txt`.
   During owner review these assets are private; a draft is not a public download.
2. Open the APWorld with Archipelago Launcher and complete normal APWorld installation.
3. Close and restart Launcher so it loads the newly installed game.
4. Open **Options Creator**. Choose **Super Mario Bros. 3: Expanded Multiworld**,
   enter your player name, select your options, and export your YAML.
5. Send that YAML to your host, or generate your own room using the same APWorld.
   The [host guide](host-guide.md) explains generation and hosting.
6. Download your own `.apsmb3x` from the generated room/output archive. Keep it.
7. In Archipelago Launcher choose **Open Patch** and select that player file.
8. When prompted, select your clean SMB3 USA Rev A ROM.
9. Select the supported installation's `EmuHawk.exe`. Use **NesHawk**, not QuickNES.
10. Enter the room address, slot name and password if requested. Wait for connection
    and the **initial verified checkpoint** before playing.
11. Play normally. After meaningful progress, return to a settled overworld,
    close menus and wait for the saved notice.
12. Close normally. Reopen the **same `.apsmb3x`** to Resume.

The exact YAML structure is:

```yaml
name: YourPlayerName
game: 'Super Mario Bros. 3: Expanded Multiworld'
'Super Mario Bros. 3: Expanded Multiworld':
  level_shuffle: vanilla
```

Prefer fresh Options Creator exports. The selector displays **Vanilla → Balanced
→ Compatible**, default Vanilla. Use ordinary Vanilla/Shuffled native music.
External custom soundtrack modes are unavailable in this build; they are not
recommended for ordinary seeds and unsupported settings are refused.

## Checkpoints and Resume

Automatic safe checkpoints coordinate native progress, inventory and AP reward
history at supported states. Merely moving on the map or opening menus does not
force a save. **Normal close does not guarantee an extra checkpoint.** Restart
uses the most recent verified checkpoint, which may precede your latest position
or unsaved mid-level progress. There is no Save & Quit controller shortcut.

Keep the player file and the whole managed session folder. Each game is tied to
its original verified emulator/core version and resource identity. Cross-version
State migration is unsupported. Do not transplant savestates, journals or caches,
reset/rewind, or load arbitrary States to recover progress. Do not delete identity
records or locks to bypass a refusal. Preserve evidence and report errors.

## Other SMB3 integrations

SMB3X (`smb3x`, `.apsmb3x`) can coexist with the independent SMB3 proof of concept
(`smb3`, `.apsmb3`) in one AP installation. Their clients, player files and sessions
are separate. Only one implementation of the older `worlds.smb3` namespace can
be installed at a time. Old SMB3X games retain their embedded runtime; no historical
room/save migration is promised by installing this beta.

[Options](../options.md) · [Troubleshooting](troubleshooting.md) ·
[Known limitations](known-limitations.md)

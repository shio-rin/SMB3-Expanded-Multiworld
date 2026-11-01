<!-- SPDX-License-Identifier: MPL-2.0 -->
# Troubleshooting and bug reports

| Symptom | Action |
|---|---|
| SMB3X absent from Launcher/Creator | Confirm official AP 0.6.8, install the verified APWorld and restart Launcher. |
| ROM refused | Check USA Rev A and the exact format/hash in the player guide; do not bypass validation. |
| Emulator refused | Use a complete supported 2.10, 2.11 or 2.11.1 release and NesHawk, with its original DLLs. |
| Existing game refuses a new emulator | Reopen with that game's original emulator/core version. Cross-version Resume is unsupported. |
| Waiting for AP server | Check room status, address, slot name and password. Wait for validated connection/checkpoint. |
| Resource/identity/native marker error | Preserve files and logs; reinstall the matching APWorld or report the error. Never edit the cache or ownership records. |
| Duplicate open refused | Close the existing game/client/error window normally. Do not delete live locks. |
| Latest movement absent after Resume | Normal close does not add a save; Resume uses the latest verified checkpoint. |
| Save failure/uncertain operation | Stop normal play, preserve evidence, and report it. Do not reset, rewind or load arbitrary States. |

Managed data normally lives under `%LOCALAPPDATA%\SMB3XAP`: settings, hash-bound
cache and sessions. Session `runs` contain client/emulator logs and bounded
`lua-diagnostics.log` backups. Do not clear this directory to troubleshoot a played
game. Work on redacted copies only.

## Report a bug

Use [GitHub Issues](https://github.com/shio-rin/SMB3-Expanded-Multiworld/issues/new?template=bug_report.md).
State expected/actual behavior, reproduction steps, APWorld version/SHA256,
Windows edition/build, AP version, exact BizHawk version, and fresh game versus
Resume. Mention selected options and any fixture assistance. Attach only relevant
redacted text excerpts, not entire managed folders.

Never post ROMs, patches/BPS, States, journals, server saves, player files, private
music, passwords, tokens, room addresses/identities or personal filesystem paths.
Keep originals intact. See [security reporting](../../SECURITY.md) for sensitive
issues. GitHub Issues will require authorized repository access while it is Private.

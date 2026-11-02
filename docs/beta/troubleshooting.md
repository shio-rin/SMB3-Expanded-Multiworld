<!-- SPDX-License-Identifier: MPL-2.0 -->
# Troubleshooting and updates

Start with the visible message or symptom. Preserve your files if something
fails; do not delete save data to bypass an error.

## Installation and starting

| Symptom | Action |
| --- | --- |
| SMB3X is missing from Launcher or Options Creator | Check official AP 0.6.8, install the APWorld, then fully restart Launcher. |
| ROM is refused | Check [USA Rev A compatibility](player-guide.md#rom-compatibility); do not use a prepatched image. |
| Emulator is refused | Read the named critical file, loader policy or setting in the error. Supported versions are 2.10, 2.11 and 2.11.1. Unrelated cores/plugins/language files may stay; they are not a reason to clean or reinstall BizHawk. Choose another installation only if the named critical components are incompatible. |
| No initial save at the title screen | Press NES Start and proceed to the world map. The first checkpoint is available there, after connection. |
| An older player file still rejects unrelated DLLs | Read [Updating](#updating). Installing a new APWorld does not replace an older game's launcher runtime. |
| Game opens paused | Read the connection/save message. An automatic connection or save pause must finish before play. If the message says the restored game is paused, unpause BizHawk normally. |

The launcher configures NesHawk automatically. Keyboard/gamepad controls are your
BizHawk controller mappings. [Map menus and paused status](player-guide.md#controls-and-menus)
use NES button names.

## Connecting and playing

| Symptom | Action |
| --- | --- |
| Waiting for the AP server | Confirm that the room/server is running, the address and port are correct, and the password matches. Your slot name is already in your player file. |
| Remote player cannot use localhost | Use the reachable address provided by the host; localhost means the player's own PC. |
| World remains locked after an airship | Check World Passes. Airship completion does not replace the destination Pass. World 8 may also require Fragments. |
| Regional Hammer does nothing | Stand still directly next to a breakable rock in the matching world; use Start → Hammers → A. Read [positioning](player-guide.md#regional-hammers-try-a-rock). |
| Status panel does not open | Start pauses an ordinary level; then Select toggles the read-only panel. Some special scenes do not support it. |
| Need hints or chat | Use the optional [official Text Client](player-guide.md#hints-and-chat). |

## Saving and continuing

| Symptom | Action |
| --- | --- |
| Latest movement or mid-level progress is missing | Resume restores the latest successful checkpoint. Normal close does not force another save. Return to the settled map, close menus and wait for the saved notice after progress. |
| Existing game refuses a different emulator version | Use the same version that created the game. Cross-version save loading is not supported. |
| Resource, ownership or native marker error | Keep the player file and session data. Record the message and report it; use the matching APWorld/runtime rather than editing caches or identity records. |
| Duplicate open is refused | Close the existing game/client or error window normally. Do not delete a lock while a process is running. |
| Save failed or an operation is uncertain | Stop play, preserve the error/logs and report it. Do not reset, rewind or load a manual State to recover. |

## Updating

Install an updated APWorld through Launcher and restart Launcher. Use the version
requested by your host for a **new** room. Already-generated `.apsmb3x` files
remain bound to their original runtime, and already-started games keep their
original save and emulator-version requirements. An APWorld update does not
rewrite those player files or migrate their saves.

For the 0.36.2 BizHawk compatibility correction, generate a **new room/player
file with 0.36.2** to use the corrected launcher. Keep your existing BizHawk
installation. Preserve older player files, caches and saved sessions; never delete
or transplant them to make an old game use the new runtime. See
[release notes](release-notes.md) for this beta's changes.

## Find the logs

Logs are optional when reporting a problem; we may ask for an excerpt while
investigating. Managed data normally lives at `%LOCALAPPDATA%\SMB3XAP` in Windows.
Each game has a folder under `sessions`, with `client.log` and per-run emulator
logs and bounded `lua-diagnostics.log` backups in `runs`. The error dialog may identify the session.
If asked for logs, use the latest run showing the problem.

Advanced save/runtime details are in [Architecture](../../ARCHITECTURE.md),
[Codebase guide](../../CODEBASE_GUIDE.md) and
[emulator contracts](../emulator-qualification.md).

## Report a bug

Bugs, suggestions and playthrough feedback are welcome on
[GitHub Issues](https://github.com/shio-rin/SMB3-Expanded-Multiworld/issues).
Describe what happened and what you were doing; you don't need a diagnosis or
reliable reproduction steps. Screenshots, error messages, settings or versions
are helpful if known, not required.

Don't upload ROMs, saves, passwords or whole session folders; remove personal
information from logs. For sensitive vulnerabilities, use [Security](../../SECURITY.md).

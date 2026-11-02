<!-- SPDX-License-Identifier: MPL-2.0 -->
# Emulator profiles and qualification

The supported profiles are Windows x64 **BizHawk 2.10, 2.11 and 2.11.1** with
NesHawk. This guide describes their loading, configuration and save contracts for
contributors; players should start with the [player guide](beta/player-guide.md).

Recorded native tests cover managed checks, rewards, inventory consumption,
connection interruptions and cold Resume. The 0.36.2 correction adds mixed-installation
coverage and dependency-focused validation. Automation used Windows 10 Pro 22H2;
targeted human reports also cover Windows 11. Those results do not qualify other
versions/platforms or every configuration. See [provenance](beta/provenance.md)
and the linked historical qualification records for evidence scope.

`shared/emulators.py` identifies the executable by SHA256 and verifies the reviewed
NES/client/Lua dependencies. Unrelated cores, plugins and language files may be
present or absent. See the [0.36.2 dependency design and owner retest](beta/bizhawk-practical-installations.md).
`launcher/config/emulators.json` records the dependency selection separately from
the stable session fingerprint, configuration and State contracts. No emulator
binary is packaged. Each session stores its exact emulator identity before creating a
native lifetime. Cross-version Resume is unsupported in every direction. Reopen
the same player file with its original emulator; do not delete or edit saves.

2.10 State uses Core.bin. 2.11/2.11.1 use Core.bin.zst and SyncSettings.json.
The validator selects these names and BizVersion.txt from the trusted session
profile, never from a State's claims. Newer State sync settings must match the
verified profile exactly, and compressed core headers must have the expected format. All prior marker, CRC, resource, witness,
receipt, epoch and exact native restore checks still apply. Lua compares the
observed version and Lua API version with Python's verified run control.

Managed configurations have explicit version headers and reviewed frontend
additions; NesHawk core/sync settings and the existing palette remain unchanged.
Preferences are isolated by installation path **and revision**. Import only from
the selected version, or use supported defaults. Late-closing games retain the
existing three-way merge protection.

## Qualifying another release

1. Download a complete official release into a new isolated directory. Record
   its URL, archive SHA256, executable revision and complete DLL inventory.
2. Inspect tagged config/NesHawk changes. Create a version-specific baseline;
   compare critical settings before and after actual normal emulator closure.
3. Test Lua 5.4, official AP0.6.8 LuaSocket/JSON, memory domains/hashes, read/write,
   execution callbacks, registers, frames, pause, and actual State save/load.
4. Inspect State members, version text and namespaced marker. Add only the
   format actually observed; never infer cross-version compatibility.
5. Run fresh managed launch, physical check, indexed reward, consumption,
   checkpoint, offline delivery/reconnect and two cold Resumes independently.
   Run effect/DeathLink tests and targeted native checks for changed behavior.
6. Test corrupt binaries/config/ROM/State, missing APIs, all cross-version
   refusals and historical dispatch. Record actual OS scope.
7. Review the explicit profile/resource recipe changes, run deterministic build,
   generation/ROM comparisons and independent verification before advertising it.

There is no hash-refresh tool that approves a new emulator merely because its
files can be hashed. Do not change old caches or migrate played sessions.

M36 requests built-in colors using a null Palette; local explicit palettes remain validated preferences. No RGB table is bundled.

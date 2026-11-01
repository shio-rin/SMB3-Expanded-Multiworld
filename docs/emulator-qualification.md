<!-- SPDX-License-Identifier: MPL-2.0 -->
# Emulator profiles and qualification

M35 registers the official Windows x64 **2.10, 2.11 and 2.11.1** installations.
All three pass the M35 managed check/reward/consumption, offline/reconnect and
two-cold-Resume fixtures. The private handoff records evidence and limitations.
Independent Sol verification passed for both M35 and M36. The M36 membership evidence correction did not change the source or package. Tests run on Windows 10 Pro 22H2; The owner reports one successful fresh 2.11.1 Windows 11 check and cold Resume; broader Windows 11 acceptance is not inferred. Other versions/platforms are not approved automatically.

`shared/emulators.py` identifies the executable by SHA256, then verifies every
file in the official DLL directory. `launcher/config/emulators.json` holds the
reviewed identities, config filename and State requirements. No emulator binary
is packaged. Each session stores its exact emulator identity before creating a
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

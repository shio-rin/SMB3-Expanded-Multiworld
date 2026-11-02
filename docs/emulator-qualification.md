<!-- SPDX-License-Identifier: MPL-2.0 -->
# Emulator profiles and qualification

This contributor guide covers supported Windows x64 **BizHawk 2.10, 2.11 and
2.11.1 / NesHawk** profiles. Players should use the [player guide](beta/player-guide.md).

## Dependency-focused validation

[shared/emulators.py](../src/smb3x/shared/emulators.py) pins the exact supported
EmuHawk.exe and verifies the NES/client/Lua execution dependencies, not equality
with an entire official ZIP directory. Unrelated cores, plugins and language
resources may be present or absent: their names and bytes are not validation
inputs. The maintained dependency lists and hashes are in
[launcher/config/emulators.json](../src/smb3x/launcher/config/emulators.json).
`validation_files` lists required components; `frontend_files` adds OpenAL load
targets only when that audio backend is selected. No emulator binary is packaged.

The selection combines tagged upstream source with observed managed/native
loading during NES, Lua and State operations. [Program's startup checks](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.EmuHawk/Program.cs)
require all eleven shared BizHawk assemblies, including DiscSystem. [NesHawk](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Emulation.Cores/Consoles/Nintendo/NES/NES.Core.cs)
runs in Emulation.Cores and uses blip_buf for audio. Lua/API startup requires
NLua, lua54 and SQLite helpers; hashing and State storage use libbizhash/libzstd.
Normal rendering, input and audio also need their reviewed frontend dependencies.
Optional core discovery tolerates missing unrelated types; discovering a managed
type does not by itself make that core a NES dependency. Platform .NET/VC runtimes
and graphics drivers remain prerequisites outside this installation hash contract.

## Loading collisions and configuration

.NET probes the application base, assembly-name subdirectories and .exe
alternatives before BizHawk's AssemblyResolve fallback to dll/. Native Win32 loads
also check the executable directory. A copy capable of shadowing a validated
dependency must match its hash; identical duplicates are allowed. Managed-only
probe forms are not applied to native DLLs. Unrelated names and locations do not
constitute collisions merely because they exist.

The selected executable's own .config controls CLR startup/loading policy.
Structural comparison guards redirection, probing/codeBase, external configuration
and assembly-manager changes while ignoring whitespace, comments, appSettings and
GC tuning. This also applies to renamed executable paths.

NesHawk core/sync settings and safety requirements are checked separately in
[launcher/preferences.py](../src/smb3x/launcher/preferences.py). Frontend preflight
runs before opening/resuming a checkpoint epoch or closing an owned emulator.
Expected incompatibilities give retry/stop choices and file-log tracebacks;
unknown implementation failures still propagate.

## Saved-session identity

`files` is the immutable serialized release fingerprint retained in session
identity; it is not a claim that every shipped file is required or observed.
`validation_files` is the separately reviewed subset actually checked at startup.
Keep these meanings distinct when changing profiles. See
[emulator_identity and require_session_emulator](../src/smb3x/launcher/emulator.py).

Every game retains its original emulator revision, core/configuration and runtime.
Cross-version Resume is unsupported in every direction. Historical player files
select their own exact cached runtime; never patch a cache or migrate States to
make a new validator apply to an existing game. Preferences are isolated by
installation path and revision, with three-way merging protecting newer edits.

2.10 States use Core.bin; 2.11/2.11.1 use Core.bin.zst and SyncSettings.json.
Validation selects these names and BizVersion.txt from the trusted session profile,
not from a State's claims. Sync settings, compressed headers, generation markers,
CRC, resources, native witnesses, receipts, epochs and exact restore checks remain
mandatory. Lua also checks the observed version/API against verified run control.

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

Managed configurations request built-in colors with a null Palette. Explicit local
palettes remain validated preferences; no RGB table is bundled.

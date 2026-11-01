<!-- SPDX-License-Identifier: MPL-2.0 -->
# Existing BizHawk installations: private 0.36.2 correction

> Historical correction/qualification snapshot. Current beta staging and installation
> instructions are in [provenance.md](provenance.md) and [player-guide.md](player-guide.md).

This candidate replaces whole-DLL-directory equality with dependency-focused
validation. It supersedes the 0.36.1 localization-only approach and its clean-folder
workaround. **Keep your existing BizHawk installation, including unrelated cores,
plugins and localization files.** No cleanup or reinstall is required.

APWorld **0.36.2**, private candidate **36.0.2-rc1**, Python runtime
`m36-python-3`; native runtime `m26-native-2` and slot release `m27-1` are unchanged.
The existing private beta draft, main branch and v0.36.0-beta.1 tag are untouched.

## Owner retest using the existing installation

1. Install this private candidate's `smb3x.apworld` through official Archipelago
   0.6.8 Launcher, then restart Launcher.
2. Generate one fresh disposable SMB3X room/player file using 0.36.2. Existing
   `.apsmb3x` files remain bound to their historical runtime; updating the APWorld does not
   replace their validator. Keep old player files and caches intact.
3. Open the new `.apsmb3x` with Launcher's Open Patch. Supply your clean SMB3 USA
   Rev A ROM and select **your existing EmuHawk.exe**, including its existing
   language assemblies and `puae.wbx.zst`. Choose your existing preferences or
   supported defaults as usual. Do not reinstall or remove files.
4. Connect, wait for the initial checkpoint, complete World 1-1 and receive/use
   a reward. Wait for the saved notice on the settled overworld; close normally
   and reopen the same player file to Resume. A normal close does not guarantee
   an additional save. This short check is sufficient; no campaign is requested.

If a real incompatibility is found, the dialog names the critical dependency,
loader policy or session mismatch. You may select another installation or stop
safely. Full technical traceback details remain in the session client.log. Known
compatibility errors do not produce an additional uncaught fatal traceback;
unknown programming failures still propagate. Canceling setup is quiet.

## Root cause and dependency design

M36 treated an official distribution inventory as an execution dependency closure.
M36.1 merely exempted thirteen hashes and still rejected an unrelated Amiga core.
Neither rule reflected what NesHawk loads. The original affected directory has
all official critical components unchanged; its extras are not incompatible.

The new validator never recursively inventories DLL directories and never hashes
unrelated additions. Presence, absence or content of an unrelated core/plugin or
satellite resource does not enter acceptance or session identity. The exact
supported EmuHawk executable remains pinned for 2.10, 2.11 and 2.11.1.

Dependency selection combines tagged upstream source with actual managed-assembly
and native-module observations during NES execution, Lua initialization and State
creation on all three versions. It is not generated from every shipped DLL:

- [Program's startup checks and assembly resolver](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.EmuHawk/Program.cs)
  require all eleven BizHawk shared assemblies, including DiscSystem, before NES
  selection. The resolver loads specifically requested assembly names from dll/.
- [NesHawk](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Emulation.Cores/Consoles/Nintendo/NES/NES.Core.cs)
  runs in Emulation.Cores; its audio uses blip_buf. Client Lua APIs require NLua,
  lua54, shared API assemblies and SQLite initialization; hashes and State storage
  use libbizhash and libzstd. Normal rendering/input/audio uses the observed
  Bizware, SDL, ImGui, Silk and Vortice dependencies and their managed helpers.
- CoreInventory tolerates missing optional core types. Virtu is loaded during
  type discovery when present but is an Apple II dependency; NES works without it.
  No .wbx.zst core, libquicknes, handheld core or other unrelated native core is
  required. Native minimal-installation probes removed 84–85 shipped files.
- OpenAL's additional load targets are verified only when that audio backend
  is selected. XAudio2 installations need not contain them. These are actual
  frontend dependencies, not an allowlist of arbitrary extra files.

The exact per-version selection is `validation_files` in
`src/smb3x/launcher/config/emulators.json`. Every selected file must match its
approved SHA256. The list contains 50/51/52 components respectively, including
EmuHawk.exe. Platform .NET/Windows/VC runtime and graphics drivers remain platform
prerequisites; this does not claim to hash or certify the operating system.

### Concrete loading collisions

.NET probes the application base (including assembly-name subdirectories and
.exe alternatives) before BizHawk's AssemblyResolve fallback. Native Win32 loads
also probe the executable directory. A file in one of those exact locations with
an audited dependency's name must match that dependency; identical duplicate
copies are accepted. Managed-only probe forms are not imposed on native DLLs.
Unrelated plugin names and paths are ignored.

The selected executable's `.config` controls CLR startup and assembly redirection.
Its startup/loading policy is compared structurally with the supported release,
including probing/codeBase/external config and assembly-manager directives.
Whitespace, comments, appSettings and GC tuning are not policy mismatches. The
actual selected filename is used, including when an executable has been renamed.
This prevents a modified loader policy from redirecting verified dependencies.

### Session and error contracts

The existing full profile `files` mapping is retained byte for byte as a stable
serialized release fingerprint. It is **not** a claim that all those files are
required or observed in the current installation. `validation_files` is separate.
No emulator revision, state interpretation, configuration fingerprint, durable
journal schema or receipt semantics changes. Cross-version Resume still rejects.
Historical files dispatch through their original exact cached runtime; no cache
is patched and no existing State is migrated.

Required NES core/sync settings and Lua bridge API/memory/callback guards remain.
Selected frontend verification occurs before opening/resuming a checkpoint epoch
or closing an owned emulator. Expected compatibility failures get explicit
retry/stop choices and file-log tracebacks; unexpected exceptions remain visible.

## Exact dependency inventory

A check mark indicates required for that supported version. Hashes remain in the
profile. Only the specifically selected OpenAL backend adds its frontend_files.

| File | 2.10 | 2.11 | 2.11.1 |
| --- | --- | --- | --- |
| `EmuHawk.exe` | yes | yes | yes |
| `dll/BizHawk.BizInvoke.dll` | yes | yes | yes |
| `dll/BizHawk.Bizware.Audio.dll` | yes | yes | yes |
| `dll/BizHawk.Bizware.Graphics.Controls.dll` | yes | yes | yes |
| `dll/BizHawk.Bizware.Graphics.dll` | yes | yes | yes |
| `dll/BizHawk.Bizware.Input.dll` | yes | yes | yes |
| `dll/BizHawk.Client.Common.dll` | yes | yes | yes |
| `dll/BizHawk.Common.dll` | yes | yes | yes |
| `dll/BizHawk.Emulation.Common.dll` | yes | yes | yes |
| `dll/BizHawk.Emulation.Cores.dll` | yes | yes | yes |
| `dll/BizHawk.Emulation.DiscSystem.dll` | yes | yes | yes |
| `dll/BizHawk.WinForms.Controls.dll` | yes | yes | yes |
| `dll/CommunityToolkit.HighPerformance.dll` | yes | yes | yes |
| `dll/Cyotek.Drawing.BitmapFont.dll` | yes | yes | yes |
| `dll/ImGui.NET.dll` | yes | yes | yes |
| `dll/Microsoft.Bcl.HashCode.dll` | yes | yes | yes |
| `dll/Microsoft.DotNet.PlatformAbstractions.dll` | — | — | yes |
| `dll/Microsoft.Extensions.DependencyModel.dll` | — | — | yes |
| `dll/NLua.dll` | yes | yes | yes |
| `dll/Newtonsoft.Json.dll` | yes | yes | yes |
| `dll/SDL2-CS.dll` | yes | yes | yes |
| `dll/SDL2.dll` | yes | yes | yes |
| `dll/SQLitePCLRaw.core.dll` | yes | yes | yes |
| `dll/SQLitePCLRaw.provider.e_sqlite3.dll` | yes | yes | yes |
| `dll/SharpGen.Runtime.COM.dll` | yes | yes | yes |
| `dll/SharpGen.Runtime.dll` | yes | yes | yes |
| `dll/Silk.NET.Core.dll` | yes | yes | yes |
| `dll/Silk.NET.OpenAL.dll` | yes | yes | yes |
| `dll/Silk.NET.OpenGL.dll` | yes | yes | yes |
| `dll/Silk.NET.WGL.Extensions.NV.dll` | yes | yes | yes |
| `dll/Silk.NET.WGL.dll` | yes | yes | yes |
| `dll/System.Buffers.dll` | yes | yes | yes |
| `dll/System.Collections.Immutable.dll` | yes | yes | yes |
| `dll/System.CommandLine.dll` | yes | yes | yes |
| `dll/System.ComponentModel.Annotations.dll` | yes | yes | — |
| `dll/System.Drawing.Common.dll` | yes | yes | yes |
| `dll/System.Memory.dll` | yes | yes | yes |
| `dll/System.Numerics.Vectors.dll` | yes | yes | yes |
| `dll/System.Runtime.CompilerServices.Unsafe.dll` | yes | yes | yes |
| `dll/System.Threading.Tasks.Extensions.dll` | — | yes | yes |
| `dll/Vortice.D3DCompiler.dll` | yes | yes | yes |
| `dll/Vortice.DXGI.dll` | yes | yes | yes |
| `dll/Vortice.Direct3D11.dll` | yes | yes | yes |
| `dll/Vortice.DirectX.dll` | yes | yes | yes |
| `dll/Vortice.Mathematics.dll` | yes | yes | yes |
| `dll/Vortice.MediaFoundation.dll` | yes | yes | yes |
| `dll/Vortice.XAudio2.dll` | yes | yes | yes |
| `dll/blip_buf.dll` | yes | yes | yes |
| `dll/cimgui.dll` | yes | yes | yes |
| `dll/e_sqlite3.dll` | yes | yes | yes |
| `dll/libbizhash.dll` | yes | yes | yes |
| `dll/libzstd.dll` | yes | yes | yes |
| `dll/lua54.dll` | yes | yes | yes |

## Sealed private candidate and reproduction

Packaged source: `7a4438a840116d279ff9688ded1c0e1b7f26d3fb`.
Later report-only documentation commits are outside the source recipe. Rebuild
from this exact commit to retain the same build-source provenance bytes.

| Identity | SHA256 |
| --- | --- |
| APWorld 0.36.2 / 36.0.2-rc1 | `88e4766294c4ed6687229114069d6d4d7d228b6bc6e68b8fd65f1c351f9a60e3` |
| Resource manifest | `eba4e81d449afe232867d4d73d5b5ce27000b99aa623ebe9ea596a4b1f1fc3e4` |
| Source recipe | `058cda0522e5e9c6aaadf681b95584c113652a63f010ba6a2b8a9d1c2896631c` |

Use Python 3.12.14 / zlib 1.3.2 for byte-identical ZIP compression, Git for source
identity, and lupa for the maintained tests. A ROM is not a package-build input.
From a clean clone, check out the packaged source commit, then run:

```text
git checkout 7a4438a840116d279ff9688ded1c0e1b7f26d3fb
python -B -m tools.check_source
python -B -m unittest discover -s tests
python -B -m tools.build_apworld ../smb3x.apworld
```

Choose a new output filename if it already exists; sealed outputs are retained.
Compare against the SHA256 above. The archive has 232 entries and 220 verified
resources. Six runtime resources changed from 0.36.1, plus three identity metadata
entries; 223 entries remain byte-identical. No native code, ROM patch, planning,
item/location IDs or gameplay data changed.

## Verification scope

The verification report accompanies the local private candidate. Native testing
uses fresh disposable rooms and byte-verified copies, including the complete
owner installation. Navigation and goal approach are scripted/assisted; genuine
native completion produces the check and the real server supplies the indexed
reward. No check bits, receipt acknowledgements or checkpoint records are injected.
Normal shutdown uses a test-only Lua `client.exit`, not a desktop close-button
click. This is not a new human-controller or full-campaign acceptance claim.

The first two dependency-inspection scripts failed in test-only .NET enumeration;
the corrected probe succeeded on all three versions. An initial source-check
command used the wrong working directory; both independent clean-clone builds
subsequently passed source checks with read-audit hooks rejecting private inputs.
All diagnostic attempts are retained outside distributable source/artifacts.

## Completed targeted verification

- **211 maintained tests pass**, independently rerun by GPT-6.1 Sol High.
- **59 real-file installation/identity cases** cover all three releases: official,
  language additions, authentic extra Amiga/handheld/core/plugin files, mixtures,
  missing optional components, actual critical byte changes/removals and collision
  paths. Maintained tests additionally cover arbitrary unseen names and prove
  extras are not recursively enumerated or hashed.
- The exact original 2.10 directory passes read-only identification with all
  extras present. A full **7,100-file** byte-identical copy passes managed startup,
  physical World 1-1 check, server publication, indexed Leaf reward, native
  consumption, durable checkpoint, ordinary shutdown and cold Resume. Every
  original file remains identical, including all thirteen satellites and puae.
- Mixed 2.11 and 2.11.1 installations pass the same complete sequence with several
  unrelated extras and optional shipped components absent. All six fresh/Resume
  processes exit successfully; consumed inventory stays consumed and the single
  indexed receipt is not duplicated. Latest checkpoint stores and resource caches
  verify independently after the runs.
- All six directed version changes reject at session ownership, State container,
  checkpoint binding and launch boundaries before process creation. The 48-case
  negative/preservation probe includes corrupt/missing State, wrong core/config,
  executable/core tampering and three unchanged fixture-session checks.
- **21 native effects/DeathLink probes** pass: six effects plus remote-death
  no-echo per version. These are actual native engine probes with a controlled
  test endpoint, not human multiplayer certification. **Three additional OpenAL
  NES/Lua/State probes** pass with OpenAL still selected after shutdown.
- All **seven official AP 0.6.8 generation comparisons** and **seven complete
  native ROM/BPS comparisons** match M36 byte for byte for the compared gameplay
  data. Runtime/resource identity deliberately changes; native patch output does
  not. Generated seed ZIPs contain only the normal multidata, player metadata and
  spoiler members; player containers contain only two JSON entries.
- **Two separate clean clones** reproduce the exact APWorld, with read-audit hooks
  recording zero private inputs. Every archive member, resource and source recipe
  mapping verifies. No ROM, prepared BPS, State, emulator DLL, private music, session
  evidence or credentials is included in the source changes or private candidate.
- Historical M36 and M36.1 cached-runtime dispatch and original validators remain
  unchanged in copied-runtime probes. Both sealed packages retain their original
  hashes. All 7,100 owner files and 136 files in the retained historical release/
  session manifest remain unchanged. Native tests declined file association
  registration; both registry trees in their execution account are unchanged.

Independent verification reviewed the dependency selection and corrected loading
collision/error-flow behavior, reran the maintained suite, accepted the unchanged
owner installation, checked committed package membership and both reproductions,
and inspected the retained native, generation and preservation evidence. It did
not claim a separate human-controller run or silently reuse historical saves.

Only the private fix branch is prepared for owner review. Main, the original beta
source tag, prior localization branch and all existing draft assets remain
unchanged. No release is published and no public distribution channel is enabled.

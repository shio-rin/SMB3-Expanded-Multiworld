<!-- SPDX-License-Identifier: MPL-2.0 -->
# Private BizHawk localization compatibility correction

> Historical correction/qualification snapshot. Current beta staging and installation
> instructions are in [provenance.md](provenance.md) and [player-guide.md](player-guide.md).

This branch prepares **APWorld 0.36.1 / 36.0.1-rc1**, Python runtime
`m36-python-2`. Native runtime `m26-native-2`, slot release `m27-1`, generation,
ROM output, checkpoint schemas and supported emulator versions are unchanged.
The existing 0.36.0 beta draft and `v0.36.0-beta.1` tag are not replaced.

## What changed

M36 required the discovered executable/DLL-tree inventory to equal the official
release inventory exactly and displayed only its first three differences. The
official Windows x64 ZIPs for 2.10, 2.11 and 2.11.1 omit System.CommandLine language
satellites, although matching optional Microsoft assemblies can accompany an
installation. Their presence therefore rejected otherwise matching required files.

The validator now admits only exact reviewed path/SHA256 pairs for thirteen
`dll/<culture>/System.CommandLine.resources.dll` files: cs, de, es, fr, it, ja,
ko, pl, pt-BR, ru, tr, zh-Hans and zh-Hant. Each may be present or absent.
2.10/2.11 use System.CommandLine 2.0.0-beta4.22272.1; 2.11.1 uses 2.0.3.
The matching netstandard2.0 parent DLL must retain its original required hash.
Profile metadata records the exact Microsoft NuGet package URL/hash used to
verify the satellite bytes. No upstream binaries are bundled with SMB3X.

This is not a wildcard exception for resources.dll. Modified satellites, other
cultures/paths, unknown assemblies and unexpected cores still reject. All required
file hashes and executable/version identities remain exact. Error messages list
all differences, grouped as missing required, modified required, modified optional
language resources and unapproved additions. Optional files do not enter or change
the required-file session identity; cross-version Resume remains prohibited.

The affected 2.10 folder inspected for this fix had **14** additions, not three:
13 verified satellites plus `dll/puae.wbx.zst`, which is absent from all three
approved official ZIPs. It has no missing or modified required files. The extra
core remains correctly rejected. Do not bypass the warning or modify played saves.

## Verify your previously failing 2.10 setup

1. Keep your current installation, old player files, managed cache and saves intact.
   Extract the complete official [BizHawk 2.10 Windows x64 ZIP](https://github.com/TASEmulators/BizHawk/releases/tag/2.10)
   into a **new, empty folder**. Do not extract over a folder containing older cores.
2. Obtain the private `36.0.1-rc1/smb3x.apworld`, install through official AP 0.6.8
   Launcher and restart Launcher. Use a separate AP installation for this test if
   you want to retain your normal installation unchanged.
3. Generate a **fresh disposable room/player file with 0.36.1**. Existing 0.36.0
   `.apsmb3x` files retain their embedded historical runtime; installing the new
   APWorld does not patch or migrate them. Do not alter their resource IDs/caches.
4. Open the new player file using that Launcher's Open Patch. Supply your clean
   SMB3 USA Rev A ROM and select the new folder's EmuHawk.exe with NesHawk.
   A setup containing only the thirteen exact matching language DLLs in addition
   to the official files is now also accepted. Do not copy other binaries across.
5. Connect, wait for the initial verified checkpoint, clear a level, receive a
   reward and wait for the saved notice on the settled overworld. Close normally,
   then reopen the same new player file with the same emulator to verify Resume.
6. If rejected, retain the complete categorized error. An unapproved
   `dll/puae.wbx.zst` warning means the selected directory is still mixed; select
   the clean directory from step 1. Do not remove ownership records, transplant
   States, reset or rewind to recover progress.

Normal close does not guarantee another save. This correction permits no new
emulator versions and does not migrate existing games. The repository remains
Private, the beta release remains unpublished, and branch review/merge and asset
replacement require separate owner authorization.

## Candidate identity and completed verification

The sealed candidate was built from source commit
`fba85f670020378c3cafb7e0db87dbde0d22c262`. This subsequent results update is
documentation only and is outside the package recipe. Reproduce the exact archive
from that source commit; building from a later documentation commit intentionally
changes the embedded source-provenance field.

| Identity | SHA256 |
| --- | --- |
| `smb3x.apworld` | `5e5b31e37237c53c726fff5928a5292722dee90f2b00c613ec12f5e478fb4ebe` |
| Resource manifest | `5653cbd457850ded5a9230a378f63ab4b6486b71b846497947d18fa933893087` |
| Source recipe | `298de2db3fb2b57d61efa56e50eb7cf3e9a73ce0acebf10b1607f4dc07b39d76` |

New verification completed for this correction:

- All **200 maintained tests** pass, including 25 emulator-profile tests.
- A separate clean clone reproduces the exact archive with no private build reads.
  All 220 resources and 232 ZIP entries verify. Only two resources changed; the
  other three changed entries contain package identity/provenance metadata.
- All required profile fields and required-file hashes are identical to M36.
  Real official-file tests reject 31 missing/modified/additional-file cases,
  including a 2.10 satellite incorrectly added to 2.11.1.
- Fresh official AP 0.6.8 / NesHawk runs pass on **2.10, 2.11 and 2.11.1**:
  real server, World 1-1 check, indexed Leaf delivery, native consumption,
  verified checkpoint, normal shutdown and cold Resume without restoring the
  consumed item. Each fresh launch has all thirteen satellites; each Resume has
  none. The 2.10 test uses the exact satellite bytes from the affected installation
  alongside its matching official required files, excluding the unapproved core.
- All six directed cross-version transitions reject at ownership, State,
  checkpoint-store and actual launch boundaries before process creation.
  The broader 48-case negative/preservation probe also rejects corrupt/missing
  States, unsafe core/configuration and executable/core tampering; all three
  new fixture sessions remain byte-identical after these negative probes.
- Seven actual generation comparisons preserve slot data, placements, options
  and RNG state. Seven complete generated ROMs and their local BPS outputs match
  M36 byte for byte across representative Vanilla/Balanced/Compatible, weighted,
  trigger, starting-inventory and plando cases. No ROM or BPS is distributed.
- Historical embedded-runtime dispatch retains M36's original validation. The
  sealed M36 archive, 136 files in the retained release/session preservation
  manifest, and all 149 executable/DLL-tree files in the affected installation
  remain unchanged. No historical cache or played game was migrated.

These are automated assisted native tests, not new human gameplay acceptance.
Creator/file selection and title/navigation/goal approach are programmatic;
no check bits, receipt acknowledgements or checkpoint records are injected.
Normal shutdown uses a test-only Lua `client.exit` request, not a desktop
close-button click. This does not claim exhaustive option or campaign coverage.

The APWorld is a new local private candidate. It is not attached to, and does not
replace assets in, the existing unpublished 0.36.0 beta draft.

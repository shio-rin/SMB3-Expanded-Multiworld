<!-- SPDX-License-Identifier: MPL-2.0 -->
# Beta source and artifact provenance

Proposed display tag: **v0.36.0-beta.1**. It points to packaged source commit
`cf90296511a46174e8daf1a634acb3127f457c51`, the original single-root M36 source.
The main branch's later documentation-only commit adds the current beta guides;
no recipe input or executable resource changes. The tag's source archive retains
the historical package-bound guides. Use the current beta guides linked from
main/README and the release notes for installation.

| Identity | Exact value |
|---|---|
| Candidate / APWorld | 36.0.0-rc1 / 0.36.0 |
| APWorld SHA256 | `8a67704da88446e48e091b801542fff5bc2c8bb5f6aa7a8f27597bbb22e1afe9` |
| Resource-manifest SHA256 | `65d8d65db3b1f3a30ba5f76d19a5f7800c560604f09175388902fb063afc6e83` |
| Recipe SHA256 | `68209fee9645ec8cf180f1463dcfe56d5dee2a63ddddd1b4be498b261c27d906` |
| Python / native / slot runtime | m36-python-1 / m26-native-2 / m27-1 |
| Original source paths / resources / ZIP entries | 282 / 220 / 232 |

For byte-identical reproduction, use a separate clean checkout of the packaged
commit and Python 3.12.14 with zlib 1.3.2, then follow BUILDING.md. Building at a
later documentation commit changes generated `build-source.json` even when recipe
inputs match; it is not the sealed archive. Do not substitute that output under
the same hash or tag. Source tests additionally require lupa.

Release asset allowlist: `smb3x.apworld`, `SHA256SUMS.txt`, `INSTALLATION.md`,
`RELEASE-NOTES.md`. Only the APWorld is the game integration artifact. Generated
player/seed archives, local prepared games, emulator binaries, ROMs/BPS/States,
private evidence and historical development Git objects are excluded.

Independent M36 evidence remains authoritative for seven generation comparisons,
seven complete native ROM comparisons, the three-version managed native matrix,
cross-version refusals and historical isolation. The membership correction accounts
for ten Git line-ending normalizations without a package change. New release
verification is summarized in the private handoff separately from inherited results.

## Final release staging checks

The sealed APWorld was rebuilt from the exact clean source using Python 3.12.14 /
zlib 1.3.2, matching every archive byte and all 220 resource members. All 190
maintained tests passed again. The build audit rejected private-project reads
outside the clean source/output and Python prerequisite.

A new isolated official AP 0.6.8 installation passed Options Creator's actual
Vanilla/Balanced/Compatible widget order, Vanilla default and clean YAML export.
A fresh disposable room and exact installed APWorld on BizHawk 2.11.1 / NesHawk
passed physical World 1-1 clear, indexed Super Leaf delivery, consumption,
checkpoint publication, ordinary client.exit closure and cold Resume. The
server retained the check and item count stayed one with Leaf quantity zero.
Cache resources and the authoritative checkpoint were verified. File selectors,
Creator selection, navigation and goal approach were assisted; no native check
bits, receipt acknowledgements or checkpoint data were injected. This is not a
new desktop mouse/controller or full campaign acceptance claim.

Actual diagnostic seed archives contain a server payload and a two-member
player container; seven older generation cases additionally include standard
spoiler text. These diagnostics remain private, never release assets. No prepared
ROM/BPS/State or emulator binary is present in the inspected generated containers.

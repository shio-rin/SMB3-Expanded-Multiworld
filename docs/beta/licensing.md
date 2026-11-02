<!-- SPDX-License-Identifier: MPL-2.0 -->
# Licensing, attribution and exceptions

SMB3X is free and unofficial, with no affiliation with Nintendo, Archipelago,
BizHawk or OpenAI. The project's [README](../../README.md) describes its origins
and AI assistance in the maintainer's own words.

## Original project source

The unchanged [MPL-2.0 text](../../LICENSE) applies to the established original
Python, Lua, tools, tests and documentation scope. [LICENSE-SCOPE.json](../../LICENSE-SCOPE.json)
records the file-level scope; new repository documentation with an SPDX MPL-2.0
notice uses that license. The grant covers only rights contributors control.
It does not license Nintendo intellectual property or blanket-relicense native
assembly, compiled certificates, descriptors, emulator configuration or other
third-party expression. Free development does not add a noncommercial restriction
to the MPL license.

## Native-material qualifications

Three documented native adaptation groups retain unresolved rights interpretations:

- House selector tables and inventory insertion adaptations in `m191.asm`.
- Angry Sun return/clamp logic in `sun-exp3.asm`.
- Sound restoration helper logic in `m244_sfx_resume.asm`.

The qualifications also cover their corresponding compiled certificate
representations. Neither infringement nor legal clearance is asserted.
Attribution alone does not establish third-party permission. These qualifications
remain in effect; this page is an editorial summary, not a new rights determination.

[NOTICE.md](../../NOTICE.md) and the scope record are frozen package inputs. Their
older administrative release-hold wording describes the source snapshot; it is
not a current installation procedure or a request for contributor approval.
The material-specific qualifications remain factual. Use this page for the
current consolidated explanation and [provenance](provenance.md) for package identity.

## Third-party components and distribution

[THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) retains the Archipelago,
BizHawk/NesHawk, Southbird disassembly, NESASM and supporting-library credits and
exceptions. Applicable full license texts remain in `third-party/`.

Players supply their own ROM. SMB3X supplies no original/modified Nintendo ROM,
original CHR banks, private soundtrack or external music pack. Locally prepared
ROMs and BPS must stay local; BPS can contain original CHR data. Played States,
private sessions, credentials and private reference/legal evidence are not release
assets. The configuration asks the installed emulator for its built-in colors;
no emulator RGB lookup table is bundled by SMB3X.

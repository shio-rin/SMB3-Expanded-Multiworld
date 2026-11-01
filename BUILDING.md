<!-- SPDX-License-Identifier: MPL-2.0 -->
# Build SMB3X

Git and Python 3.12+ suffice. Packaging uses only committed source and the standard
library: no ROM, installed AP/BizHawk, private soundtrack, old APWorld or cache.
Exact ZIP reproduction uses Python 3.12.14/zlib 1.3.2; another compression version
may change ZIP bytes while preserving member hashes.

To reproduce the sealed first beta, use a separate clean checkout of
`cf90296511a46174e8daf1a634acb3127f457c51` (the intended `v0.36.0-beta.1` tag).
Later documentation commits change generated build-source metadata even though
recipe inputs are identical. See [beta provenance](docs/beta/provenance.md).

From that clean committed checkout:

```powershell
python -B -m tools.check_source
python -B tools/build_apworld.py ../smb3x.apworld
```

Choose a fresh output; existing archives are never overwritten. The builder checks
`packaging/resources.json` source and emitted hashes, then writes an APWorld and
sibling `.build.json` with source commit, recipe/resource identity and member hashes.
See NOTICE.md before any distribution.

## Edit → test → recipe review → clean build

1. Edit actual implementation under `src/smb3x`; run affected tests (TESTING.md).
2. Run `python tools/update_recipe.py --propose ../recipe-review.json`.
3. Review each named source/output resource and old/new canonical/emitted hashes.
   Membership additions/removals require an explicit recipe edit and code review.
4. For ordinary text, apply exactly that proposal:
   `python tools/update_recipe.py --apply ../recipe-review.json`.
5. Commit code/tests/recipe together. Build twice from separate clean checkouts;
   compare archive and member hashes.

Apply refuses stale proposals and native certificate changes. It does not silently
add resources or approve arbitrary binaries. New certificate hashes are not a fix
for a failed native check.

## Reconstruct native certificates

Player preparation validates certified spans and every original-ROM guard. It
never records a new certificate. Readable inputs live in
`src/smb3x/native/{asm,symbols,certificates}`. Their historical basenames identify
certified source, not executing Python layers.

Optional maintainers supply NESASM with SHA256
`d6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501`:

```powershell
python -m tools.rebuild_assembly --source . --assembler C:/tools/nesasm.exe --output ../assembly-review
python -m tools.rebuild_helpers --source . --assembler C:/tools/nesasm.exe --output ../helper-review
python -m tools.rebuild_menu --source . --assembler C:/tools/nesasm.exe --output ../menu-review
```

These write fresh review outputs, not production recipes. Compare emitted bytes,
symbols and allocation spans. Thirteen core records, palette helpers, giant-block
helper and menu record have generators. Later guarded edit certificates also contain
reviewed source-ROM/interface facts; their ASM alone is not a full-record generator.
Native changes require guard review and complete ROM-byte regression comparisons.

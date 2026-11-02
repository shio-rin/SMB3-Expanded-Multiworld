<!-- SPDX-License-Identifier: MPL-2.0 -->
# Release provenance

[First public beta v0.36.2-beta.1](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.2-beta.1)
is APWorld **0.36.2**, sealed candidate **36.0.2-rc1**.

| Identity | Exact value |
| --- | --- |
| Packaged source / tag target | `7a4438a840116d279ff9688ded1c0e1b7f26d3fb` |
| APWorld SHA256 | `88e4766294c4ed6687229114069d6d4d7d228b6bc6e68b8fd65f1c351f9a60e3` |
| Resource-manifest SHA256 | `eba4e81d449afe232867d4d73d5b5ce27000b99aa623ebe9ea596a4b1f1fc3e4` |
| Recipe SHA256 | `058cda0522e5e9c6aaadf681b95584c113652a63f010ba6a2b8a9d1c2896631c` |

The release tag preserves the reproducible packaged source. For exact archive
reproduction, check out that commit and follow [BUILDING.md](../../BUILDING.md),
including Python 3.12.14 / zlib 1.3.2. Main may contain newer documentation;
building a newer commit changes build-source metadata and is not guaranteed to
reproduce the historical archive. Documentation commits do not renumber the game.

## Retained package snapshots

`NOTICE.md`, `docs/player-guide.md`, `docs/host-guide.md` and `docs/options.md`
remain hash-bound package inputs. Their wording and older links are retained
unchanged, not repaired as live navigation. Use the [current player guide](player-guide.md),
[host guide](host-guide.md) and [options reference](../../apworld/smb3/docs/options-reference.md).

The frozen `LICENSE-SCOPE.json` enumeration describes the packaged-source snapshot,
not a complete inventory of current main. Removed historical documentation remains
available at the release tag. See [licensing](licensing.md) for current scope and
material-specific qualifications. Full license texts, notices and recipe inputs
remain unchanged; no new release build is needed for repository prose cleanup.

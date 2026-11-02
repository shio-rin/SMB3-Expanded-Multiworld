<!-- SPDX-License-Identifier: MPL-2.0 -->
# Architectural consolidation

> Historical engineering record; dated results retain their original scope.
> Use the [current player guide](docs/beta/player-guide.md) for setup and play.

The current implementation uses responsibility-based modules under `src/smb3x`.
World, planning, launcher, native pipeline, client and Lua wrapper chains were
replaced with direct implementations. Stable IDs and protocol/save semantics remain.
Removed YAML now rejects in both official import orders. Journal temporary names
are bounded and managed paths are checked before native work. Fresh games use
`SMB3X - Expanded Multiworld.nes`; historical games retain their own runtimes.
See ARCHITECTURE.md, CODEBASE_GUIDE.md and BUILDING.md.

# Local candidate 31.0.0-rc6

Level Shuffle is Vanilla (default), Balanced (neighboring original worlds), or
Compatible (the full technically eligible 53-stage pool). Pool/range selectors
and obsolete twelve-stage planning are removed. Removed YAML keys reject with
migration guidance, including weighted and trigger-injected settings. The existing
numeric option IDs are unchanged; the dropdown order is display-specific.

Historical player files keep their matching cached runtimes. Public packaging
needs no private music or development seed records. The broader native/gameplay
implementation and persistence cadence are preserved. See NOTICE.md for the
remaining publication/licensing gates; this is a local candidate only.

Public source hard-disables private provider loading. Only a separately hash-bound
private build can enable it; adding metadata files to a public cache cannot.

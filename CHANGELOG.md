<!-- SPDX-License-Identifier: MPL-2.0 -->
# Changelog

## 0.36.3 — Gameplay hotfix

- Fix a potential input lock when consecutive N-Spade matching-card games start.
  Legal roaming Hammer Bros. encounter chains also retain normal controls.
- Retain scheduled trap delays through fortress doorways, subject to each
  effect's gameplay and technical restrictions.
- Recognize Archipelago victory at authenticated credits entry, preserving
  Standard, All Koopalings and All Locations requirements and safe reconnection.
- Generate a new game with APWorld 0.36.3 to use these fixes. Existing games
  retain their original runtime and saved sessions.

[Beta 0.36.3](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.3-beta.1)

## 0.36.2 — First public beta

Published **2026-11-02**, per the [GitHub release](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.2-beta.1).

- First public SMB3X release: all eight worlds, 125 randomized reward checks,
  World Pass progression, reusable Regional or consumable Legacy Hammers,
  stacked inventory and native progression/travel menus.
- Optional stage shuffling, Star Fragment gates, hazards, traps, Blessings,
  DeathLink, palettes, original/shuffled music and cosmetic Luigi.
- Managed safe checkpoints and cold Resume with BizHawk 2.10, 2.11 or 2.11.1 / NesHawk
  on Windows x64, using official Archipelago 0.6.8.
- Existing supported emulator installations can retain unrelated cores, plugins
  and language files; executable and critical dependency integrity stay verified.
- Beta boundaries include limited optional-hazard coverage, some fixed stage
  arrangements, saves at safe states rather than continuously, and no cross-version
  save migration. See [known limitations](docs/beta/known-limitations.md).

[Player guide](docs/beta/player-guide.md) · [Release notes](docs/beta/release-notes.md) ·
[Build provenance](docs/beta/provenance.md)

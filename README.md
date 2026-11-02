<!-- SPDX-License-Identifier: MPL-2.0 -->
# Super Mario Bros. 3: Expanded Multiworld (SMB3X)

This is a heavily AI-assisted Archipelago implementation of SMB3, which started
as a "What if..." after using Codex for a little while. The goal was to have another
fun, short-ish Archipelago game I could keep coming back to every now and then, with
some replay-ability through shuffled levels, color palettes, and more. There were tons
of testing involved in the process of putting this together, added with all the planning, 
brainstorming and adjustments that were made as the versions went - and now I consider
that this reached the point where it is pretty polished, for a beta at least.

There is still plenty of work to be done; logic could use some adjusting or more options, 
regional hammers add additional 'gating' but there could be more, level shuffle works
great but is a bit more restrictive than I would like as some stages are omitted, 
poison mushrooms and angry sun encounters need more coverage (especially the latter), 
traps are in a good spot for a beta but will definitely need some more variety, 
some of the palettes randomization options are not the best, and the list goes on...

I do not plan on posting this to the official Archipelago discord because of the 
community 'general' sentiment towards AI use, especially in a case like this, though
in my mind I can't see this as another instance of 'AI slop' with all the time I've sunk
into it. At the end of the day, I made this to have fun, and if some others get to enjoy
it too, then great! Otherwise then no biggie.

I'm always open to criticism, bug-reports, and especially any constructive feedback or
ideas on how to improve this. I only see this as a fun project with a fun side effect of
giving me a functional Archipelago implementation of one of my favorite childhood games, 
while looking forward to seeing what it becomes in the long run.

## Codex's description and instructions

SMB3X connects all eight Super Mario Bros. 3 worlds to Archipelago. Clear 125
reward checks, send items to other players, and receive World Passes, Regional
Hammers and useful inventory items. Bowser is the victory goal, not a reward check.
Optional level shuffling, hazards, traps, Blessings, palettes and Luigi's appearance
let you vary a game.

**First public beta:** [APWorld 0.36.2 / v0.36.2-beta.1](https://github.com/shio-rin/SMB3-Expanded-Multiworld/releases/tag/v0.36.2-beta.1).
This is a beta prerelease; feedback and bug reports are welcome.

## Start playing

You need Windows x64, official Archipelago 0.6.8, BizHawk 2.10, 2.11 or 2.11.1,
and your own clean SMB3 USA Revision A ROM. Your existing supported BizHawk
installation can be used; unrelated cores, plugins and language files may stay.
The launcher sets up NesHawk automatically.

1. Install `smb3x.apworld` through Archipelago Launcher and restart Launcher.
2. Export your choices from Options Creator and send the YAML to your host.
3. Open your room's `.apsmb3x` using Launcher → Open Patch, then select your ROM
   and EmuHawk.exe when prompted. Your player name comes from that player file.
4. Press **Start** at the title screen. The first save becomes available once you
   reach the world map and connect. Wait for the successful save notice there.

The **[player guide](docs/beta/player-guide.md)** is the main guide for setup,
[controls and menus](docs/beta/player-guide.md#controls-and-menus),
[saving and continuing](docs/beta/player-guide.md#saving-and-continuing), and
[hints/chat](docs/beta/player-guide.md#hints-and-chat).

[Short installation page](INSTALL.md) · [Hosting](docs/beta/host-guide.md) ·
[Options](apworld/smb3/docs/options-reference.md) ·
[Troubleshooting and updates](docs/beta/troubleshooting.md) ·
[Release notes](docs/beta/release-notes.md) · [Known limitations](docs/beta/known-limitations.md)

## Development, support and licensing

[Report a bug or suggest an improvement](https://github.com/shio-rin/SMB3-Expanded-Multiworld/issues).
Include steps and relevant redacted log excerpts; see
[bug reporting](docs/beta/troubleshooting.md#report-a-bug) or
[security reporting](SECURITY.md) for sensitive issues.

Contributors can start with [Contributing](CONTRIBUTING.md), [Development](DEVELOPMENT.md),
[Build](BUILDING.md), [Testing](TESTING.md), [Architecture](ARCHITECTURE.md) and
[Codebase guide](CODEBASE_GUIDE.md).

SMB3X is free and unofficial, with no affiliation with Nintendo, Archipelago,
BizHawk or OpenAI. MPL-2.0 covers
the established original-source scope; see [licensing and exceptions](docs/beta/licensing.md)
and [third-party credits](THIRD_PARTY_NOTICES.md).
[Build provenance](docs/beta/provenance.md) identifies the sealed package and explains
which older documents are preserved snapshots rather than current setup guides.

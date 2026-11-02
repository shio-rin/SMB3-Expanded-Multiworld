<!-- SPDX-License-Identifier: MPL-2.0 -->
# A guided reading path

All paths below are under `src/smb3x` unless stated otherwise.

| Question | Actual implementation |
|---|---|
| How does AP find the game? | `world/registration.py`; root `packaging/apworld_bootstrap.py` |
| Where are the options? | `world/options.py:SMB3Options`; `yaml_validation.py` rejects removed keys |
| Where are numeric IDs? | `shared/ids.py`; enabled registry in `shared/locations.py` |
| How are items placed? | `world/item_pool.py`, `rules.py`, `placement.py` |
| How are levels shuffled? | `planning/stages.py:assignments`, `matching.py`, `special_stages.py` |
| What can hazards affect? | `planning/hazards.py` and its checked data |
| How is a ROM built? | `native/pipeline.py:build`, then named patch stages |
| How does launch work? | `launcher/player.py:main`, `preparation.py:prepare`, `emulator.py:play` |
| How does a check leave the NES? | `bizhawk/locations.lua:poll`, `client/service.py:watcher` |
| How does a reward arrive? | `client/network.py`, `persistence/receipts.py`, `bizhawk/delivery.lua` |
| Why does Resume avoid duplicates? | `client/persistence/coordinator.py`, `checkpoints.py` |

Retained native/data basenames and strings such as `m27-1` identify exact contracts,
not another Python implementation to find. Do not renumber IDs or rewrite protocol
strings while learning the code.

## World 1-1: Mario's clear and an incoming reward

The NES owns gameplay; Lua observes and performs controlled native operations;
Python validates ownership, talks to AP and keeps durable histories; the AP server
routes randomized rewards. A network message alone does not prove a native grant.

1. Mario clears the physical World 1-1 host and returns. Its entry in
   `planning/data/locations_m242.json` has ID `0x534D3301`, address `0x7D04`, mask
   `0x80`. Shuffle changes the content played, not this host check.
2. `bizhawk/locations.lua:poll` checks the native marker, bound session and safe
   overworld conditions before reading the bit. `import_checks` merges restored
   history without issuing a new clear notification. `bridge.lua` returns the
   observation to Python; Lua does not contact AP.
3. `client/native_session.py` validates the response. `service.watcher` records
   physical observations and calls `Coordinator.after_poll`. It freezes safely,
   reconciles histories, requests native State capture, validates the witness,
   publishes the immutable checkpoint/epoch records, activates it and thaws.
   Only `publication_checks` can authorize the saved, server-missing check for
   `ctx.check_locations`. An observed bit alone is insufficient.
4. AP looks up the placement, which may belong to another player. An incoming item
   for this player reaches `SMB3Context.on_package` as indexed `ReceivedItems`.
   Reconnect uses Sync and a history barrier; `Coordinator.before_poll` validates
   the complete prefix before native work resumes.
5. The receipt state persists pending work before requesting delivery. Two equal
   item types at different indices are different deliveries. `delivery.lua` waits
   for safe conditions. For a stacked Super Leaf it publishes ticket `index + 1`
   and request fields at `0x7BD0` onward. `native/asm/m191.asm:StackNativeGrant`
   applies the quantity change and publishes a receipt. Lua verifies the receipt,
   including its one-step increment, before reporting success.
6. Python persists the acknowledgement. A post-delivery checkpoint protects the
   granted inventory before normal spending resumes. Native Leaf consumption is
   another meaningful change and requests another checkpoint. Replaying the server
   index therefore cannot refill a Leaf already consumed before a verified save.
7. Cold Resume checks the exact ROM/emulator/resource binding and checkpoint owner.
   `checkpoints.py` selects verified native State plus matching histories; the
   coordinator validates server history before releasing control. It does not
   reconstruct native inventory from server checks alone.

Ordinary close uses the latest verified checkpoint, not an exact mid-level crash
snapshot. Uncertain operations pause safely and retain evidence instead of guessing.
Begin with locations and the service loop, then follow `publication_checks` before
studying the larger checkpoint validation routines.

## A small first contribution

Start with `shared/locations.py` and `world/regions.py:create_regions`: a registry row
declares a physical host; `location.access_rule` controls logical reachability. The
named `config`, `world_number` and `entry` locals refer to progression settings, the
host world and native map coordinates. The M19.1 event strings remain stable AP graph
keys, not another implementation to find.

For a first edit, improve an option description in `world/options.py` (preserve the
class attributes and their order), or a notification string in
`client/notifications.py` (preserve its queue/acknowledgement behavior). Add a small
regression beside the corresponding tests. Read TESTING.md before building. Begin
with text and isolated tests, rather than checkpoint ownership or native addresses.

Then read `client/service.py:watcher` in order: persist pending receipts, poll native
state, persist acknowledgements, ask `Coordinator.after_poll` to establish checkpoint
authority, and publish only `publication_checks`. Repeated ownership checks after
awaits are intentional. `checkpoints.validate_components` compares the native witness,
typed receipt partition, controller and complete server prefix before Resume.

`planning/audio_allocation.py:allocate` uses stable hash ranks and ordered iteration,
not the world's RNG. `native/pipeline.py:build` lists every patch stage explicitly;
its order, original-byte guards and final BPS reproduction check are part of correctness.

Emulator-version and State boundaries are documented in
[emulator qualification](docs/emulator-qualification.md). See [licensing scope and exclusions](docs/beta/licensing.md) for source terms.

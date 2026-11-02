<!-- SPDX-License-Identifier: MPL-2.0 -->
# Test by responsibility

Run `python -B -m unittest discover -s tests` from the checkout, with `lupa`
installed. Tests use synthetic histories and mocked RAM/State, without ROM/server.
`test_controlled_checkpoint_fixture.py` retains an older characterization fixture;
it is never packaged in the runtime.

| Change | Focused gates |
|---|---|
| Planning | `test_shuffle`, `test_private_boundaries`; exact official generation/plans |
| Effects/DeathLink | `test_effect_pool`, `test_effect_queue`, `test_effect_persistence`, `test_deathlink` |
| Transport | `test_transport`; real reconnect and uncertain-response cases |
| Checkpoints/filesystem | `test_checkpoints`, `test_autosave_policy`, `test_managed_paths`; native Resume |
| Ownership/launch | `test_runtime_ownership`, `test_identity`, `test_association`; both POC import orders |
| Lua/presentation | `test_console`, `test_diagnostics`; actual console, input and pause behavior |
| Options | official Generate/Options Creator, export/templates and both import orders |
| Native | reconstructed certificates, symbols/spans/guards, complete ROM bytes |

Example: `python -B -m unittest tests.test_shuffle tests.test_private_boundaries`.

Compare official Vanilla/Balanced/Compatible, Mixed Fortresses, hazards, palette/music,
weighted YAML, triggers, start inventory and plando. Compare placements, slot data
and RNG states, not just success. Creator must show Vanilla → Balanced → Compatible,
default Vanilla, with no obsolete selectors. Direct, weighted, linked and triggered
Legacy12 YAML must reject clearly.

For runtime changes, use a fresh isolated AP/BizHawk installation and synthetic room.
Perform a genuine check, publication, indexed Leaf delivery, native consumption,
later checkpoint, ordinary close and two cold Resumes. Exercise reconnect, offline
pending items, full inventory, interrupted capture/delivery and foreign ownership.
Test effects and DeathLink where affected. Record assistance; writing a completion
bit is not a physical check. Never alter old caches to make new player files run.
A bounded matrix does not certify an eight-world campaign.

Build from two unrelated clean checkouts. Compare ZIP/member hashes. Keep evidence
outside the recipe. Developer tests and generators stay in source control but are
not player runtime resources.


`test_rom_launch` tests the actual `launcher.emulator.play` boundary. Its valid
synthetic control reaches mocked process creation; missing/corrupt canonical ROMs
must fail before that call. Patch verification is mocked separately: `verify_game`
reconstructs the expected ROM and validates build/session data, while `play` compares
the physical file. These unit tests require no commercial ROM or private fixture.

`test_connected_identity` compiles the actual connection validator without the external
AP client framework. It uses real local planners and synthetic context data to check
current acceptance, historical-release rejection before planning/mutation, each later
contract, prepared palette ownership and protocol short-circuiting. This complements,
and does not replace, official AP generation and real-client lifecycle tests.

Emulator-version and State boundaries are documented in
[emulator qualification](docs/emulator-qualification.md). See [licensing scope and exclusions](docs/beta/licensing.md) for source terms.

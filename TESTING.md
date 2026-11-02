<!-- SPDX-License-Identifier: MPL-2.0 -->
# Testing

## Running the maintained tests

Use Python 3.12+, Git and `lupa`; [Development](DEVELOPMENT.md) has setup commands.
From the checkout, run:

```powershell
python -B -m unittest discover -s tests
```

The maintained suite uses synthetic histories and mocked emulator/RAM/State APIs;
it needs no ROM or running server.

## Checking your contribution

Choose checks for what changed. Documentation-only edits need formatting and
link/anchor checks, not gameplay tests. Code changes should run relevant tests
and exercise the affected behavior. Explain what you checked and what remains
untested in your pull request.

| Area | Useful test modules |
| --- | --- |
| Planning | `test_shuffle`, `test_private_boundaries` |
| Effects / DeathLink | `test_effect_pool`, `test_effect_queue`, `test_effect_persistence`, `test_deathlink` |
| Networking | `test_transport`, `test_connected_identity` |
| Saves / filesystem | `test_checkpoints`, `test_autosave_policy`, `test_managed_paths` |
| Launcher / emulator | `test_runtime_ownership`, `test_identity`, `test_association`, `test_emulator_profiles`, `test_launcher_errors`, `test_rom_launch` |
| Lua / presentation | `test_console`, `test_diagnostics` |

For example: `python -B -m unittest tests.test_shuffle tests.test_private_boundaries`.

For option changes, check Options Creator and a normal official AP generation.
Keep Vanilla / Balanced / Compatible in that order with Vanilla as default, and
verify YAML export and rejection of removed selections, including weighted or
triggered settings. Stable numeric IDs must remain unchanged.

## Maintainer checks for runtime, native changes and releases

Saving, networking, native patches and emulator compatibility need additional
verification of the affected safety boundaries. Full release qualification belongs
to maintainers preparing a release, not every small contribution.

- Use isolated AP/BizHawk installations, disposable games and managed roots.
  Never alter played saves/caches. Check genuine completion, server publication,
  indexed rewards, consumption, checkpoints, normal close and Resume where affected.
  Saving/networking changes also need reconnect, offline items, full inventory,
  interrupted capture/delivery and foreign ownership. Test effects/DeathLink if
  affected. Label mocked or assisted evidence accurately; an injected completion
  bit is not a physical check.
- For planners, compare placements, slot data and RNG states. Cover affected
  shuffle modes, special stages, hazards, palettes/music, weighted/triggered YAML,
  starting items and plando. Check both integration import orders when relevant.
- For native patches, compare reconstructed certificates, symbols, spans, ROM
  guards and complete ROM output. See [BUILDING.md](BUILDING.md). Emulator changes
  follow [qualification](docs/emulator-qualification.md), including same-version
  Resume and cross-version refusal. Syntax checks cannot prove dynamic imports,
  Lua paths or native guards work.
- Release qualification includes recipe review and two clean-source builds with
  matching archive/member hashes ([BUILDING.md](BUILDING.md)), plus two cold
  Resumes. Keep verification outputs outside package inputs.

Refactoring must preserve lazy validation, await order and durable-write order;
[Architecture](ARCHITECTURE.md) explains these safety boundaries.

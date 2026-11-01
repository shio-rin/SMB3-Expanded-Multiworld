<!-- SPDX-License-Identifier: MPL-2.0 -->
# Development setup

Use a separate checkout and disposable managed root. Never experiment on an
existing player's cache, room or journal. Python 3.12+ and Git suffice for packaging;
maintained tests additionally use `lupa` for actual Lua with mocked emulator APIs.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install lupa
.venv/Scripts/python -B -m unittest discover -s tests
```

Official integration uses Windows Archipelago 0.6.8 and BizHawk 2.10, 2.11 or 2.11.1 / NesHawk.
Use fresh copies; set `SMB3X_MANAGED_HOME` to a short disposable path before launch.
Install the candidate there and generate a new synthetic room. Supply your own
verified ROM for preparation only. Decline optional association registration.

Read ARCHITECTURE.md and CODEBASE_GUIDE.md, then follow BUILDING.md for explicit
recipe review. Start with a small planner or presentation change. Persistence and
native changes need TESTING.md's additional gates. Syntax checks do not exercise
dynamic imports, Lua paths, frozen AP namespaces or native byte guards.

For a readability edit, characterize the affected return values, exceptions and side
effects first. Keep chained Boolean checks lazy: evaluating every operand into a
temporary can access malformed data that the original guard rejected safely. Do not
move an await or a durable write while wrapping long statements. A scoped formatter
is optional developer tooling; it is not needed to build or run SMB3X.

M35 emulator/version and State boundaries are documented in
[emulator qualification](docs/emulator-qualification.md). Original project source
notices use MPL-2.0; see LICENSE-SCOPE.json and NOTICE.md for exclusions.

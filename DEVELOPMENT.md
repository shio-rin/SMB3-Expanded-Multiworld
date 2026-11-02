<!-- SPDX-License-Identifier: MPL-2.0 -->
# Development setup

Use Python 3.12+ and Git. Maintained tests also need `lupa` to run Lua against
mocked emulator APIs. From the checkout:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install lupa
.venv/Scripts/python -B -m unittest discover -s tests
```

Use the [Codebase guide](CODEBASE_GUIDE.md) to find the relevant implementation and
[Testing](TESTING.md) to choose checks for your change. [BUILDING.md](BUILDING.md)
covers packaging and recipe review.

## Testing with the game

Integration testing uses official Windows Archipelago 0.6.8 and BizHawk 2.10,
2.11 or 2.11.1 / NesHawk. Use a disposable test game and an isolated managed root,
not a played save. Set `SMB3X_MANAGED_HOME` to a short disposable path before launch,
install the candidate in your test AP installation, and generate a fresh room.
Supply your own verified ROM locally; decline optional association registration.

Saving, networking, native patches and emulator changes need the targeted
[maintainer checks](TESTING.md#maintainer-checks-for-runtime-native-changes-and-releases).
See [emulator qualification](docs/emulator-qualification.md) for version/save contracts.

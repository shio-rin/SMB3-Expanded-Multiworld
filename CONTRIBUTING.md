<!-- SPDX-License-Identifier: MPL-2.0 -->
# Contributing

Bug reports, clearer instructions and focused improvements are welcome. For a bug,
start with [reporting steps](docs/beta/troubleshooting.md#report-a-bug). For code,
read [Development](DEVELOPMENT.md), [Codebase guide](CODEBASE_GUIDE.md) and
[Testing](TESTING.md). A small option-description or notification improvement is
a useful first contribution.

Make one focused change and explain the before/after behavior. Add relevant tests
and update the reader-facing guide if behavior changes. Distinguish mocked tests,
actual emulator tests and human play; describe assistance accurately.

Preserve stable IDs, RNG order, original-ROM guards, receipt/checkpoint meanings
and historical games. Use disposable rooms and managed roots; never modify an
installed player's cache to make a test pass. Review resource-recipe changes using
[BUILDING.md](BUILDING.md). Do not accept new hashes merely to hide a failure.
Formatting edits must preserve lazy checks, await order and durable write order.

Contributions must be yours to license under MPL-2.0 or carry separate compatible
terms and required notices. See [scope and exceptions](docs/beta/licensing.md).
Do not add blanket MPL notices to excluded material. Keep ROMs, private music,
player files, credentials, journals and States out of commits and bug attachments.

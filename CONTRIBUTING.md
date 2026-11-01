<!-- SPDX-License-Identifier: MPL-2.0 -->
# Contributing

This beta is staged privately for owner review. Original project contributions use
MPL-2.0; the specific third-party uncertainties in NOTICE.md remain. Read the
[current licensing addendum](docs/beta/licensing.md) for release status. Contributions must be yours to license under MPL-2.0,
or identify their separate compatible terms and retain all required notices.
Do not add MPL notices to uncertain or excluded material. Substantial implementation, testing and documentation were
produced with OpenAI Codex and ChatGPT under human direction. Describe assistance
and test scope accurately.

Make one responsibility-sized change with a concrete before/after example. Add
relevant tests, document changed behavior and review the resource recipe using
BUILDING.md. Preserve RNG order, stable IDs, original-ROM guards and receipt/checkpoint
meanings unless a separately scoped design authorizes a change. Do not accept new
hashes merely to suppress a failure.

Never include ROMs, private music/catalogues, player files, credentials, journals
or States. Use synthetic fixtures and do not edit installed caches. A useful bug
report gives exact artifact/resource hashes, environment, steps, expected behavior
and redacted logs. Distinguish mocks from actual NesHawk tests; neither implies a
complete human gameplay campaign.

For a small first contribution, improve an option description, clarify a notification,
or add a focused regression. CODEBASE_GUIDE.md names the relevant implementation.
Keep receipt, grant, observation and publication terminology distinct. State the
behavior your test protects and whether it uses mocks or a real emulator. Formatting
changes should be scoped and reviewed; do not refresh native certificate hashes to
make an unrelated source edit build.

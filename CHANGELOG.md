# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.18] - 2026-08-29

Adds the scheduled release-consistency check this repository was
missing, and refreshes the shared conformance gate.

### Added

- `scripts/check_suite_consistency.py` and a scheduled **Release
  Consistency** workflow compare this tree against what is actually
  published on PyPI. A version bumped in the tree and never released
  breaks nothing — the tree is consistent, the tests pass, the changelog
  is written — and only the index disagrees. That has happened three
  times in this suite, each time stranding a security floor that reached
  nobody.
- The check distinguishes the two directions: a tree ahead of the index
  is the expected transient between merging a bump and pushing its tag,
  while a tree *behind* it means a release was cut from somewhere other
  than this branch.

### Changed

- Refreshed `tests/test_suite_conformance.py` to the current canonical
  copy. This repository was carrying a 24-invariant version; the
  twenty-fifth is the one that requires the check added above, so it had
  been conformant only against an older bar.

## [0.0.17] - 2026-08-29

The first release since 0.0.15. **`0.0.16` was bumped in the tree but never
tagged or published**, so the `cryptography` advisory floor cut then has
never reached a dependent. This release ships it.

Also brings the repository onto the suite conformance gate: it had no
`CONTRIBUTING.md`, `SECURITY.md`, `docs/`, `examples/` or `benches/`.

### Fixed

- **`cryptography` floored at 50.0.0** (#9, #10), the release patching a
  high-severity advisory. Cut as `0.0.16` and never published. If you are
  pinned below `0.0.17`, upgrade.

### Added

- **`benches/bench_investigations.py`**. E&I messages are small, so there is
  no size axis worth sweeping — the cost is per call, which is how they
  arrive.

  About **0.25 ms per message** warm, so a queue of a few thousand
  investigations is a background job rather than a capacity problem.
  Validation costs about the same as generation (0.99x), so generating and
  then validating pays for the schema twice. Refusal is essentially free
  (~0.001 ms), the work skipped rather than done and discarded.

  **The first message in a process costs about 205 ms** against 0.32 ms for
  the second — a **640x** difference while the XSD compiles. Measured in a
  fresh interpreter, because timing it in-process reports the warm number.

- **`docs/index.md`**, **`examples/`** (two runnable examples),
  **`SECURITY.md`** and **`CONTRIBUTING.md`**.

- **`tests/test_suite_conformance.py`** — invariants shared across the
  suite, vendored from one canonical copy and checksummed by its own test.

### Documented

- **The two types do not require the same fields.** `camt.029` needs a
  `confirmation_code` that `camt.056` does not. Ask `get_required_fields`
  rather than assuming.

- **`generate_message` returns an error dict rather than raising.** A caller
  that does not check `"error"` will treat a refusal as a message. The
  benchmark here did exactly that on its first run — timing the rejection
  path for one of the two types and reporting it as throughput — which is
  why both the docs and `SECURITY.md` now say so.

### Changed

- CI lints, formats and runs `examples/` and `benches/`.

## [0.0.15] - 2026-07-16

Undocumented at the time; reconstructed from the commit history.

### Added

- Prompts and resources, for parity across the MCP suite (#7).
- `glama.json`, so Glama can build the server.

### Fixed

- `mcp` capped below 2.0. 2.0 removed `mcp.server.fastmcp`, the import this
  server uses (#6).

### Changed

- Release workflow emits real provenance and an SBOM on publish (#5).
- Licensing ships as `Apache-2.0 OR MIT` (#11).

## [0.0.14] - 2026-07-16

### Changed

- **Version** — suite-wide lockstep bump to `0.0.14`, following the core
  `camt053` 0.0.14 release, to keep the ISO 20022 MCP suite packages on
  the same version. No functional changes to the library or MCP server.

## [0.0.13] - 2026-07-16

### Changed

- **Version** — suite-wide lockstep bump to `0.0.13` to keep the ISO 20022
  MCP suite packages on the same version. No functional changes to the
  library or MCP server.

### Added

- **Load/stress test suite** (`tests/test_stress.py`, marker `perf`,
  excluded from the default coverage-gated run): sustained concurrent
  camt.056 generation + validation (32 workers × 300 iterations, zero
  errors, p95/p99 latency tripwires), a tracemalloc soak loop asserting
  bounded memory growth, and large-batch cases (500 transactions in one
  message; a 250-document burst). Run with
  `pytest tests/test_stress.py -m perf --no-cov`.

## [0.0.2] - 2026-07-12

### Added

- Initial public release: `camt.056.001.12` (FI to FI Payment Cancellation
  Request) and `camt.029.001.14` (Resolution of Investigation) generation
  and XSD validation, plus an MCP server exposing 4 tools over stdio.

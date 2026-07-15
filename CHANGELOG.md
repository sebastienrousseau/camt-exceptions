# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

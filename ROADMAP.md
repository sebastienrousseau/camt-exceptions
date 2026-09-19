# camt-exceptions Roadmap

This roadmap tracks what is planned for camt-exceptions, the ISO 20022
Exceptions & Investigations generator and MCP server. It summarises the
CHANGELOG and the open issues; it does not promise work that is not
tracked there. Releases ship when the gates pass, not on a calendar.

## v0.0.18 (current)

- Two message types: `camt.056.001.12` (FI to FI Payment Cancellation
  Request) and `camt.029.001.14` (Resolution of Investigation), each
  generated from a bundled template and validated against the bundled
  XSD before it is returned.
- Four tools (`list_message_types`, `get_required_fields`,
  `generate_message`, `validate_xml`), two resources
  (`camt-exceptions://message-types`,
  `camt-exceptions://required-fields/{message_type}`) and one prompt
  (`build_investigation_message`).
- 100% line+branch coverage gate, the shared suite conformance test, a
  per-call benchmark, and a scheduled check that the tree agrees with
  what is published on PyPI.

## Next release (on `main`, unreleased)

- stdio, streamable HTTP (2026-07-28 and 2025-11-25) and SSE from one
  command line (ADR 0001).
- Runs on both supported majors of the `mcp` SDK through a
  compatibility shim; a fresh install gets 2.x.

## Beyond

The README lists three further E&I messages as planned: `camt.026`
(Unable to Apply), `camt.027` (Claim Non-Receipt) and `camt.087`
(Request to Modify Payment). Each plugs into the same engine: bundle
its official XSD and `template.xml`, register it in `MESSAGE_TYPES`,
declare its required fields. None is scheduled and there are no open
issues at the time of writing.

## Out of scope (handled elsewhere)

- **Payment status and return messages** (`pacs.002`, `pacs.004`) - see
  [`pacs008-mcp`](https://github.com/sebastienrousseau/pacs008-mcp).
- **Bank statements** (`camt.053`) - see
  [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp).

<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# camt-exceptions Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about camt-exceptions
without prior context.

## The pipeline

```
MCP client (Claude Desktop, IDE, agent)
        |  stdio, streamable HTTP or SSE (JSON-RPC)
        v
camt_exceptions/server.py      (MCP server: tools, resources, prompt)
        |  thin typed wrappers
        v
camt_exceptions/generator.py   (MESSAGE_TYPES, required fields,
        |                       Jinja2 rendering, XSD validation)
        v
camt_exceptions/templates/     (one directory per message type:
        |                       the official XSD and template.xml)
        v
ISO 20022 camt.056 / camt.029 XML, XSD-validated before it is returned
```

Tools are deliberately thin: every one is a small adapter that delegates
to `camt_exceptions.generator` and returns a JSON-serialisable result.
The generator renders a bundled template and validates the output
against the bundled schema; nothing is fetched at runtime.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Server** | `camt_exceptions/server.py` | The MCP server, all tool / resource / prompt registrations |
| **Entry point** | `camt_exceptions.server:main` (console script: `camt-exceptions-mcp`) | Launches the server over stdio, or over streamable HTTP / SSE with `--transport` (`_cli.py` + `_transports.py`, ADR 0001) |
| **Generator** | `camt_exceptions/generator.py` | `MESSAGE_TYPES`, `get_required_fields`, `generate_message`, `validate_xml` |
| **Schemas and templates** | `camt_exceptions/templates/<message type>/` | The official ISO 20022 XSD and the Jinja2 `template.xml` for each supported type |
| **SDK shim** | `camt_exceptions/_mcp_compat.py` | Builds the server on either supported major of the `mcp` SDK (2.x `MCPServer`, 1.x `FastMCP`) |
| **Version** | `camt_exceptions/__init__.py` | Single source of truth (`__version__`) |
| **Tests** | `tests/test_server.py`, `tests/test_generator.py`, `tests/test_transports.py`, `tests/test_mcp_sdk_compat.py`, `tests/test_stress.py`, `tests/test_suite_conformance.py` | The tools and resources, the generator, the command line, the SDK shim, the load tests (marker `perf`, outside the default gate) and the shared suite conformance gate |
| **Examples** | `examples/01_cancel_a_payment.py`, `examples/02_resolve_an_investigation.py` | Runnable, offline walkthroughs of the two message types |
| **Benchmarks** | `benches/bench_investigations.py` | Per-call cost of generate, validate and refuse; `docs/index.md` explains the result |
| **Release helpers** | `scripts/verify_versions.py`, `scripts/check_suite_consistency.py` | Assert every restatement of the version agrees; compare the tree against what PyPI has published |

## Tools, resources, prompts

The current MCP surface:

- **Tools** - four. `list_message_types` (the supported types and their
  names), `get_required_fields` (the top-level fields a type requires),
  `generate_message` (render a record and validate the XML against the
  bundled XSD) and `validate_xml` (check raw XML against a type's XSD).
- **Resources** - `camt-exceptions://message-types` (the catalogue as
  JSON) and `camt-exceptions://required-fields/{message_type}` (one
  type's required fields).
- **Prompts** - `build_investigation_message(message_type)` (guided
  instruction template for building and validating one E&I message).

## Key design decisions

- **Template plus schema, nothing else.** Each message type is a
  directory holding the official XSD and a Jinja2 template. Adding a
  type is bundling those two files, registering the type in
  `MESSAGE_TYPES` and declaring its required fields.
- **Validated before it is returned.** `generate_message` runs the
  rendered XML through the XSD; a message that fails validation is never
  handed back as a message.
- **Errors as data.** Tools never raise. A `ValueError` (unknown type,
  missing required field) is turned into an `{"error": ...}` payload so
  the agent can reason about failure without parsing tracebacks. Every
  caller has to check for it; `SECURITY.md` says why.
- **The two types differ.** `camt.029` requires a `confirmation_code`
  that `camt.056` does not; `get_required_fields` is the source of truth
  so callers ask rather than assume.
- **Loopback by default.** stdio needs no socket. The HTTP transports
  bind `127.0.0.1` unless told otherwise and add no authentication of
  their own; a routable deployment sits behind a gateway (ADR 0001).
- **No network, no state.** The server sends nothing, stores nothing
  and holds no credentials; the XSD is read from the package, not
  fetched.
- **Coverage enforced at 100%** line+branch; only defensive guards are
  `# pragma: no cover`.

## Extension points

- **Add a message type:** create `camt_exceptions/templates/<type>/`
  with the XSD and `template.xml`, register it in `MESSAGE_TYPES` in
  `camt_exceptions/generator.py`, declare its required fields, and add
  tests in `tests/test_generator.py`. The benchmark builds its record
  from `get_required_fields`, so a new type is measured automatically.
- **Add a tool:** add a function under `@server.tool(...)` in
  `camt_exceptions/server.py`; keep the error-dict convention; pair it
  with tests in `tests/test_server.py`.
- **Add a resource:** `@server.resource("camt-exceptions://...")`
  decorator.
- **Add a prompt:** `@server.prompt()` decorator.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- The two messages and the calling convention: [`docs/index.md`](docs/index.md)
- Decisions: [`docs/adr/`](docs/adr/index.md)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)

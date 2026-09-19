<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Getting support

Thanks for using camt-exceptions. Here's the fastest way to get help, by need.

## Questions & how-to

- **Read first:** the [README](README.md), [`docs/index.md`](docs/index.md)
  and the two runnable [`examples/`](examples/) (cancel a payment, resolve
  an investigation).
- **Still stuck?** Open a question issue at
  <https://github.com/sebastienrousseau/camt-exceptions/issues/new>. Include
  your Python version, the `camt-exceptions` version
  (`camt-exceptions-mcp --version`), your MCP client (Claude Desktop / IDE /
  agent), the transport you run, and a minimal reproducer.

## Bugs

Open a bug report at
<https://github.com/sebastienrousseau/camt-exceptions/issues/new> with a
minimal reproducer, the tool name, the message type, the record (with
sensitive values redacted) and the full `{"error": ...}` payload or the
schema errors `validate_xml` returned.

## Feature requests

Open a feature request at
<https://github.com/sebastienrousseau/camt-exceptions/issues/new>. New E&I
message types (camt.026, camt.027, camt.087) plug into the same engine -
see [ARCHITECTURE.md](ARCHITECTURE.md) for the extension points and
[ROADMAP.md](ROADMAP.md) for what's planned.

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Contributing & maintaining

See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Supported versions

Fixes land on the latest release line. See [SECURITY.md](SECURITY.md) for
the supported-version policy. camt-exceptions requires Python 3.10+.

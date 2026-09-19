<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security Policy

## Supported versions

| Version  | Supported |
| -------- | --------- |
| 0.0.18   | :white_check_mark: |
| < 0.0.18 | :x:               |

## Reporting a vulnerability

Report privately through
[GitHub Security Advisories](https://github.com/sebastienrousseau/camt-exceptions/security/advisories/new).
Please do not open a public issue for a security problem.

## What this package does

It builds and validates two ISO 20022 message types. It sends nothing,
stores nothing, and holds no credentials. XML is produced from a template
and checked against the schema shipped with the package; no schema is
fetched at runtime.

## Transports

The server speaks MCP over stdio by default. `--transport
streamable-http` and `--transport sse` open a listener that binds
`127.0.0.1` unless `--host` says otherwise and carries no authentication
or TLS of its own. Do not bind a routable address without a gateway in
front of it that adds both.

An MCP server is driven by a model, so its inputs are not necessarily
written by a person who read the docs. Records handed to the tools are
validated, not executed; treat the payment references, agent BICs and
reasons they carry as data subject to your own confidentiality rules,
because they reach the model's context and any transport in between.

## The failure mode worth guarding against

`generate_message` **returns an error dict rather than raising**:

```python
{"error": "camt.029.001.14 is missing required field(s): confirmation_code"}
```

A caller that does not check `"error"` will treat a refusal as a message and
may send an empty or partial document downstream. That is the most likely
way this package contributes to an incident, and it is a calling convention
rather than a defect — but it deserves stating.

Always check, or use `validate_xml` on the result before acting on it.

## Dependencies

`cryptography` is floored at 50.0.0, the release patching a high-severity
advisory. Nothing else in the tree constrained it, so a resolver was free to
pick a vulnerable version.

That floor was cut into the tree as `0.0.16` and **never published** — PyPI's
latest was `0.0.15` — so no dependent received it until `0.0.17`. If you are
pinned below `0.0.17`, upgrade.

## Continuous integration

- `ci.yml` runs ruff, black, mypy --strict and pytest with the 100%
  line+branch coverage gate, then the examples and the benchmark, on
  every push and pull request.
- `codeql.yml` runs GitHub's CodeQL Python analysis on every push, pull
  request and weekly.
- `scorecard.yml` publishes the OpenSSF Scorecard weekly; every action
  in every workflow is pinned by commit SHA.
- `dco.yml` requires a `Signed-off-by:` trailer on every commit.
- `mcp-inspect.yml` lists the tools through the MCP Inspector over
  stdio, streamable HTTP and SSE.
- Dependabot (`.github/dependabot.yml`) proposes pip and GitHub Actions
  updates weekly.
- `release.yml` publishes to PyPI through OIDC trusted publishing with
  SLSA build provenance, cosign signatures and SBOMs.

<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security Policy

## Supported versions

| Version  | Supported |
| -------- | --------- |
| 0.0.17   | :white_check_mark: |
| < 0.0.17 | :x:               |

## Reporting a vulnerability

Report privately through
[GitHub Security Advisories](https://github.com/sebastienrousseau/camt-exceptions/security/advisories/new).
Please do not open a public issue for a security problem.

## What this package does

It builds and validates two ISO 20022 message types. It sends nothing,
stores nothing, and holds no credentials. XML is produced from a template
and checked against the schema shipped with the package; no schema is
fetched at runtime.

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

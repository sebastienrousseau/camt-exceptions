# camt-exceptions: ISO 20022 Exceptions & Investigations, generated + XSD-valid

**Generate and validate ISO 20022 Exceptions & Investigations (E&I) `camt`
messages — with an [MCP][mcp] server.** Starts with **`camt.056`** (FI-to-FI
Payment Cancellation Request): the message a bank sends to *recall or cancel* a
payment it already dispatched — a duplicate, an erroneous amount, a fraud
recall. Output is validated against the **official bundled XSD** before it's
returned.

> **Latest release: v0.0.13** — `camt.056` + `camt.029` generation + validation, 4 MCP
> tools over stdio, 100% branch coverage, for Python 3.10+. Part of the
> [ISO 20022 MCP suite](#the-suite). Additional E&I messages (camt.029, camt.026,
> camt.027, camt.087) plug into the same engine.

## Why E&I

When a payment goes wrong, the fix is an Exceptions & Investigations message —
and these are the *least* tooled corner of ISO 20022. `camt.056` alone covers
the single most common need: **"I need to cancel/recall that payment."** This
library makes it a one-call, schema-valid operation for an agent, with the same
depth as the credit-transfer generators elsewhere in the suite.

## Install

```sh
pip install camt-exceptions
# or run the MCP server without installing:
uvx camt-exceptions
```

MCP client config (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "camt-exceptions": {
      "command": "camt-exceptions-mcp"
    }
  }
}
```

## Quick start — cancel a payment

```python
from camt_exceptions import generator as g

xml = g.generate_message("camt.056.001.12", {
    "assignment_id": "CXL-001",
    "assigner_agent_bic": "DEUTDEFF",
    "assignee_agent_bic": "COBADEFF",
    "creation_date_time": "2026-03-02T10:00:00",
    "original_msg_id": "MSG-ORIG-001",
    "original_msg_nm_id": "pacs.008.001.08",
    "transactions": [{
        "original_end_to_end_id": "E2E-001",
        "original_interbank_settlement_amount": "1000.00",
        "original_interbank_settlement_currency": "EUR",
        "cancellation_reason_cd": "DUPL",       # duplicate payment
    }],
})
assert g.validate_xml("camt.056.001.12", xml)["is_valid"]   # True
```

## Tools

| Tool | What it does |
| --- | --- |
| `list_message_types` | List supported E&I message types and names. |
| `get_required_fields` | Required top-level fields for a message type. |
| `generate_message` | Generate a validated E&I XML message from a record (validated against the bundled XSD before return). |
| `validate_xml` | Validate raw XML against a message type's bundled XSD. |

## Supported messages

| Message | Name | Status |
| --- | --- | --- |
| `camt.056.001.12` | FI to FI Payment Cancellation Request | ✅ |
| `camt.029.001.14` | Resolution of Investigation | ✅ |
| `camt.026` | Unable to Apply | planned |
| `camt.027` | Claim Non-Receipt | planned |
| `camt.087` | Request to Modify Payment | planned |

Each new message plugs into the same engine: bundle its official XSD +
`template.xml` and register it in `MESSAGE_TYPES`. Generated output is always
XSD-validated before return, so correctness is machine-checked, not asserted.

> Note: the payment-status and return messages of the E&I family —
> **`pacs.002`** (Payment Status Report) and **`pacs.004`** (Payment Return) —
> are already generated, XSD-valid, by [`pacs008-mcp`][pacs008-mcp].

## The suite

Part of a family of vendor-neutral, Python-native ISO 20022 MCP servers:

- [`iso20022-mcp`][iso20022-mcp] — unified gateway across the families.
- [`pain001-mcp`][pain001-mcp] · [`pacs008-mcp`][pacs008-mcp] ·
  [`camt053-mcp`][camt053-mcp] · [`acmt001-mcp`][acmt001-mcp] — per-family servers.
- [`reconcile-mcp`][reconcile-mcp] — statement/payment reconciliation.

## Development

```sh
git clone https://github.com/sebastienrousseau/camt-exceptions
cd camt-exceptions
python -m venv .venv && . .venv/bin/activate
pip install -e . && pip install pytest pytest-cov ruff black mypy
pytest                      # 100% branch coverage gate; output is XSD-validated
ruff check camt_exceptions tests && black --check camt_exceptions tests && mypy camt_exceptions
```

## Licence

Code licensed under the [Apache License, Version 2.0](LICENSE). Bundled ISO
20022 message schemas (`*.xsd`) are © ISO 20022 and redistributed under the
ISO 20022 terms; they are the same schemas published at
[iso20022.org](https://www.iso20022.org).

---

`mcp-name: io.github.sebastienrousseau/camt-exceptions`

[mcp]: https://modelcontextprotocol.io
[iso20022-mcp]: https://github.com/sebastienrousseau/iso20022-mcp
[pain001-mcp]: https://github.com/sebastienrousseau/pain001-mcp
[pacs008-mcp]: https://github.com/sebastienrousseau/pacs008-mcp
[camt053-mcp]: https://github.com/sebastienrousseau/camt053-mcp
[acmt001-mcp]: https://github.com/sebastienrousseau/acmt001-mcp
[reconcile-mcp]: https://github.com/sebastienrousseau/reconcile-mcp

# camt-exceptions

Raise and resolve ISO 20022 **exceptions and investigations** — the messages
banks exchange when a payment needs stopping, returning, or explaining.

| Message | What it is |
|---|---|
| `camt.056.001.12` | FI to FI Payment Cancellation Request |
| `camt.029.001.14` | Resolution of Investigation |

```{toctree}
:maxdepth: 2
:caption: Contents

readme
api
adr/index
roadmap
changelog
```

## The pair

`camt.056` asks: *stop or return this payment.* `camt.029` answers: *here is
what happened to it.* Together they are the formal record of an
investigation, which is what a bank needs when a customer says the money
went to the wrong place.

```python
from camt_exceptions.server import generate_message, get_required_fields

record = {
    "assignment_id": "ASG-2026-0001",
    "assigner_agent_bic": "DEUTDEFF",
    "assignee_agent_bic": "NWBKGB2L",
    "creation_date_time": "2026-06-21T10:00:00",
}
result = generate_message("camt.056.001.12", record)
```

## Two things to know before you call it

**The two types do not require the same fields.** `camt.029` additionally
needs a `confirmation_code`; `camt.056` does not. Ask rather than assume:

```python
get_required_fields("camt.029.001.14")["required_fields"]
# ['assignment_id', 'assigner_agent_bic', 'assignee_agent_bic',
#  'creation_date_time', 'confirmation_code']
```

**`generate_message` returns an error dict; it does not raise.**

```python
result = generate_message(message_type, record)
if "error" in result:
    ...            # refused
xml = result["xml"]
```

A caller that does not check will treat a refusal as a message. This is easy
to get wrong: the benchmark in this repository did exactly that on its first
run, timing the rejection path for one of the two types and reporting the
result as throughput.

## Install

```sh
pip install camt-exceptions        # Python 3.10+
uvx camt-exceptions                # or run the MCP server without installing
```

## Transports

```sh
camt-exceptions-mcp                                   # stdio (default)
camt-exceptions-mcp --transport streamable-http       # HTTP on 127.0.0.1:8000/mcp
camt-exceptions-mcp --transport sse --port 8001       # the older HTTP+SSE transport
```

Streamable HTTP serves both current protocol revisions (2026-07-28
stateless with `server/discover`, and 2025-11-25 with the `initialize`
handshake) on one endpoint. The listener binds loopback unless told
otherwise and carries no authentication; put it behind a gateway before
binding a routable address. See ADR 0001 for the decision.

## Tools

| Tool | Returns |
|---|---|
| `list_message_types` | Both supported types with their names |
| `get_required_fields` | What a given type requires |
| `generate_message` | `{"xml": ...}` or `{"error": ...}` |
| `validate_xml` | `{"is_valid": bool, "errors": [...]}` |

The `build_investigation_message` prompt walks a client through the four
tools in order; the `camt-exceptions://message-types` and
`camt-exceptions://required-fields/{message_type}` resources expose the
catalogue to clients that read resources rather than call tools.

## Performance

[`benches/bench_investigations.py`](https://github.com/sebastienrousseau/camt-exceptions/blob/main/benches/bench_investigations.py).

E&I messages are small — a few hundred bytes — so there is no size axis
worth sweeping. The cost is per call, which is how they arrive: an
operations team chasing a failed batch raises one per payment.

```
        message type   bytes  generate ms  validate ms  refuse ms
     camt.056.001.12     703         0.25         0.25      0.001
     camt.029.001.14     568         0.25         0.25      0.001
```

- **About 0.25 ms per message.** A queue of a few thousand investigations is
  a background job, not a capacity problem.
- **Validation costs about the same as generation** (0.99x). Both touch the
  schema, so generating and then validating pays for it twice.
- **Refusal is essentially free** (~0.001 ms) — the work is skipped rather
  than done and discarded, which is the right way round.

**The first message in a process costs about 205 ms**, against 0.32 ms for
the second — a **640x** difference, because the XSD compiles once and is
then cached. A worker handling one investigation per invocation pays that
every time; a long-lived one pays it once. Measured in a fresh interpreter,
since timing it in-process reports the warm number.

## Worked examples

Both run standalone with no arguments and no network:

- [`examples/01_cancel_a_payment.py`](https://github.com/sebastienrousseau/camt-exceptions/blob/main/examples/01_cancel_a_payment.py)
- [`examples/02_resolve_an_investigation.py`](https://github.com/sebastienrousseau/camt-exceptions/blob/main/examples/02_resolve_an_investigation.py)

## Quality gates

Every change passes a 100% line and branch coverage gate, a 100%
docstring gate (`interrogate`), property-based tests (Hypothesis), a
mutation-testing floor over the tool handlers and the generator
(`mutmut`), ruff, black and strict mypy, and a benchmark that runs in CI
so it cannot rot.

## Quick links

- [Source on GitHub](https://github.com/sebastienrousseau/camt-exceptions)
- [PyPI release](https://pypi.org/project/camt-exceptions/)
- [The ISO 20022 MCP suite](https://github.com/sebastienrousseau/iso20022-mcp)

## Licence

Apache-2.0 OR MIT, at your option.

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`

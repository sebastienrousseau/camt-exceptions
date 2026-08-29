# camt-exceptions

Raise and resolve ISO 20022 **exceptions and investigations** — the messages
banks exchange when a payment needs stopping, returning, or explaining.

| Message | What it is |
|---|---|
| `camt.056.001.12` | FI to FI Payment Cancellation Request |
| `camt.029.001.14` | Resolution of Investigation |

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

## Tools

| Tool | Returns |
|---|---|
| `list_message_types` | Both supported types with their names |
| `get_required_fields` | What a given type requires |
| `generate_message` | `{"xml": ...}` or `{"error": ...}` |
| `validate_xml` | `{"is_valid": bool, "errors": [...]}` |
| `build_investigation_message` | Higher-level construction |

## Performance

[`benches/bench_investigations.py`](../benches/bench_investigations.py).

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

- [`examples/01_cancel_a_payment.py`](../examples/01_cancel_a_payment.py)
- [`examples/02_resolve_an_investigation.py`](../examples/02_resolve_an_investigation.py)

## Licence

Apache-2.0 OR MIT, at your option.

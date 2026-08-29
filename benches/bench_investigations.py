#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What an exceptions-and-investigations message costs to build and check.

E&I messages are small — a cancellation request is a few hundred bytes, not
a statement with ten thousand entries — so there is no size axis worth
sweeping. The cost is per call, and per call is exactly how they arrive: an
operations team chasing a batch of failed payments raises one `camt.056` per
payment, and an agent working a queue does the same.

So the questions are different from a parser's:

* **What does one message cost?** If generation is milliseconds, a queue of
  a few thousand investigations is a background job. If it is tens of
  milliseconds, it is a capacity problem.

* **How does validation compare with generation?** Both touch the schema.
  A large gap in either direction is worth knowing: a caller that generates
  and then validates is paying for the schema twice if generation already
  validated.

* **What does the first call cost?** The XSD compiles once per process and
  is then cached, so the first message is far dearer than the rest.
  A worker handling one investigation per invocation pays that every time;
  a long-lived one pays it once. A mean over warm calls hides it entirely.

Run::

    python benches/bench_investigations.py
    python benches/bench_investigations.py --json
    python benches/bench_investigations.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from camt_exceptions import server  # noqa: E402

#: Plausible values for every field the E&I types ask for. The record is
#: built per message type from ``get_required_fields`` rather than shared,
#: because the types differ: ``camt.029`` additionally requires
#: ``confirmation_code``. A shared record generated fine for one type and
#: returned an error dict for the other, and every ratio computed from that
#: was meaningless.
_VALUES = {
    "assignment_id": "ASG-BENCH-0001",
    "assigner_agent_bic": "DEUTDEFF",
    "assignee_agent_bic": "NWBKGB2L",
    "creation_date_time": "2026-06-21T10:00:00",
    "confirmation_code": "CNCL",
    "case_id": "CASE-BENCH-0001",
    "original_message_id": "PMT-BENCH-0001",
}


def record_for(message_type: str) -> dict:
    """A record carrying exactly what this message type requires."""
    required = server.get_required_fields(message_type)["required_fields"]
    return {name: _VALUES.get(name, f"BENCH-{name}") for name in required}


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The warm-up matters here: the XSD compiles on first use, so without it
    the first sample measures schema compilation rather than the operation.
    That cost is real and is reported separately below, not folded into the
    per-call number.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def _safe(call):
    """A refusal is a result: how fast it declines is a measurement."""

    def wrapped():
        try:
            return call()
        except Exception:
            return None

    return wrapped


def measure(message_type: str, repeats: int) -> dict:
    record = record_for(message_type)
    generated = server.generate_message(message_type, record)
    if "error" in generated:
        # Refuse to report ratios against a refusal. generate_message
        # returns an error dict rather than raising, so a benchmark that
        # does not look would happily time the rejection path and present
        # it as throughput.
        return {
            "message_type": message_type,
            "error": generated["error"],
        }

    generate = _best(
        lambda: server.generate_message(message_type, record), repeats
    )
    xml = generated["xml"]
    validate = _best(
        _safe(lambda: server.validate_xml(message_type, xml)), repeats
    )
    fields = _best(lambda: server.get_required_fields(message_type), repeats)
    # A record missing a mandatory field. Refusing should be cheaper than
    # producing, since the work is skipped rather than done and discarded.
    broken = {k: v for k, v in record.items() if k != "assignment_id"}
    refuse = _best(
        _safe(lambda: server.generate_message(message_type, broken)), repeats
    )
    return {
        "message_type": message_type,
        "generate_ms": generate * 1e3,
        "validate_ms": validate * 1e3,
        "required_fields_us": fields * 1e6,
        "refuse_ms": refuse * 1e3,
        "validate_over_generate": validate / generate if generate else 0.0,
        "refuse_over_generate": refuse / generate if generate else 0.0,
        "bytes": len(xml),
    }


def measure_cold(message_type: str) -> dict:
    """First message in a fresh interpreter against the second.

    Run as a subprocess on purpose: measured in-process this reports a warm
    cache and misses the whole point.
    """
    script = (
        "import sys, time, json\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "from camt_exceptions import server\n"
        f"mt = {message_type!r}\n"
        f"rec = json.loads({json.dumps(record_for(message_type))!r})\n"
        "t0 = time.perf_counter(); server.generate_message(mt, rec)\n"
        "cold = time.perf_counter() - t0\n"
        "t1 = time.perf_counter(); server.generate_message(mt, rec)\n"
        "warm = time.perf_counter() - t1\n"
        "print(json.dumps({'cold': cold, 'warm': warm}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        return {"message_type": message_type, "error": result.stderr[-200:]}
    data = json.loads(result.stdout.strip().splitlines()[-1])
    return {
        "message_type": message_type,
        "cold_ms": data["cold"] * 1e3,
        "warm_ms": data["warm"] * 1e3,
        "cold_over_warm": (
            data["cold"] / data["warm"] if data["warm"] else 0.0
        ),
    }


def run(quick: bool) -> dict:
    types = [
        entry["message_type"]
        for entry in server.list_message_types()["message_types"]
    ]
    if quick:
        types = types[:1]
    repeats = 20 if quick else 200
    return {
        "types": [measure(mt, repeats) for mt in types],
        "cold": measure_cold(types[0]),
    }


def render(results: dict) -> None:
    print(
        f"{'message type':>20}{'bytes':>8}{'generate ms':>13}"
        f"{'validate ms':>13}{'refuse ms':>11}{'fields us':>11}"
    )
    for row in results["types"]:
        if "error" in row:
            print(f"{row['message_type']:>20}  refused: {row['error'][:50]}")
            continue
        print(
            f"{row['message_type']:>20}{row['bytes']:>8}"
            f"{row['generate_ms']:>13.2f}{row['validate_ms']:>13.2f}"
            f"{row['refuse_ms']:>11.3f}{row['required_fields_us']:>11.1f}"
        )

    rows = [r for r in results["types"] if "error" not in r]
    if rows:
        per_hour = 3_600_000 / max(r["generate_ms"] for r in rows)
        print(
            f"\n  At the dearest message here, one core produces about "
            f"{per_hour:,.0f} messages an hour. An operations team chasing a\n"
            f"  failed batch raises one per payment, so that is the number "
            f"that decides whether a queue is a background job."
        )
        worst_v = max(r["validate_over_generate"] for r in rows)
        print(
            f"\n  validate_xml costs up to {worst_v:.2f}x generate_message. "
            f"Both touch the schema, so a caller that generates and then\n"
            f"  validates is paying for it twice if generation already did."
        )
        worst_r = max(r["refuse_over_generate"] for r in rows)
        verdict = (
            "cheaper, as it should be"
            if worst_r < 0.9
            else "NOT cheaper — the work is being done and discarded"
        )
        print(
            f"\n  Refusing a record missing a mandatory field costs "
            f"{worst_r:.2f}x a successful generate — {verdict}."
        )

    cold = results["cold"]
    print("\nfirst message in a fresh interpreter against the second")
    if "error" in cold:
        print(f"  failed: {cold['error']}")
    else:
        print(
            f"  cold {cold['cold_ms']:,.0f} ms, warm "
            f"{cold['warm_ms']:,.2f} ms — {cold['cold_over_warm']:,.0f}x"
        )
        print(
            "  The XSD compiles once per process. A worker handling one\n"
            "  investigation per invocation pays that every time; a\n"
            "  long-lived one pays it once. Invisible to any benchmark\n"
            "  reporting a mean over warm calls."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="one type, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

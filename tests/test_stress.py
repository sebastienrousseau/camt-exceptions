# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Load/stress tests for camt.056 generation and validation.

Marked ``perf`` and excluded from the default coverage-gated run (the
pyproject addopts select ``-m "not perf"``, matching the suite-wide
camt053 convention). Run explicitly with::

    pytest tests/test_stress.py -m perf --no-cov

Covers three failure modes the functional suite cannot see:

* thread-safety / error rate under sustained concurrent load (the MCP
  server handles tools concurrently, and the module-level Jinja and
  XSD caches are shared);
* memory growth over a long soak (leaks in the cached schema/template
  paths would accumulate);
* large-batch behaviour (many transactions in one message, many
  messages in one burst).

Latency bounds are deliberately generous -- they are regression
tripwires for order-of-magnitude blowups, not benchmarks.
"""

import gc
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

import pytest

from camt_exceptions import generator

pytestmark = pytest.mark.perf

MT = "camt.056.001.12"

# Sustained-load shape: 32 concurrent workers, several hundred
# iterations each (one iteration = one generate + one validate).
WORKERS = 32
ITERATIONS_PER_WORKER = 300

# Generous latency ceilings (seconds). Warm single-threaded calls run
# in well under 1 ms; these only catch order-of-magnitude regressions.
P95_CEILING_S = 0.25
P99_CEILING_S = 1.0

# Soak / memory bounds.
SOAK_ITERATIONS = 2_000
MAX_SOAK_GROWTH_BYTES = 8 * 1024 * 1024  # 8 MiB

# Large-batch shape.
BATCH_TRANSACTIONS = 500
BATCH_DOCUMENTS = 250


def _record(seq: int) -> dict:
    """A unique, XSD-valid camt.056 record for iteration ``seq``."""
    return {
        "assignment_id": f"CXL-STRESS-{seq:06d}",
        "assigner_agent_bic": "DEUTDEFF",
        "assignee_agent_bic": "COBADEFF",
        "creation_date_time": "2026-03-02T10:00:00",
        "original_msg_id": f"MSG-ORIG-{seq:06d}",
        "original_msg_nm_id": "pacs.008.001.08",
        "transactions": [
            {
                "original_end_to_end_id": f"E2E-{seq:06d}",
                "original_tx_id": f"TX-{seq:06d}",
                "original_interbank_settlement_amount": "1000.00",
                "original_interbank_settlement_currency": "EUR",
                "cancellation_reason_cd": "DUPL",
            }
        ],
    }


def _generate_and_validate(seq: int) -> float:
    """One load iteration; returns its wall-clock latency in seconds."""
    started = time.perf_counter()
    xml = generator.generate_message(MT, _record(seq))
    result = generator.validate_xml(MT, xml)
    elapsed = time.perf_counter() - started
    assert result["is_valid"] is True, result["errors"]
    assert f"CXL-STRESS-{seq:06d}" in xml
    return elapsed


def _warm_caches() -> None:
    """Prime the cached XSD + template so tests measure steady state."""
    generator.generate_message(MT, _record(0))


def _percentile(latencies: list, fraction: float) -> float:
    """The ``fraction`` percentile of ``latencies`` (nearest-rank)."""
    ordered = sorted(latencies)
    index = min(len(ordered) - 1, int(len(ordered) * fraction))
    return ordered[index]


def test_sustained_concurrent_generation_and_validation():
    """32 workers x 300 iterations: zero errors, sane tail latency."""
    _warm_caches()
    total = WORKERS * ITERATIONS_PER_WORKER
    errors: list = []
    latencies: list = []

    def worker(worker_id: int) -> list:
        results = []
        for i in range(ITERATIONS_PER_WORKER):
            seq = worker_id * ITERATIONS_PER_WORKER + i
            try:
                results.append(_generate_and_validate(seq))
            except Exception as exc:  # noqa: BLE001 - collected, not hidden
                errors.append((seq, repr(exc)))
        return results

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for chunk in pool.map(worker, range(WORKERS)):
            latencies.extend(chunk)

    assert errors == [], f"{len(errors)}/{total} iterations failed: " + str(
        errors[:5]
    )
    assert len(latencies) == total
    p95 = _percentile(latencies, 0.95)
    p99 = _percentile(latencies, 0.99)
    assert p95 < P95_CEILING_S, f"p95 latency {p95:.4f}s under load"
    assert p99 < P99_CEILING_S, f"p99 latency {p99:.4f}s under load"


def test_soak_memory_growth_is_bounded():
    """A long generate+validate soak must not accumulate memory."""
    _warm_caches()
    gc.collect()
    tracemalloc.start()
    try:
        # Let lazily-built internals (validators, iterators) settle
        # before taking the baseline.
        for seq in range(100):
            _generate_and_validate(seq)
        gc.collect()
        baseline, _ = tracemalloc.get_traced_memory()

        for seq in range(SOAK_ITERATIONS):
            _generate_and_validate(seq)
        gc.collect()
        final, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    growth = final - baseline
    assert growth < MAX_SOAK_GROWTH_BYTES, (
        f"traced memory grew {growth / 1024 / 1024:.2f} MiB over "
        f"{SOAK_ITERATIONS} iterations"
    )


def test_large_batch_single_message_many_transactions():
    """One camt.056 carrying 500 transactions renders and validates."""
    record = _record(0)
    record["transactions"] = [
        {
            "original_end_to_end_id": f"E2E-BULK-{i:05d}",
            "original_tx_id": f"TX-BULK-{i:05d}",
            "original_interbank_settlement_amount": "1000.00",
            "original_interbank_settlement_currency": "EUR",
            "cancellation_reason_cd": "DUPL",
        }
        for i in range(BATCH_TRANSACTIONS)
    ]
    xml = generator.generate_message(MT, record)
    assert xml.count("<TxInf>") == BATCH_TRANSACTIONS
    assert generator.validate_xml(MT, xml)["is_valid"] is True


def test_large_batch_many_documents():
    """A burst of 250 distinct documents: all unique, all XSD-valid."""
    documents = [
        generator.generate_message(MT, _record(seq))
        for seq in range(BATCH_DOCUMENTS)
    ]
    assert len(set(documents)) == BATCH_DOCUMENTS
    for seq, xml in enumerate(documents):
        assert f"E2E-{seq:06d}" in xml
        result = generator.validate_xml(MT, xml)
        assert result["is_valid"] is True, (seq, result["errors"])

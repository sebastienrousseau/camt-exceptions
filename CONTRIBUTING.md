<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing

Thanks for looking. This package builds and validates the two ISO 20022
exceptions-and-investigations messages.

## Before you open a pull request

```sh
pip install -e .
pip install pytest pytest-cov ruff black mypy
pytest                                             # tests plus the gate
ruff check camt_exceptions/ tests/ examples/ benches/
black --check camt_exceptions/ tests/ examples/ benches/
mypy camt_exceptions/
python benches/bench_investigations.py --quick
```

`pytest` fails below **100% branch coverage**.

## The calling convention to preserve

`generate_message` returns `{"xml": ...}` or `{"error": ...}`. It does not
raise. Every caller has to check, and every example here does.

If you add a tool, keep the convention — mixing raising and non-raising
tools in one server is worse than either alone. And if you change it, change
it everywhere at once and say so loudly in the changelog: silently switching
from an error dict to an exception turns every unchecked caller into a
crash.

## Adding a message type

The two supported types require different fields; `camt.029` needs a
`confirmation_code` that `camt.056` does not. Declare requirements in the
table `get_required_fields` reads, so callers can ask rather than guess, and
add the type to the benchmark — it builds its record from
`get_required_fields`, so a new type is measured automatically.

## Benchmarks

`benches/` measures per-call cost, because these messages are small and
arrive one at a time. Two numbers matter: ~0.25 ms warm, and ~205 ms for the
first message in a process while the XSD compiles.

It asserts no threshold — wall-clock is not comparable between machines —
but CI runs `--quick` so a benchmark that stops compiling fails the build
rather than rotting.

## The shared conformance file

`tests/test_suite_conformance.py` is generated from one canonical copy
shared across all 32 repositories. **Do not edit it here.**

## Versioning

**Versions increment by 0.0.1.** `0.1.0` follows `0.0.999`.

Change `pyproject.toml` and `camt_exceptions/__init__.py` together, add a
`CHANGELOG.md` entry, **and make sure the release is actually tagged.** This
package sat at `0.0.16` in the tree with `0.0.15` on PyPI for weeks, which
meant a security floor nobody received.

## Licence

Apache-2.0 OR MIT, at your option.

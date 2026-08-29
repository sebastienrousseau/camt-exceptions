#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
"""Answer a cancellation request, and validate the answer.

`camt.029` is the resolution: the assignee tells the assigner what happened
to the payment they asked about. It needs a `confirmation_code` that
`camt.056` does not, which is the sort of difference worth discovering from
`get_required_fields` rather than from a rejection.

Run with ``python examples/02_resolve_an_investigation.py``.
"""

from camt_exceptions.server import (
    generate_message,
    get_required_fields,
    validate_xml,
)


def main() -> None:
    """Build a resolution, then check it against the schema."""
    message_type = "camt.029.001.14"
    required = get_required_fields(message_type)["required_fields"]
    print(f"{message_type} requires: {', '.join(required)}\n")

    record = {
        "assignment_id": "ASG-2026-0001",
        "assigner_agent_bic": "NWBKGB2L",
        "assignee_agent_bic": "DEUTDEFF",
        "creation_date_time": "2026-06-21T11:00:00",
        "confirmation_code": "CNCL",
    }

    result = generate_message(message_type, record)
    if "error" in result:
        print(f"refused: {result['error']}")
        return

    xml = result["xml"]
    print(f"generated {len(xml)} bytes")

    verdict = validate_xml(message_type, xml)
    print(f"validates: {verdict}")

    # And what a missing field looks like, since that is the common case.
    incomplete = {k: v for k, v in record.items() if k != "confirmation_code"}
    print(
        f"\nwithout confirmation_code -> "
        f"{generate_message(message_type, incomplete).get('error')}"
    )


if __name__ == "__main__":
    main()

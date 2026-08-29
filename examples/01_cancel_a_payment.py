#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
"""Raise a cancellation request for a payment that should not have gone.

`camt.056` is the message a bank sends when it wants a payment stopped or
returned. It is the first half of an investigation; `camt.029` is the reply.

Run with ``python examples/01_cancel_a_payment.py``.
"""

from camt_exceptions.server import generate_message, get_required_fields


def main() -> None:
    """Build a cancellation request and show what it required."""
    message_type = "camt.056.001.12"
    required = get_required_fields(message_type)["required_fields"]
    print(f"{message_type} requires: {', '.join(required)}\n")

    record = {
        "assignment_id": "ASG-2026-0001",
        "assigner_agent_bic": "DEUTDEFF",
        "assignee_agent_bic": "NWBKGB2L",
        "creation_date_time": "2026-06-21T10:00:00",
    }

    result = generate_message(message_type, record)

    # generate_message returns an error dict rather than raising. A caller
    # that does not look will happily treat a refusal as a message.
    if "error" in result:
        print(f"refused: {result['error']}")
        return

    print(result["xml"])


if __name__ == "__main__":
    main()

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
"""Property-based tests over the logic this package owns.

The generator renders a record through a template and checks the result
against the bundled XSD; the server wraps it in error envelopes. Both
have invariants an agent relies on that a handful of hand-written
records cannot establish: any record built from schema-valid values
must produce schema-valid XML (so the template escapes correctly and
never emits an element the schema forbids), every missing required field
must be named, an unknown message type must always come back as an
``{"error": ...}`` payload, and ``validate_xml`` must answer with a
report whatever it is handed. Hypothesis searches the input space for a
counterexample instead of trusting the examples the unit tests use.
"""

from __future__ import annotations

import datetime
import json
import string

from hypothesis import given
from hypothesis import strategies as st

import camt_exceptions.server as server
from camt_exceptions import generator

MT056 = "camt.056.001.12"
MT029 = "camt.029.001.14"
TOOLS = (
    "list_message_types",
    "get_required_fields",
    "generate_message",
    "validate_xml",
)

# ---------------------------------------------------------------------------
# Strategies drawn from the XSD types the templates bind: Max35Text (with
# the characters Jinja must escape), BICFIDec2014Identifier, ISODateTime,
# the four-character external code lists, and a settlement amount.
# ---------------------------------------------------------------------------
_MAX35 = st.text(
    alphabet=string.ascii_letters + string.digits + " <>&\"'-_./:",
    min_size=1,
    max_size=35,
)
_MAX4 = st.text(
    alphabet=string.ascii_uppercase + string.digits, min_size=1, max_size=4
)
_BIC = st.from_regex(
    r"[A-Z0-9]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?", fullmatch=True
)
_DATETIME = st.datetimes(
    min_value=datetime.datetime(2000, 1, 1),
    max_value=datetime.datetime(2099, 12, 31),
).map(datetime.datetime.isoformat)
_AMOUNT = st.decimals(
    min_value=0, max_value=10**12, places=2, allow_nan=False
).map(str)
_CURRENCY = st.from_regex(r"[A-Z]{3}", fullmatch=True)
_TEXT = st.text(max_size=40)

_ASSIGNMENT = st.fixed_dictionaries(
    {
        "assignment_id": _MAX35,
        "assigner_agent_bic": _BIC,
        "assignee_agent_bic": _BIC,
        "creation_date_time": _DATETIME,
    }
)
_TRANSACTION = st.fixed_dictionaries(
    {},
    optional={
        "cancellation_id": _MAX35,
        "original_end_to_end_id": _MAX35,
        "original_tx_id": _MAX35,
        "cancellation_reason_cd": _MAX4,
        "cancellation_reason_addtl_inf": _MAX35,
    },
).flatmap(
    lambda tx: st.one_of(
        st.just(tx),
        st.fixed_dictionaries(
            {
                "original_interbank_settlement_amount": _AMOUNT,
                "original_interbank_settlement_currency": _CURRENCY,
            }
        ).map(lambda amt: {**tx, **amt}),
    )
)
_RECORD_056 = st.builds(
    lambda base, original, txs: {**base, **original, "transactions": txs},
    _ASSIGNMENT,
    st.one_of(
        st.just({}),
        st.fixed_dictionaries(
            {"original_msg_id": _MAX35, "original_msg_nm_id": _MAX35}
        ),
    ),
    st.lists(_TRANSACTION, max_size=3),
)
_RECORD_029 = st.builds(
    lambda base, code, case: {**base, "confirmation_code": code, **case},
    _ASSIGNMENT,
    _MAX4,
    st.one_of(
        st.just({}), st.fixed_dictionaries({"resolved_case_id": _MAX35})
    ),
)


# ---------------------------------------------------------------------------
# Round trip: any record of schema-valid values renders to XML the XSD
# accepts, through the tool as well as the generator.
# ---------------------------------------------------------------------------
@given(record=_RECORD_056)
def test_every_camt056_record_renders_xsd_valid_xml(record: dict) -> None:
    result = server.generate_message(MT056, record)
    assert set(result) == {"message_type", "xml"}
    assert result["message_type"] == MT056
    assert result["xml"].startswith("<?xml")
    report = server.validate_xml(MT056, result["xml"])
    assert report == {"message_type": MT056, "is_valid": True, "errors": []}
    # Every transaction the record carried is rendered, none invented.
    assert result["xml"].count("<TxInf>") == len(record["transactions"])


@given(record=_RECORD_029)
def test_every_camt029_record_renders_xsd_valid_xml(record: dict) -> None:
    xml = generator.generate_message(MT029, record)
    assert generator.validate_xml(MT029, xml)["is_valid"] is True
    assert ("<RslvdCase>" in xml) == ("resolved_case_id" in record)


# ---------------------------------------------------------------------------
# Required fields: every one that is missing or blank is named, in the
# order the spec declares them, and nothing else is.
# ---------------------------------------------------------------------------
@given(
    message_type=st.sampled_from([MT056, MT029]),
    record=_RECORD_029,
    dropped=st.sets(
        st.sampled_from(generator.get_required_fields(MT029)), min_size=1
    ),
    blank=st.booleans(),
)
def test_every_missing_required_field_is_named(
    message_type: str, record: dict, dropped: set[str], blank: bool
) -> None:
    required = generator.get_required_fields(message_type)
    missing = [f for f in required if f in dropped]
    if not missing:
        return
    for field in dropped:
        if blank:
            record[field] = ""
        else:
            record.pop(field)
    result = server.generate_message(message_type, record)
    assert set(result) == {"error"}
    assert result["error"] == (
        f"{message_type} is missing required field(s): {', '.join(missing)}"
    )


@given(message_type=st.sampled_from([MT056, MT029]))
def test_required_fields_are_handed_out_as_fresh_copies(
    message_type: str,
) -> None:
    first = generator.get_required_fields(message_type)
    first.append("tampered")
    assert "tampered" not in generator.get_required_fields(message_type)
    assert (
        len(first) == len(generator.MESSAGE_TYPES[message_type].required) + 1
    )


# ---------------------------------------------------------------------------
# Error envelopes: an unknown type is data, never an exception, on every
# surface that takes one, and the payload names the offending type and
# the supported ones.
# ---------------------------------------------------------------------------
@given(message_type=_TEXT)
def test_unknown_message_types_yield_error_payloads(
    message_type: str,
) -> None:
    if message_type in generator.MESSAGE_TYPES:
        return
    payloads = [
        server.get_required_fields(message_type),
        server.generate_message(message_type, {}),
        server.validate_xml(message_type, "<x/>"),
        json.loads(server.required_fields_resource(message_type)),
    ]
    known = ", ".join(sorted(generator.MESSAGE_TYPES))
    for payload in payloads:
        json.dumps(payload)
        assert payload == {
            "error": (
                f"unsupported message type {message_type!r}; "
                f"supported: {known}"
            )
        }


# ---------------------------------------------------------------------------
# validate_xml: a report for any input, internally consistent, and the
# same answer twice (the schema cache must not change the verdict).
# ---------------------------------------------------------------------------
@given(message_type=st.sampled_from([MT056, MT029]), xml=_TEXT)
def test_validate_xml_never_raises_and_reports_consistently(
    message_type: str, xml: str
) -> None:
    report = server.validate_xml(message_type, xml)
    json.dumps(report)
    assert set(report) == {"message_type", "is_valid", "errors"}
    assert report["message_type"] == message_type
    assert report["is_valid"] == (report["errors"] == [])
    assert all(isinstance(e, str) and e for e in report["errors"])
    # Arbitrary short text is never a valid message.
    assert report["is_valid"] is False
    again = server.validate_xml(message_type, xml)
    assert again["is_valid"] == report["is_valid"]
    assert len(again["errors"]) == len(report["errors"])


# ---------------------------------------------------------------------------
# Resources are projections of the tools.
# ---------------------------------------------------------------------------
@given(message_type=st.one_of(_TEXT, st.sampled_from([MT056, MT029])))
def test_required_fields_resource_agrees_with_the_tool(
    message_type: str,
) -> None:
    assert json.loads(server.required_fields_resource(message_type)) == (
        server.get_required_fields(message_type)
    )


def test_message_types_resource_agrees_with_the_tool() -> None:
    assert json.loads(server.message_types_resource()) == (
        server.list_message_types()
    )
    assert server.list_message_types() == {
        "message_types": generator.list_message_types()
    }


# ---------------------------------------------------------------------------
# Prompt: a pure function of its argument that names every tool.
# ---------------------------------------------------------------------------
@given(message_type=_TEXT)
def test_prompt_names_the_type_and_every_tool(message_type: str) -> None:
    text = server.build_investigation_message(message_type)
    assert text.startswith(
        "Help me build a valid ISO 20022 Exceptions & Investigations "
        f"message of type {message_type}. Work through the tools in order:\n"
    )
    for step, tool in enumerate(TOOLS, start=1):
        assert f"{step}. Call {tool}" in text
    assert text.count(f"message_type={message_type!r}") == 3
    assert text.endswith("Report the final XML and its validation result.")
    assert text == server.build_investigation_message(message_type)

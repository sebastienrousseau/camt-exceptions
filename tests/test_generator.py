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

"""Tests for the E&I generation engine (camt.056)."""

import jinja2
import pytest

from camt_exceptions import generator

MT = "camt.056.001.12"


@pytest.fixture
def record():
    return {
        "assignment_id": "CXL-001",
        "assigner_agent_bic": "DEUTDEFF",
        "assignee_agent_bic": "COBADEFF",
        "creation_date_time": "2026-03-02T10:00:00",
        "original_msg_id": "MSG-ORIG-001",
        "original_msg_nm_id": "pacs.008.001.08",
        "transactions": [
            {
                "original_end_to_end_id": "E2E-001",
                "original_tx_id": "TX-001",
                "original_interbank_settlement_amount": "1000.00",
                "original_interbank_settlement_currency": "EUR",
                "cancellation_reason_cd": "DUPL",
            }
        ],
    }


def test_list_message_types():
    types = {t["message_type"] for t in generator.list_message_types()}
    assert MT in types


def test_get_required_fields():
    req = generator.get_required_fields(MT)
    assert "assignment_id" in req and "assigner_agent_bic" in req


def test_get_required_fields_unknown_raises():
    with pytest.raises(ValueError, match="unsupported message type"):
        generator.get_required_fields("camt.999.001.01")


def test_generate_message_is_xsd_valid(record):
    xml = generator.generate_message(MT, record)
    assert xml.startswith("<?xml")
    assert "urn:iso:std:iso:20022:tech:xsd:camt.056.001.12" in xml
    # Round-trip: the generated XML validates against the bundled XSD.
    assert generator.validate_xml(MT, xml)["is_valid"] is True


def test_generate_message_minimal_without_transactions():
    # Only the required assignment fields -- still XSD-valid.
    xml = generator.generate_message(
        MT,
        {
            "assignment_id": "CXL-2",
            "assigner_agent_bic": "DEUTDEFF",
            "assignee_agent_bic": "COBADEFF",
            "creation_date_time": "2026-03-02T10:00:00",
        },
    )
    assert generator.validate_xml(MT, xml)["is_valid"] is True


def test_generate_message_missing_required_field():
    with pytest.raises(ValueError, match="missing required field"):
        generator.generate_message(MT, {"assignment_id": "X"})


def test_generate_message_unknown_type():
    with pytest.raises(ValueError, match="unsupported message type"):
        generator.generate_message("camt.999.001.01", {})


def test_generate_message_rejects_invalid_output(monkeypatch, record):
    # If a template ever renders schema-invalid XML, generation must refuse it
    # rather than emit bad output. Force that path with a broken template.
    generator._template.cache_clear()
    bad = jinja2.Environment(autoescape=True).from_string("<Document/>")
    monkeypatch.setattr(generator, "_template", lambda mt: bad)
    with pytest.raises(ValueError, match="failed XSD validation"):
        generator.generate_message(MT, record)


def test_validate_xml_detects_invalid():
    result = generator.validate_xml(MT, "<Document>not valid</Document>")
    assert result["is_valid"] is False
    assert result["errors"]


def test_validate_xml_unknown_type_raises():
    with pytest.raises(ValueError, match="unsupported message type"):
        generator.validate_xml("camt.999.001.01", "<x/>")

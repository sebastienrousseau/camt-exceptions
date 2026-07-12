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

"""Tests for the camt-exceptions MCP server tool surface."""

import asyncio

import pytest

pytest.importorskip("mcp")

import camt_exceptions.server as srv  # noqa: E402
from camt_exceptions import __version__  # noqa: E402

MT = "camt.056.001.12"
EXPECTED_TOOLS = {
    "list_message_types",
    "get_required_fields",
    "generate_message",
    "validate_xml",
}


def _registered_tool_names() -> set[str]:
    manager = getattr(srv.server, "_tool_manager", None)
    if manager is not None and hasattr(manager, "list_tools"):
        return {tool.name for tool in manager.list_tools()}
    tools = asyncio.run(srv.server.list_tools())  # pragma: no cover
    return {tool.name for tool in tools}  # pragma: no cover


def test_all_tools_registered():
    assert _registered_tool_names() == EXPECTED_TOOLS


def test_server_version_override():
    assert srv.server._mcp_server.version == __version__


def test_list_message_types_tool():
    out = srv.list_message_types()
    assert any(t["message_type"] == MT for t in out["message_types"])


def test_get_required_fields_tool_happy_and_error():
    ok = srv.get_required_fields(MT)
    assert "assignment_id" in ok["required_fields"]
    err = srv.get_required_fields("camt.999.001.01")
    assert "error" in err


def test_generate_message_tool_happy_and_error():
    ok = srv.generate_message(
        MT,
        {
            "assignment_id": "CXL-1",
            "assigner_agent_bic": "DEUTDEFF",
            "assignee_agent_bic": "COBADEFF",
            "creation_date_time": "2026-03-02T10:00:00",
            "transactions": [{"cancellation_reason_cd": "DUPL"}],
        },
    )
    assert "urn:iso:std:iso:20022:tech:xsd:camt.056.001.12" in ok["xml"]
    err = srv.generate_message(MT, {"assignment_id": "X"})
    assert "error" in err


def test_validate_xml_tool_happy_and_error():
    xml = srv.generate_message(
        MT,
        {
            "assignment_id": "CXL-1",
            "assigner_agent_bic": "DEUTDEFF",
            "assignee_agent_bic": "COBADEFF",
            "creation_date_time": "2026-03-02T10:00:00",
        },
    )["xml"]
    assert srv.validate_xml(MT, xml)["is_valid"] is True
    err = srv.validate_xml("camt.999.001.01", "<x/>")
    assert "error" in err


def test_main_runs_server(monkeypatch):
    called = {}
    monkeypatch.setattr(
        srv.server, "run", lambda: called.setdefault("ran", True)
    )
    srv.main()
    assert called["ran"] is True

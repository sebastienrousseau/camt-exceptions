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

"""Model Context Protocol (MCP) server for ISO 20022 Exceptions & Investigations.

Exposes generation and validation of E&I ``camt`` messages -- starting with
``camt.056`` (FI to FI Payment Cancellation Request) -- as MCP tools. Each tool
is a thin wrapper over :mod:`camt_exceptions.generator`; tools return
JSON-serializable data and, on a :class:`ValueError`, return an
``{"error": ...}`` payload rather than raising.

Launching the server:
    * As a console script::

        camt-exceptions-mcp

    * In an MCP client config (e.g. Claude Desktop)::

        {
          "mcpServers": {
            "camt-exceptions": {
              "command": "camt-exceptions-mcp"
            }
          }
        }

stdio by default; ``--transport streamable-http`` or ``--transport sse``
listens on ``--host``/``--port`` instead. See :mod:`camt_exceptions._cli`.
"""

import json
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from camt_exceptions import __version__, _cli, generator
from camt_exceptions._mcp_compat import build_server

# The shim picks FastMCP (mcp 1.x) or MCPServer (mcp 2.x) and reports
# the package version in serverInfo either way.
server = build_server("camt-exceptions", __version__)

# Every tool is a pure, side-effect-free reader: it computes solely from its
# arguments and the XSDs/templates bundled with this package. Nothing opens a
# caller-supplied path or reaches an external system.
_PURE_READ = ToolAnnotations(  # type: ignore[call-arg]
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_MT_DESC = (
    "An E&I message type, e.g. 'camt.056.001.12' (see list_message_types)."
)


def list_message_types() -> dict[str, Any]:
    """List supported E&I message types."""
    return {"message_types": generator.list_message_types()}


def get_required_fields(
    message_type: Annotated[str, Field(description=_MT_DESC)],
) -> dict[str, Any]:
    """Return the required fields for a message type."""
    try:
        return {
            "message_type": message_type,
            "required_fields": generator.get_required_fields(message_type),
        }
    except ValueError as exc:
        return {"error": str(exc)}


def generate_message(
    message_type: Annotated[str, Field(description=_MT_DESC)],
    record: Annotated[
        dict[str, Any],
        Field(description="Message fields; see get_required_fields."),
    ],
) -> dict[str, Any]:
    """Generate a validated E&I XML message."""
    try:
        return {
            "message_type": message_type,
            "xml": generator.generate_message(message_type, record),
        }
    except ValueError as exc:
        return {"error": str(exc)}


def validate_xml(
    message_type: Annotated[str, Field(description=_MT_DESC)],
    xml: Annotated[str, Field(description="Raw ISO 20022 XML to validate.")],
) -> dict[str, Any]:
    """Validate XML against a message type's XSD."""
    try:
        return generator.validate_xml(message_type, xml)
    except ValueError as exc:
        return {"error": str(exc)}


def build_investigation_message(
    message_type: Annotated[str, Field(description=_MT_DESC)] = (
        "camt.056.001.12"
    ),
) -> str:
    """Guide the caller through building a validated E&I ``camt`` message."""
    return (
        f"Help me build a valid ISO 20022 Exceptions & Investigations "
        f"message of type {message_type}. Work through the tools in order:\n"
        f"1. Call list_message_types to confirm {message_type} is supported "
        f"(and to discover its human-readable name).\n"
        f"2. Call get_required_fields with message_type={message_type!r} to "
        f"learn which top-level fields the record must supply.\n"
        f"3. Call generate_message with message_type={message_type!r} and a "
        f"record populated with those required fields (for camt.056, include "
        f"a 'transactions' list with the original payment references and a "
        f"cancellation reason code). The output XML is validated against the "
        f"bundled XSD before it is returned.\n"
        f"4. Call validate_xml with message_type={message_type!r} and the "
        f"generated XML to double-check is_valid and surface any schema "
        f"errors.\n"
        f"Report the final XML and its validation result."
    )


def message_types_resource() -> str:
    """Expose the supported E&I message types as a JSON resource."""
    return json.dumps({"message_types": generator.list_message_types()})


def required_fields_resource(message_type: str) -> str:
    """Expose a message type's required fields as a JSON resource."""
    try:
        return json.dumps(
            {
                "message_type": message_type,
                "required_fields": generator.get_required_fields(message_type),
            }
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


# Tools, the prompt and the resources are registered here, in definition
# order, rather than with decorators on each function: mutmut 3 never
# mutates a decorated function, so the decorator form left every handler
# outside mutation testing. The registered object is the same function,
# docstring and signature, and clients list the tools in this order.
server.tool(
    annotations=_PURE_READ,
    description="""List supported ISO 20022 Exceptions & Investigations message types.

Purpose:
Returns the catalog of supported E&I message identifiers (e.g. camt.056.001.12 Payment Cancellation Request, camt.029.001.14 Resolution of Investigation) and their human-readable definitions.

When to use:
- When discovering valid message_type parameters before generating or validating messages.
- When verifying schema version support for payment recall or resolution workflows.

When NOT to use:
- Do NOT use for payment initiation (pain) or statement (camt.053) messages.

Behavioral transparency:
Static catalogue retrieval; pure, deterministic, and side-effect-free.""",
)(list_message_types)
server.tool(
    annotations=_PURE_READ,
    description="""Get required schema fields for an ISO 20022 E&I message type.

Purpose:
Returns the list of mandatory top-level data fields required to construct a valid message record (e.g. assignment identification, instruct team agent, and transaction arrays).

When to use:
- When preparing input payloads before calling generate_message.
- When validating payload completeness prior to XML serialization.

When NOT to use:
- Do NOT use with unsupported message types; discover supported types via list_message_types.

Behavioral transparency:
Deterministic field dictionary lookup; pure, read-only, and idempotent.""",
)(get_required_fields)
server.tool(
    annotations=_PURE_READ,
    description="""Generate a schema-validated ISO 20022 E&I XML message from a record.

Purpose:
Renders a complete, XSD-compliant ISO 20022 XML document (e.g. camt.056 payment cancellation or camt.029 investigation resolution) from structured field dictionaries, validating the result against the bundled official schema before returning.

When to use:
- When raising payment cancellation, recall, or investigation response messages for interbank transmission.
- When requiring guaranteed XSD-valid XML output for downstream payment processing.

When NOT to use:
- Do NOT use to validate pre-existing XML files without generating; use validate_xml instead.
- Do NOT pass incomplete records; check get_required_fields first.

Behavioral transparency:
Pure template rendering and in-memory schema validation; side-effect-free and idempotent.""",
)(generate_message)
server.tool(
    annotations=_PURE_READ,
    description="""Validate raw ISO 20022 E&I XML against bundled XSD schemas.

Purpose:
Validates an XML string against the official bundled XSD schema for the specified E&I message type, returning validation status and detailed schema violation diagnostics.

When to use:
- When inspecting received or pre-generated ISO 20022 E&I XML before ingesting or routing.
- When diagnosing schema structural, datatype, or constraint errors in message payloads.

When NOT to use:
- Do NOT use for payment initiation (pain) or statement (camt.053) documents.
- Do NOT pass unparseable binary content; requires valid XML text.

Behavioral transparency:
Pure, in-memory schema validation using local bundled XSDs; zero network access or side effects.""",
)(validate_xml)
server.prompt(
    title="Build an Exceptions & Investigations message",
)(build_investigation_message)
server.resource(
    "camt-exceptions://message-types",
    title="Supported E&I message types",
    description=(
        "The supported ISO 20022 Exceptions & Investigations message types "
        "and their names, as JSON."
    ),
    mime_type="application/json",
)(message_types_resource)
server.resource(
    "camt-exceptions://required-fields/{message_type}",
    title="Required fields for an E&I message type",
    description=(
        "The required top-level fields for a given E&I message type, as JSON."
    ),
    mime_type="application/json",
)(required_fields_resource)


def main(argv: list[str] | None = None) -> None:
    """Run the E&I MCP server (the ``camt-exceptions-mcp`` entry point).

    stdio by default; ``--transport streamable-http`` or ``--transport sse``
    listens on ``--host``/``--port`` instead. See :mod:`camt_exceptions._cli`.

    Args:
        argv: Command-line arguments; ``None`` reads ``sys.argv[1:]``.
    """
    _cli.serve(server, argv, "camt-exceptions-mcp", __version__)


if __name__ == "__main__":
    main()

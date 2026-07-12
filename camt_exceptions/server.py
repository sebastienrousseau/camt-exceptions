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

The server communicates over stdio (FastMCP's default transport).
"""

from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from camt_exceptions import __version__, generator

server = FastMCP("camt-exceptions")
# FastMCP does not expose a version kwarg; without this override the MCP SDK's
# own version leaks into serverInfo.version, breaking manifest/runtime
# coherence checks (e.g. Glama scoring).
server._mcp_server.version = __version__

# Every tool is a pure, side-effect-free reader: it computes solely from its
# arguments and the XSDs/templates bundled with this package. Nothing opens a
# caller-supplied path or reaches an external system.
_PURE_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_MT_DESC = (
    "An E&I message type, e.g. 'camt.056.001.12' (see list_message_types)."
)


@server.tool(
    annotations=_PURE_READ,
    description=(
        "List the supported ISO 20022 Exceptions & Investigations message "
        "types (e.g. camt.056 payment cancellation request) and their names."
    ),
)
def list_message_types() -> dict[str, Any]:
    """List supported E&I message types."""
    return {"message_types": generator.list_message_types()}


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Return the required top-level fields for an E&I message type."
    ),
)
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


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Generate a validated ISO 20022 E&I XML message from a record. For "
        "camt.056, the record cancels/recalls a previously sent payment "
        "(assignment ids + agent BICs + a list of 'transactions' with the "
        "original payment references and a cancellation reason code). Output "
        "is validated against the bundled XSD before it is returned."
    ),
)
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


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Validate raw ISO 20022 XML against an E&I message type's bundled XSD; "
        "returns is_valid plus any schema errors."
    ),
)
def validate_xml(
    message_type: Annotated[str, Field(description=_MT_DESC)],
    xml: Annotated[str, Field(description="Raw ISO 20022 XML to validate.")],
) -> dict[str, Any]:
    """Validate XML against a message type's XSD."""
    try:
        return generator.validate_xml(message_type, xml)
    except ValueError as exc:
        return {"error": str(exc)}


def main() -> None:
    """Run the E&I MCP server over stdio (the ``camt-exceptions-mcp`` entry)."""
    server.run()


if __name__ == "__main__":
    main()

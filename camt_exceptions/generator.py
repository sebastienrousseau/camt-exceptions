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

"""Generate and validate ISO 20022 Exceptions & Investigations (E&I) messages.

This is the ``camt`` counterpart to the generation engines elsewhere in the
suite: each supported message type bundles its official XSD plus a Jinja2
``template.xml``; :func:`generate_message` renders a record into XML and
:func:`validate_xml` checks any XML against the bundled schema.

Currently supported:

* ``camt.056.001.12`` -- FI to FI Payment Cancellation Request (recall or
  cancel a previously sent payment, e.g. a duplicate or erroneous transfer).

Additional E&I messages (camt.029 resolution of investigation, camt.026 unable
to apply, camt.027 claim non-receipt, camt.087 request to modify) plug in by
dropping their XSD + ``template.xml`` alongside and registering them in
:data:`MESSAGE_TYPES`.
"""

from __future__ import annotations

import functools
from importlib.resources import files
from typing import Any

import jinja2
import xmlschema


class MessageSpec:
    """Static description of one supported E&I message type."""

    def __init__(
        self,
        message_type: str,
        name: str,
        required: tuple[str, ...],
    ) -> None:
        self.message_type = message_type
        self.name = name
        self.required = required


# Registry of supported message types. Adding a message = bundle its
# templates/<mt>/<mt>.xsd + template.xml and add a MessageSpec here.
MESSAGE_TYPES: dict[str, MessageSpec] = {
    "camt.056.001.12": MessageSpec(
        message_type="camt.056.001.12",
        name="FI to FI Payment Cancellation Request",
        required=(
            "assignment_id",
            "assigner_agent_bic",
            "assignee_agent_bic",
            "creation_date_time",
        ),
    ),
}


def list_message_types() -> list[dict[str, str]]:
    """Return every supported E&I message type and its human name."""
    return [
        {"message_type": s.message_type, "name": s.name}
        for s in MESSAGE_TYPES.values()
    ]


def _spec(message_type: str) -> MessageSpec:
    """Return the spec for a message type or raise a helpful ValueError."""
    spec = MESSAGE_TYPES.get(message_type)
    if spec is None:
        known = ", ".join(sorted(MESSAGE_TYPES))
        raise ValueError(
            f"unsupported message type {message_type!r}; supported: {known}"
        )
    return spec


def get_required_fields(message_type: str) -> list[str]:
    """Return the required top-level fields for a message type."""
    return list(_spec(message_type).required)


def _template_text(message_type: str) -> str:
    """Read the bundled Jinja template for a message type."""
    base = files("camt_exceptions") / "templates" / message_type
    return (base / "template.xml").read_text(encoding="utf-8")


@functools.cache
def _schema(message_type: str) -> xmlschema.XMLSchema:
    """Load (and cache) the bundled XSD for a message type."""
    base = files("camt_exceptions") / "templates" / message_type
    xsd = base / f"{message_type}.xsd"
    return xmlschema.XMLSchema(str(xsd))


@functools.cache
def _template(message_type: str) -> jinja2.Template:
    """Compile (and cache) the Jinja template for a message type."""
    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=True,
    )
    return env.from_string(_template_text(message_type))


def generate_message(message_type: str, record: dict[str, Any]) -> str:
    """Render a validated E&I message to XML.

    Args:
        message_type: e.g. ``"camt.056.001.12"``.
        record: the message fields (see :func:`get_required_fields` for the
            required keys; ``transactions`` is a list of per-transaction dicts).

    Returns:
        The rendered ISO 20022 XML as a string.

    Raises:
        ValueError: unknown message type, a missing required field, or output
            that fails XSD validation.
    """
    spec = _spec(message_type)
    missing = [f for f in spec.required if not record.get(f)]
    if missing:
        raise ValueError(
            f"{message_type} is missing required field(s): "
            f"{', '.join(missing)}"
        )
    xml = _template(message_type).render(**record)
    errors = list(_schema(message_type).iter_errors(xml))
    if errors:
        first = str(errors[0]).splitlines()[0]
        raise ValueError(
            f"generated {message_type} failed XSD validation: {first}"
        )
    return xml


def validate_xml(message_type: str, xml: str) -> dict[str, Any]:
    """Validate raw XML against a message type's bundled XSD.

    Returns:
        ``{"message_type": ..., "is_valid": bool, "errors": [...]}`` -- never
        raises on a validation failure (only on an unknown message type).
    """
    _spec(message_type)
    errors = [
        str(e).splitlines()[0] for e in _schema(message_type).iter_errors(xml)
    ]
    return {
        "message_type": message_type,
        "is_valid": not errors,
        "errors": errors,
    }

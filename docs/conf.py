"""Sphinx configuration for camt-exceptions documentation."""

from __future__ import annotations

import importlib.metadata

project = "camt-exceptions"
author = "Sebastien Rousseau"
copyright = "2023-2026, Sebastien Rousseau"

try:
    release = importlib.metadata.version("camt-exceptions")
except importlib.metadata.PackageNotFoundError:
    release = "0.0.0+dev"
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "myst_parser",
]

# MyST options: enable Markdown directives without breaking standard
# CommonMark renders.
myst_enable_extensions = ["colon_fence", "deflist", "linkify"]
# Resolve the README's in-page links (#the-suite, ...) to headings.
myst_heading_anchors = 3

# Allow myst_parser to ingest the top-level README.md.
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Furo theme: lightweight, modern, mobile-friendly.
html_theme = "furo"
html_title = f"camt-exceptions {release}"

# Cross-link to the Python stdlib.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# ``pydantic.Field`` is imported into the server module for the
# parameter annotations; it is not part of this package's API, and its
# own annotations use forward references the type-hint extension cannot
# resolve from here.
suppress_warnings = ["sphinx_autodoc_typehints.forward_reference"]

# Autodoc defaults.
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

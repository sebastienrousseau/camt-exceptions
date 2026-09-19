<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Releasing camt-exceptions

This document defines **what merits a release** and **how to cut one**,
so versions are deliberate rather than ad-hoc.

## Versioning scheme

camt-exceptions ships on its own version line. **Versions increment by
0.0.1**; `0.1.0` follows `0.0.999`. There is no sibling package to keep
in lockstep. The scheduled `Release Consistency` workflow
(`scripts/check_suite_consistency.py`) fails when the tree and PyPI
disagree - a version bumped in the tree and never tagged breaks nothing
until somebody looks, which is how `0.0.16` sat unpublished for weeks
with a security floor nobody received.

## What merits a release

Cut a new version when there is user-visible change to ship - bug fixes,
security or dependency patches, new message types, tools, resources or
prompts, or documentation that ships in the package.

Do **not** cut a release that contains only a version-number bump with
no functional, security, or documentation change.

## Pre-flight checklist

A release is ready only when **all** of the following hold on `main`:

1. The gate is green: `pytest` (100% line+branch coverage),
   `ruff check`, `black --check`, `mypy camt_exceptions/`, both
   examples and `python benches/bench_investigations.py --quick`.
2. Every Dependabot / CodeQL / Scorecard alert is resolved or has a
   documented, expiring suppression.
3. `CHANGELOG.md` has a dated section for the new version describing the
   change set.
4. The version is identical in `pyproject.toml`,
   `camt_exceptions/__init__.py`, `CHANGELOG.md`, `glama.json` and
   `server.json` (enforced by `scripts/verify_versions.py`, which the
   `Version sources agree` workflow runs). The Glama directory and the
   MCP registry read those two manifests; a release that forgets them
   shows an old version to every agent that browses for the server.
5. `SECURITY.md`'s supported-versions table names the new version.

## Cutting the release

1. Bump the version in `pyproject.toml`, `camt_exceptions/__init__.py`,
   `glama.json` and `server.json`, and add the `CHANGELOG.md` section,
   in a single PR.
2. Merge the PR to `main` once CI is green.
3. Push a signed tag:

   ```bash
   git tag -s vX.Y.Z -m "camt-exceptions vX.Y.Z" <merge-commit>
   git push origin vX.Y.Z
   ```

4. The tag triggers two workflows:
   - `release.yml` builds the distributions, runs `twine check`,
     attaches a SLSA build provenance attestation, publishes to PyPI via
     OIDC trusted publishing, signs every distribution keylessly with
     cosign, creates the GitHub release with generated notes, and
     attaches CycloneDX and SPDX SBOMs plus a licence manifest.
   - `publish-mcp.yml` stamps `server.json` from the tag, waits for
     PyPI to surface the version, and publishes to the MCP registry.

## After releasing

- Confirm the version is live on
  [PyPI](https://pypi.org/project/camt-exceptions/) and the GitHub
  release is published (not draft).
- Verify a clean install: `pip install camt-exceptions==X.Y.Z` and
  `camt-exceptions-mcp --version`.
- Confirm the MCP registry and Glama show the new version.

## CI integrations

- **PyPI trusted publisher** (`release.yml`): configured at
  <https://pypi.org/manage/account/publishing/>. The publisher claim
  set is `repo:sebastienrousseau/camt-exceptions:environment:pypi` with
  `workflow_ref` pointing at `.github/workflows/release.yml`.
- **MCP registry** (`publish-mcp.yml`): authenticates with the
  workflow's GitHub OIDC token; no secret to configure.

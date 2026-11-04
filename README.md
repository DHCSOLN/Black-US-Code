# Black US Code — SOLN Legal Intelligence MCP development starter

Canonical supplied requirements: [PRD.md](PRD.md). The accompanying PRD.yml is a pointer; preserve the repository's existing PRD.yml if it differs.

This package is **not** a complete MCP server, deployed website, or production legal screening system.

Current Python foundation: `server/core.py` (SQLite registry, manual flags, decisions, search).
Initial document identifiers and source URLs: `registry/initial_inventory.json` (inventory only; no documents downloaded).
Open work and implementation audit: [IMPLEMENTATION_GAPS.md](IMPLEMENTATION_GAPS.md).

Run tests with `python -m unittest discover -s tests -v`.

Important: approval logic is a local prototype with reviewer-name input, **not authenticated authorization**. Do not expose administrative functions publicly.

# PRD 1.0 implementation audit — 2026-11-04

## Existing working foundation
- Local SQLite US/SOLN instrument registry with basic search and source URLs.
- Entity registry with count against target of 196; **no verified entity list loaded**.
- Manual concern flags, pending queue, human-named review decisions.
- Basic unit tests and GitHub CI.

## Not implemented — do not represent as operational
- Official SOLN source ingestion, original binary archiving, PDF/DOCX/HTML parsing, hashes of originals, duplicate detection, document versions and amendment histories.
- US Code source connectors, point-in-time law, state law, cross-references and classification hierarchy.
- Automatic discrimination screening with evidence, contextual review, and 196-entity coverage.
- Authenticated reviewer identities, role-based approvals, tamper-evident/immutable audit logs.
- The 12 specified MCP tools, a live MCP server, Ashley client integration.
- Semantic search, legal explanations with passage citations, citation verification, amendment comparison.
- Website monitoring and review of source changes.
- Public portal, downloads and Ashley interface.
- AWS infrastructure, deployment approval gates, production security tests.

## Critical design and safety requirements
- Original legal instruments remain separate; US and SOLN sources have distinct legal status.
- No automatic adoption of flagged provisions. Decisions require authenticated authorization in production.
- Declining SOLN adoption does not change applicable US law.
- Read-only research module; no transfers, payments, judicial acts or binding legal determinations.
- No claims of legal recognition, source completeness or deployment without independent evidence.

## Before uploading
- Review existing GitHub PRD.yml before replacing it: the supplied PRD text is Markdown, so this package keeps it in PRD.md and uses PRD.yml only as a pointer. Do not overwrite an existing canonical PRD.yml blindly.
- Review README and CI. The package is a **development starter**, not production-ready.
- Target repository: `DHCSOLN/Black-US-Code` (confirmed by project owner).

# Black US Code — SOLN Legal Intelligence MCP Server

Repository: `DHCSOLN/Black-US-Code` · Ashley Executive Assistant integration target.

## Run now

```bash
python -m unittest discover -s tests -v
python -m server.mcp
python -m server.http
```

- MCP stdio server: `python -m server.mcp` (15 read-only research tools, protocol 2024-11-05).
- Public read-only portal: `http://127.0.0.1:8080/`.
- Ingest an approved local source:

```bash
python -m server.ingest --file path/to/source.pdf --id SOLN17 --framework SOLN --category constitution --title "SOLN 17" --citation "SOLN 17" --url "https://stateoflocnation.com/..." --status "SOLN-published"
```

PDF and DOCX ingestion requires `pip install -r requirements-ingest.txt`.
The site is **empty until actual approved source documents are ingested**. The inventory contains only titles and URLs, not legal text. A missing record is not evidence a law does not exist.

## Implemented
- Persistent SQLite source registry, independent US/SOLN records, source text and passage preservation, file checksum and original byte archive, version history and pending change queue.
- Keyword search, original-source excerpts, citation lookup against local archive, text comparison, manually initiated review flags, entity registry, and append-only event log protected by SQLite triggers.
- 15 MCP stdio research tools, local read-only HTTP portal, Docker image, CI tests, manual AWS deployment workflow that **fails closed**.

## Production blockers
- Official legal corpus not retrieved or verified; 196-entity registry not supplied; no independent legal authority or adoption verification.
- No automated discrimination classifier or semantic search; flags are entered manually.
- Review CLI/API requires authenticated identity and roles before real administration; local review is a prototype.
- Audit event chain needs off-database WORM backups and key management for true tamper resistance.
- Official-source website change polling, complete external US law integration, substantive cross-reference graph, public Ashley AI chat, and AWS resources are not configured.
- HTTP API is read-only; **do not expose it directly on the internet without TLS, ingress authentication/rate limits and security review**.
- AWS workflow is intentionally blocked until administrator-approved infrastructure and production checks are implemented.

## Legal and financial boundaries
SOLN and U.S. instruments are preserved as distinct records. Inclusion in this library is not evidence of enactment or legal force under U.S. law. The platform does not make binding legal determinations or execute financial transactions.

Full requirements: `PRD.yml` and `PRD.md`. Implementation status: `IMPLEMENTATION_GAPS.md`.

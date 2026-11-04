
"""Explicitly authorized document ingestion; never silently publishes updates."""
import argparse, urllib.request, urllib.parse, io, re, html
from pathlib import Path
from .engine import Engine

def extract(raw,fmt):
    fmt=fmt.lower()
    if fmt in ("txt","md"):return raw.decode("utf-8")
    if fmt in ("html","htm"):
        s=raw.decode("utf-8",errors="replace")
        s=re.sub(r"(?is)<(script|style).*?</\1>","",s)
        return html.unescape(re.sub(r"<[^>]+>"," ",s))
    if fmt=="pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:raise RuntimeError("Install requirements-ingest.txt") from exc
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
    if fmt=="docx":
        try:
            from docx import Document
        except ImportError as exc:raise RuntimeError("Install requirements-ingest.txt") from exc
        return "\n".join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
    raise ValueError("Unsupported format")

def ingest_file(engine,filename,*,id,framework,category,title,citation,url,status):
    p=Path(filename);raw=p.read_bytes()
    text=extract(raw,p.suffix.lstrip("."))
    if not text.strip():raise ValueError("No extractable text: manual review required")
    return engine.ingest(id=id,framework=framework,category=category,title=title,citation=citation,
                         text=text,url=url,status=status,original_bytes=raw)

def main():
    p=argparse.ArgumentParser()
    for x in ("file","id","framework","category","title","citation","url","status"):p.add_argument("--"+x,required=True)
    p.add_argument("--db",default="data/soln.sqlite")
    args=p.parse_args()
    print(ingest_file(Engine(args.db),args.file,id=args.id,framework=args.framework,category=args.category,
                      title=args.title,citation=args.citation,url=args.url,status=args.status))
if __name__=="__main__":main()


"""Source-grounded SOLN research engine. No legal or financial execution."""
import hashlib, json, re, sqlite3, difflib, datetime
from pathlib import Path
from .core import connect, add_instrument, search, entity_coverage

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dicts(cursor): return [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]

class Engine:
    def __init__(self, path=":memory:", archive="data/originals"):
        self.db=connect(path)
        self.archive=Path(archive)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS documents(
          id TEXT NOT NULL, version INTEGER NOT NULL, framework TEXT NOT NULL CHECK(framework IN ('US','SOLN')),
          category TEXT NOT NULL, title TEXT NOT NULL, citation TEXT NOT NULL,
          text TEXT NOT NULL, url TEXT NOT NULL, sha256 TEXT NOT NULL,
          status TEXT NOT NULL, fetched_at TEXT NOT NULL, effective_date TEXT,
          title_no TEXT, chapter_no TEXT, section_no TEXT, original_path TEXT,
          PRIMARY KEY(id,version));
        CREATE TABLE IF NOT EXISTS passages(
          document_id TEXT NOT NULL, version INTEGER NOT NULL, passage_no INTEGER NOT NULL,
          heading TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(document_id,version,passage_no));
        CREATE TABLE IF NOT EXISTS changes(
          id INTEGER PRIMARY KEY, document_id TEXT NOT NULL, old_version INTEGER,
          new_version INTEGER, status TEXT NOT NULL DEFAULT 'pending',
          detected_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS review_events(
          id INTEGER PRIMARY KEY, flag_id INTEGER NOT NULL, decision TEXT NOT NULL,
          actor TEXT NOT NULL, at TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_review_update BEFORE UPDATE ON review_events BEGIN SELECT RAISE(ABORT,'immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_review_delete BEFORE DELETE ON review_events BEGIN SELECT RAISE(ABORT,'immutable'); END;
        """)
    def ingest(self, *, id, framework, category, title, citation, text, url, status,
               effective_date=None, title_no=None, chapter_no=None, section_no=None, original_bytes=None):
        if framework not in ('US','SOLN'): raise ValueError("Invalid framework")
        if not all([id,category,title,citation,text,url,status]): raise ValueError("Required fields missing")
        digest=hashlib.sha256(original_bytes if original_bytes is not None else text.encode()).hexdigest()
        prev=self.db.execute("SELECT version,sha256 FROM documents WHERE id=? ORDER BY version DESC LIMIT 1",(id,)).fetchone()
        if prev and prev[1]==digest: return {"id":id,"version":prev[0],"unchanged":True}
        version=(prev[0]+1) if prev else 1
        original_path=None
        if original_bytes is not None:
            self.archive.mkdir(parents=True,exist_ok=True)
            target=self.archive/(digest+".bin")
            if not target.exists(): target.write_bytes(original_bytes)
            original_path=str(target)
        with self.db:
            self.db.execute("""INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (id,version,framework,category,title,citation,text,url,digest,status,now(),effective_date,title_no,chapter_no,section_no,original_path))
            for n,(heading,body) in enumerate(split_passages(text),1):
                self.db.execute("INSERT INTO passages VALUES (?,?,?,?,?)",(id,version,n,heading,body))
            if prev: self.db.execute("INSERT INTO changes(document_id,old_version,new_version,status,detected_at) VALUES (?,?,?,'pending',?)",(id,prev[0],version,now()))
        return {"id":id,"version":version,"unchanged":False,"sha256":digest,"change_pending":bool(prev)}
    def get(self,id,version=None):
        sql="SELECT * FROM documents WHERE id=?"
        args=[id]
        if version is not None: sql+=" AND version=?";args.append(version)
        sql+=" ORDER BY version DESC LIMIT 1"
        rows=dicts(self.db.execute(sql,args))
        if not rows: return {"error":"NOT_FOUND","id":id}
        d=rows[0]
        d["passages"]=dicts(self.db.execute("SELECT passage_no,heading,body FROM passages WHERE document_id=? AND version=? ORDER BY passage_no",(id,d["version"])))
        return d
    def search(self,q,framework=None,category=None):
        if not q or not q.strip(): return []
        sql="""SELECT d.id,d.version,d.framework,d.category,d.title,d.citation,d.url,d.status,
                substr(d.text,1,400) AS excerpt
                FROM documents d WHERE d.version=(SELECT MAX(version) FROM documents WHERE id=d.id)
                AND (d.title LIKE ? OR d.citation LIKE ? OR d.text LIKE ?)"""
        args=["%"+q+"%"]*3
        if framework: sql+=" AND d.framework=?";args.append(framework)
        if category: sql+=" AND d.category=?";args.append(category)
        return dicts(self.db.execute(sql+" ORDER BY d.id LIMIT 100",args))
    def verify(self,citation):
        rows=dicts(self.db.execute("SELECT id,version,title,citation,url,status FROM documents WHERE citation=? ORDER BY version DESC",(citation,)))
        return {"verified_in_local_archive":bool(rows),"records":rows,"independent_official_verification":False}
    def compare(self,a,b,version_a=None,version_b=None):
        x,y=self.get(a,version_a),self.get(b,version_b)
        if "error" in x or "error" in y:return {"error":"NOT_FOUND"}
        return {"left":{"id":a,"version":x["version"]},"right":{"id":b,"version":y["version"]},
                "diff":list(difflib.unified_diff(x["text"].splitlines(),y["text"].splitlines(),fromfile=a,tofile=b,lineterm=""))}
    def history(self,id):
        return dicts(self.db.execute("SELECT id,version,title,citation,url,sha256,status,fetched_at FROM documents WHERE id=? ORDER BY version",(id,)))
    def explain(self,query,framework="SOLN"):
        results=self.search(query,framework=framework)
        return {"question":query,"source_passages":[{"id":r["id"],"citation":r["citation"],"url":r["url"],
          "passages":[{"passage_no":p["passage_no"],"text":p["body"][:700]} for p in self.get(r["id"])["passages"][:4]]} for r in results[:8]],
          "notice":"Source excerpts only; no invented legal conclusions or independent legal-status verification."}
    def flag_review(self,document_id,version,entity_id,concern,evidence):
        if not concern.strip() or not evidence.strip(): raise ValueError("Concern and evidence required")
        d=self.get(document_id,version)
        if "error" in d:raise ValueError("Unknown document")
        if entity_id and not self.db.execute("SELECT 1 FROM entities WHERE id=?",(entity_id,)).fetchone():raise ValueError("Unknown entity")
        with self.db:
            # legacy flags schema points to instruments: keep source record separate, register immutable source snapshot
            if not self.db.execute("SELECT 1 FROM instruments WHERE id=?",(document_id,)).fetchone():
                add_instrument(self.db,id=document_id,framework=d["framework"],title=d["title"],citation=d["citation"],text=d["text"],source_url=d["url"],legal_status=d["status"])
            cur=self.db.execute("INSERT INTO flags(instrument_id,entity_id,concern,evidence) VALUES (?,?,?,?)",(document_id,entity_id,concern,evidence))
        return {"flag_id":cur.lastrowid,"status":"pending"}
    def review(self,flag_id,decision,actor):
        if decision not in ("approved","declined","further_review") or not actor.strip():raise ValueError("Explicit review required")
        with self.db:
            row=self.db.execute("SELECT status FROM flags WHERE id=?",(flag_id,)).fetchone()
            if not row or row[0]!="pending":raise ValueError("Not pending")
            prev=self.db.execute("SELECT event_hash FROM review_events ORDER BY id DESC LIMIT 1").fetchone()
            prev_hash=prev[0] if prev else "GENESIS"
            stamp=now()
            digest=hashlib.sha256(json.dumps([flag_id,decision,actor,stamp,prev_hash]).encode()).hexdigest()
            self.db.execute("UPDATE flags SET status=?,reviewer=?,reviewed_at=? WHERE id=?",(decision,actor,stamp,flag_id))
            self.db.execute("INSERT INTO review_events(flag_id,decision,actor,at,prev_hash,event_hash) VALUES (?,?,?,?,?,?)",(flag_id,decision,actor,stamp,prev_hash,digest))
        return {"flag_id":flag_id,"decision":decision,"event_hash":digest}
    def review_queue(self):
        return dicts(self.db.execute("""SELECT f.id AS flag_id,f.instrument_id,i.citation,f.entity_id,f.concern,f.evidence,f.status
                                        FROM flags f JOIN instruments i ON f.instrument_id=i.id WHERE f.status='pending' ORDER BY f.id"""))
    def status(self):
        return {"documents":self.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
                "entity_coverage":entity_coverage(self.db),"pending_reviews":len(self.review_queue()),
                "production_ready":False}

def split_passages(text):
    chunks=re.split(r"\n\s*\n",text)
    return [(c.splitlines()[0][:160],c) for c in chunks if c.strip()] or [("Full text",text)]

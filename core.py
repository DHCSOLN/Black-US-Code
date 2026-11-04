"""SOLN legal registry MVP: local-only, no automatic legal determinations."""
import json, sqlite3, hashlib, datetime
from pathlib import Path

SCHEMA='''CREATE TABLE IF NOT EXISTS instruments(id TEXT PRIMARY KEY, framework TEXT NOT NULL CHECK(framework IN ('US','SOLN')), title TEXT NOT NULL, citation TEXT NOT NULL, text TEXT NOT NULL, source_url TEXT NOT NULL, legal_status TEXT NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS flags(id INTEGER PRIMARY KEY AUTOINCREMENT, instrument_id TEXT NOT NULL REFERENCES instruments(id), entity_id TEXT REFERENCES entities(id), concern TEXT NOT NULL, evidence TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','declined','further_review')), reviewer TEXT, reviewed_at TEXT);
CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY AUTOINCREMENT, flag_id INTEGER NOT NULL REFERENCES flags(id), decision TEXT NOT NULL, reviewer TEXT NOT NULL, recorded_at TEXT NOT NULL);'''
def connect(path=':memory:'):
    db=sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(SCHEMA)
    return db

def add_instrument(db, *, id, framework, title, citation, text, source_url, legal_status):
    if not all([id,framework,title,citation,text,source_url,legal_status]): raise ValueError('All source fields required')
    if framework not in ('US','SOLN'): raise ValueError('Invalid framework')
    digest=hashlib.sha256(text.encode()).hexdigest()
    with db: db.execute('INSERT INTO instruments VALUES (?,?,?,?,?,?,?,?,?)',(id,framework,title,citation,text,source_url,legal_status,digest,datetime.datetime.now(datetime.timezone.utc).isoformat()))
    return digest

def search(db, query, framework=None):
    if not query.strip(): return []
    sql='SELECT id,framework,title,citation,source_url,legal_status FROM instruments WHERE (title LIKE ? OR citation LIKE ? OR text LIKE ?)'
    args=['%'+query+'%']*3
    if framework:
        if framework not in ('US','SOLN'): raise ValueError('Invalid framework')
        sql+=' AND framework=?';args.append(framework)
    return [dict(zip(['id','framework','title','citation','source_url','legal_status'],row)) for row in db.execute(sql+' ORDER BY id LIMIT 100',args)]

def add_entity(db,id,name):
    with db: db.execute('INSERT INTO entities VALUES (?,?)',(id,name))

def flag(db,instrument_id,concern,evidence,entity_id=None):
    if not concern.strip() or not evidence.strip(): raise ValueError('Evidence and concern required')
    with db:
        cur=db.execute('INSERT INTO flags(instrument_id,entity_id,concern,evidence) VALUES (?,?,?,?)',(instrument_id,entity_id,concern,evidence))
    return cur.lastrowid

def decide(db,flag_id,decision,reviewer):
    if decision not in ('approved','declined','further_review') or not reviewer.strip(): raise ValueError('Explicit human review required')
    with db:
        row=db.execute('SELECT status FROM flags WHERE id=?',(flag_id,)).fetchone()
        if not row or row[0]!='pending': raise ValueError('Flag absent or already decided')
        now=datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute('UPDATE flags SET status=?,reviewer=?,reviewed_at=? WHERE id=?',(decision,reviewer,now,flag_id))
        db.execute('INSERT INTO decisions(flag_id,decision,reviewer,recorded_at) VALUES (?,?,?,?)',(flag_id,decision,reviewer,now))

def screening_queue(db):
    return [dict(zip(['flag_id','instrument_id','citation','entity_id','concern','evidence','status'],r)) for r in db.execute('SELECT f.id,f.instrument_id,i.citation,f.entity_id,f.concern,f.evidence,f.status FROM flags f JOIN instruments i ON i.id=f.instrument_id WHERE f.status="pending" ORDER BY f.id')]

def entity_coverage(db):
    count=db.execute('SELECT COUNT(*) FROM entities').fetchone()[0]
    return {'registered':count,'target':196,'complete':count==196}

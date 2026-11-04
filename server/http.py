
"""Read-only HTTP API and public static portal. Bind to localhost by default."""
import json, os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from pathlib import Path
from .engine import Engine
from .mcp import dispatch,TOOLS

class Handler(BaseHTTPRequestHandler):
    engine=None
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path=="/":
            data=(Path(__file__).parents[1]/"web"/"index.html").read_bytes()
            self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data);return
        if parsed.path=="/health":return self.respond({"status":"ok","read_only":True})
        if parsed.path=="/api/tools":return self.respond({"tools":list(TOOLS)})
        if parsed.path.startswith("/api/"):
            name=parsed.path.split("/")[-1]
            if name not in TOOLS or name=="get_review_queue":return self.respond({"error":"NOT_FOUND"},404)
            args={k:v[0] for k,v in parse_qs(parsed.query).items()}
            try:return self.respond(dispatch(self.engine,name,args))
            except (ValueError,KeyError) as exc:return self.respond({"error":str(exc)},400)
        self.respond({"error":"NOT_FOUND"},404)
    def do_POST(self):self.respond({"error":"READ_ONLY"},405)
    def respond(self,obj,code=200):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
def main():
    host=os.getenv("SOLN_HTTP_HOST","127.0.0.1")
    if host not in ("127.0.0.1","localhost","::1") and not os.getenv("SOLN_ALLOW_PUBLIC_READONLY"):
        raise SystemExit("Remote bind requires explicit SOLN_ALLOW_PUBLIC_READONLY=1 and upstream TLS/rate-limits")
    Handler.engine=Engine(os.getenv("SOLN_DB","data/soln.sqlite"))
    ThreadingHTTPServer((host,int(os.getenv("PORT","8080"))),Handler).serve_forever()
if __name__=="__main__":main()

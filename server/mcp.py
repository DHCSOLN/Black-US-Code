
"""MCP JSON-RPC 2.0 over stdio, protocol version 2024-11-05."""
import json, sys, traceback
from .engine import Engine
TOOLS = {
"search_soln_law": ["query"],
"get_soln_constitution": [],
"get_soln_law": ["id"],
"get_soln_executive_order": ["number"],
"explain_majority_protection": ["query"],
"compare_soln_instruments": ["left","right"],
"verify_soln_citation": ["citation"],
"trace_legal_authority": ["query"],
"search_restitution_framework": ["query"],
"get_amendment_history": ["id"],
"check_source_updates": [],
"generate_legal_explanation": ["query"],
"search_us_law": ["query"],
"get_review_queue": [],
"get_registry_status": [],
}
def dispatch(engine,name,a):
    if name=="search_soln_law": return engine.search(a["query"],"SOLN")
    if name=="get_soln_constitution": return engine.search("SOLN 17","SOLN")
    if name=="get_soln_law": return engine.get(a["id"])
    if name=="get_soln_executive_order": return engine.search(a["number"],"SOLN","executive_order")
    if name=="explain_majority_protection": return engine.explain(a.get("query","majority protection"))
    if name=="compare_soln_instruments": return engine.compare(a["left"],a["right"],a.get("version_left"),a.get("version_right"))
    if name=="verify_soln_citation": return engine.verify(a["citation"])
    if name=="trace_legal_authority": return {"matches":engine.search(a["query"]),"note":"Cross-reference graph not yet populated"}
    if name=="search_restitution_framework": return engine.search(a.get("query","restitution"),"SOLN")
    if name=="get_amendment_history": return engine.history(a["id"])
    if name=="check_source_updates": return {"pending":engine.db.execute("SELECT COUNT(*) FROM changes WHERE status='pending'").fetchone()[0],"note":"Live website polling not configured"}
    if name=="generate_legal_explanation": return engine.explain(a["query"])
    if name=="search_us_law": return engine.search(a["query"],"US")
    if name=="get_review_queue": return engine.review_queue()
    if name=="get_registry_status": return engine.status()
    raise ValueError("Unknown tool")
def handle(engine,req):
    method=req.get("method","")
    ident=req.get("id")
    if method=="notifications/initialized":return None
    if method=="initialize":
        return {"jsonrpc":"2.0","id":ident,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"black-us-code","version":"0.2.0"}}}
    if method=="ping":return {"jsonrpc":"2.0","id":ident,"result":{}}
    if method=="tools/list":
        return {"jsonrpc":"2.0","id":ident,"result":{"tools":[{"name":name,"description":"Read-only source-grounded legal research: "+name,"inputSchema":{"type":"object","properties":{p:{"type":"string"} for p in params},"required":params,"additionalProperties":False}} for name,params in TOOLS.items()]}}
    if method=="tools/call":
        try:
            a=req.get("params",{})
            name=a.get("name")
            if name not in TOOLS:raise ValueError("Unknown tool")
            args=a.get("arguments",{})
            for required in TOOLS[name]:
                if required not in args:raise ValueError("Missing argument "+required)
            result=dispatch(engine,name,args)
            return {"jsonrpc":"2.0","id":ident,"result":{"content":[{"type":"text","text":json.dumps(result,ensure_ascii=False)}]}}
        except (ValueError,KeyError) as exc:
            return {"jsonrpc":"2.0","id":ident,"result":{"isError":True,"content":[{"type":"text","text":str(exc)}]}}
    return {"jsonrpc":"2.0","id":ident,"error":{"code":-32601,"message":"Method not found"}}
def main():
    import os
    engine=Engine(os.getenv("SOLN_DB","data/soln.sqlite"),os.getenv("SOLN_ARCHIVE","data/originals"))
    for line in sys.stdin:
        try:
            req=json.loads(line)
            result=handle(engine,req)
            if result is not None:print(json.dumps(result),flush=True)
        except Exception as exc:
            print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":str(exc)}}),flush=True)
if __name__=="__main__":main()

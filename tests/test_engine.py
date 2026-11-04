
import unittest, tempfile
from server.engine import Engine
from server.mcp import handle, TOOLS
class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.e=Engine(":memory:",self.tmp.name)
        self.e.ingest(id="SOLN17",framework="SOLN",category="constitution",title="SOLN 17",
                      citation="SOLN 17",text="Article 1. Majority protection.",url="https://example.org/soln17",status="SOLN-published")
    def tearDown(self):self.tmp.cleanup()
    def test_version_preserved(self):
        self.e.ingest(id="SOLN17",framework="SOLN",category="constitution",title="SOLN 17",
                      citation="SOLN 17",text="Article 2. Revised.",url="https://example.org/soln17",status="SOLN-published")
        self.assertEqual(len(self.e.history("SOLN17")),2)
        self.assertEqual(self.e.get("SOLN17",1)["text"],"Article 1. Majority protection.")
        self.assertEqual(self.e.get("SOLN17",2)["text"],"Article 2. Revised.")
    def test_duplicate_dedup(self):
        d=self.e.get("SOLN17")
        self.assertTrue(self.e.ingest(id="SOLN17",framework="SOLN",category="constitution",title="SOLN 17",
                      citation="SOLN 17",text=d["text"],url=d["url"],status=d["status"])["unchanged"])
    def test_manual_review_and_immutable_log(self):
        f=self.e.flag_review("SOLN17",1,None,"Possible exclusion","Article 1 wording")["flag_id"]
        self.assertEqual(self.e.review_queue()[0]["flag_id"],f)
        self.e.review(f,"declined","administrator")
        self.assertEqual(self.e.review_queue(),[])
        with self.assertRaises(Exception):self.e.db.execute("DELETE FROM review_events")
    def test_mcp(self):
        init=handle(self.e,{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        self.assertEqual(init["result"]["serverInfo"]["name"],"black-us-code")
        self.assertGreaterEqual(len(TOOLS),12)
        r=handle(self.e,{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_soln_law","arguments":{"query":"majority"}}})
        self.assertIn("SOLN17",r["result"]["content"][0]["text"])
    def test_no_entity_claim(self):
        self.assertFalse(self.e.status()["entity_coverage"]["complete"])
    def test_legal_status(self):
        self.assertFalse(self.e.verify("SOLN 17")["independent_official_verification"])
if __name__=="__main__":unittest.main()

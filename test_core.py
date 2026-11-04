import unittest
from server.core import connect,add_instrument,search,add_entity,flag,decide,screening_queue,entity_coverage
class RegistryTests(unittest.TestCase):
 def setUp(self):
  self.db=connect();add_instrument(self.db,id='us-1',framework='US',title='Example provision',citation='Example § 1',text='Illustrative text only',source_url='https://example.org',legal_status='example')
 def test_search(self): self.assertEqual(search(self.db,'Example')[0]['id'],'us-1')
 def test_queue_approval(self):
  add_entity(self.db,'e1','Example entity');fid=flag(self.db,'us-1','Potential unequal impact','Review required','e1');self.assertEqual(len(screening_queue(self.db)),1);decide(self.db,fid,'further_review','Human reviewer');self.assertEqual(screening_queue(self.db),[])
 def test_no_automatic_approval(self):
  fid=flag(self.db,'us-1','Concern','Evidence');self.assertEqual(screening_queue(self.db)[0]['status'],'pending')
  with self.assertRaises(ValueError): decide(self.db,fid,'approved','')
 def test_coverage(self): self.assertFalse(entity_coverage(self.db)['complete'])
if __name__=='__main__': unittest.main()

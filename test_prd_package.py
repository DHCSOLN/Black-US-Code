import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PRDPackageTests(unittest.TestCase):
    def test_prd_preserved(self):
        text = (ROOT / 'PRD.md').read_text()
        self.assertIn('SOLN LEGAL INTELLIGENCE MCP SERVER', text)
        self.assertIn('196 Represented Entities', text)
        self.assertIn('Ashley Executive Assistant', text)

    def test_inventory_is_not_misrepresented_as_ingested(self):
        inventory = json.loads((ROOT / 'registry' / 'initial_inventory.json').read_text())
        self.assertEqual(inventory['status'], 'inventory_only_not_ingested')
        self.assertIn('EO 1118', inventory['executive_orders'])

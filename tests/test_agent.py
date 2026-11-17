import unittest,json
from pathlib import Path
from src.agent import run_deterministic,STORES
class AgentTests(unittest.TestCase):
    def test_golden_cases(self):
        cases=[json.loads(x) for x in Path('data/golden_cases.jsonl').read_text().splitlines()]
        self.assertGreaterEqual(len(cases),20)
        for c in cases:
            with self.subTest(c['id']):
                actual=run_deterministic(c['input'])
                self.assertEqual(actual['decision'],c['expected']['decision'])
                self.assertEqual(actual['pickup_promised'],actual['decision']=='ELIGIBLE')
                if actual['coordinates'] is not None:
                    self.assertIn(actual['store_id'],STORES)
    def test_no_coordinates_for_unknown_store(self):
        a=run_deterministic({'country':'TR','city':'Istanbul','district':'Kadikoy','store_id':'UNKNOWN','order_status':'READY_FOR_PICKUP'})
        self.assertIsNone(a['coordinates'])
    def test_not_ready(self):
        a=run_deterministic({'country':'AE','city':'Dubai','district':'Downtown','store_id':'UAE-DXB-01','order_status':'PROCESSING'})
        self.assertFalse(a['pickup_promised'])
if __name__=='__main__':unittest.main()

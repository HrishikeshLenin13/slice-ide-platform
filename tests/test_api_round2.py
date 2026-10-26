import tempfile,unittest
from pathlib import Path
from backend.parser import PythonParser
from backend.graph import RepoGraph
from backend import slicer
class ApiExtensions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'demo.py').write_text('def target():\n    return 1\ndef caller(\n    argument: int,\n):\n    return target()\n')
        self.graph=RepoGraph(*PythonParser.parse_repo(str(self.root)))
        self.result=slicer.slice_for(self.graph,'demo.target')
    def tearDown(self):self.temp.cleanup()

    def test_json_report_round_trip_is_detached(self):
        data=self.result.to_dict();restored=slicer.SliceResult.from_dict(data);data['included'].clear();self.assertEqual(restored.included,self.result.included)
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict({'target':'x'})

    def test_summary_counts_members_without_exposing_lists(self):
        data=self.result.summary();self.assertEqual(data['target'],'demo.target');self.assertEqual(data['callers'],1);self.assertIsInstance(data['included'],int)

    def test_multiline_caller_signatures_remain_complete(self):
        text=slicer.render_slice(self.graph,self.result);self.assertIn('argument: int,',text);self.assertNotIn('return target()',text);self.assertIn('caller body omitted',text)

    def test_source_units_preserve_emission_order_and_detach_metadata(self):
        units=slicer.source_units(self.graph,self.result);self.assertEqual([u['id'] for u in units],self.result.included);units[0]['source']='changed';self.assertNotEqual(self.graph.symbols[self.result.target].source,'changed')

    def test_batch_reuses_graph_and_deduplicates_targets(self):
        batch=slicer.slice_many(self.graph,['demo.target','demo.target','demo.caller']);self.assertEqual(list(batch),['demo.target','demo.caller'])
        with self.assertRaises(KeyError):slicer.slice_many(self.graph,['demo.target','missing'])

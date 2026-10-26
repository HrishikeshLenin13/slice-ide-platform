import tempfile,unittest,copy,json
from pathlib import Path
from backend.parser import PythonParser
from backend.graph import RepoGraph
from backend import slicer
class CompletionContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        (root/'demo.py').write_text('VALUE=7\ndef leaf():return VALUE\ndef target():return leaf()\ndef caller():return target()\n')
        self.graph=RepoGraph(*PythonParser.parse_repo(str(root)));self.result=slicer.slice_for(self.graph,'demo.target')
    def tearDown(self):self.temp.cleanup()

    def test_001_single_slice_always_keeps_the_target_first(self):
        self.assertEqual(self.result.included[0],'demo.target');self.assertIn('demo.leaf',self.result.included)

    def test_002_report_round_trip_preserves_all_fields(self):
        data=self.result.to_dict();self.assertEqual(slicer.SliceResult.from_dict(data).to_dict(),data)

    def test_003_serialized_reports_are_json_compatible(self):
        data=self.result.to_dict();self.assertEqual(json.loads(json.dumps(data)),data)

    def test_004_reject_nonlist_included(self):
        data=self.result.to_dict();data['included']='bad'
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_005_reject_duplicate_included(self):
        data=self.result.to_dict();data['included']=['demo.target','demo.target']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_006_reject_empty_ids_in_included(self):
        data=self.result.to_dict();data['included']=['']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_007_reject_nonlist_callees(self):
        data=self.result.to_dict();data['callees']='bad'
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_008_reject_duplicate_callees(self):
        data=self.result.to_dict();data['callees']=['demo.target','demo.target']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_009_reject_empty_ids_in_callees(self):
        data=self.result.to_dict();data['callees']=['']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_010_reject_nonlist_callers(self):
        data=self.result.to_dict();data['callers']='bad'
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_011_reject_duplicate_callers(self):
        data=self.result.to_dict();data['callers']=['demo.target','demo.target']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_012_reject_empty_ids_in_callers(self):
        data=self.result.to_dict();data['callers']=['']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_013_reject_nonlist_type_refs(self):
        data=self.result.to_dict();data['type_refs']='bad'
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_014_reject_duplicate_type_refs(self):
        data=self.result.to_dict();data['type_refs']=['demo.target','demo.target']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_015_reject_empty_ids_in_type_refs(self):
        data=self.result.to_dict();data['type_refs']=['']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_016_reject_nonlist_global_refs(self):
        data=self.result.to_dict();data['global_refs']='bad'
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_017_reject_duplicate_global_refs(self):
        data=self.result.to_dict();data['global_refs']=['demo.target','demo.target']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_018_reject_empty_ids_in_global_refs(self):
        data=self.result.to_dict();data['global_refs']=['']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_019_reject_omitted_members_in_callees(self):
        data=self.result.to_dict();data['callees']=['missing']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_020_reject_omitted_members_in_callers(self):
        data=self.result.to_dict();data['callers']=['missing']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

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

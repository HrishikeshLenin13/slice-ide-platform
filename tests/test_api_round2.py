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

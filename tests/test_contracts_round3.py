import tempfile,unittest
from pathlib import Path
from backend.parser import PythonParser
from backend.graph import RepoGraph
from backend import slicer
class ContractsRound3(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        (root/'demo.py').write_text('def target(): return 1\ndef caller(): return target()\n')
        self.graph=RepoGraph(*PythonParser.parse_repo(str(root)));self.result=slicer.slice_for(self.graph,'demo.target')
    def tearDown(self):self.temp.cleanup()
    def test_depth_contract_rejects_floats_strings_and_booleans_before_batch_work(self):
        for value in [True,1.5,'1',-1]:
            with self.assertRaises(ValueError):slicer.slice_for(self.graph,'demo.target',caller_depth=value)
            with self.assertRaises(ValueError):slicer.slice_many(self.graph,['demo.target'],callee_depth=value)
    def test_reports_reject_duplicate_or_empty_member_ids(self):
        for included in [['demo.target','demo.target'],['demo.target','']]:
            with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),'included':included})
    def test_reports_reject_roles_that_reference_omitted_members(self):
        for name in ['callees','callers','type_refs','global_refs']:
            with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),name:['missing']})
        self.assertEqual(slicer.SliceResult.from_dict(self.result.to_dict()).included,self.result.included)
    def test_source_units_expose_detached_multi_role_labels(self):
        self.assertEqual(slicer.symbol_roles(self.result,'demo.target'),['target'])
        units=slicer.source_units(self.graph,self.result);self.assertIn('roles',units[0]);units[0]['roles'].clear()
        self.assertEqual(slicer.symbol_roles(self.result,'demo.target'),['target'])
        with self.assertRaises(KeyError):slicer.symbol_roles(self.result,'missing')

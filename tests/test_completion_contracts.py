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

    def test_021_reject_omitted_members_in_type_refs(self):
        data=self.result.to_dict();data['type_refs']=['missing']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_022_reject_omitted_members_in_global_refs(self):
        data=self.result.to_dict();data['global_refs']=['missing']
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict(data)

    def test_023_unknown_report_fields_fail_explicitly(self):
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),'secret':1})

    def test_024_target_must_be_in_the_included_members(self):
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),'target':'missing'})

    def test_025_soundness_must_be_a_real_boolean(self):
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),'sound':1})

    def test_026_metadata_lists_are_validated_for_unresolved(self):
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),'unresolved':{'demo.target':'not-a-list'}})

    def test_027_metadata_lists_are_validated_for_unsound_reasons(self):
        with self.assertRaises(ValueError):slicer.SliceResult.from_dict({**self.result.to_dict(),'unsound_reasons':{'demo.target':'not-a-list'}})

    def test_028_serialized_member_lists_are_detached(self):
        data=self.result.to_dict();data['included'].clear();self.assertTrue(self.result.included)

    def test_029_deserialized_nested_metadata_is_detached(self):
        data=self.result.to_dict();data['unresolved']={'demo.target':['name']};r=slicer.SliceResult.from_dict(data);data['unresolved']['demo.target'].clear();self.assertEqual(r.unresolved['demo.target'],['name'])

    def test_030_symbol_order_accessors_return_copies(self):
        ids=self.result.symbols_in_order();ids.clear();self.assertTrue(self.result.included)

    def test_031_summary_exposes_counts_not_internal_lists(self):
        summary=self.result.summary();self.assertEqual(summary['included'],len(self.result.included));self.assertIsInstance(summary['callers'],int)

    def test_032_target_role_is_exposed_to_ide_clients(self):
        self.assertIn('target',slicer.symbol_roles(self.result,'demo.target'))

    def test_033_unknown_role_queries_fail_instead_of_guessing(self):
        with self.assertRaises(KeyError):slicer.symbol_roles(self.result,'missing')

    def test_034_source_units_keep_selected_emission_order(self):
        self.assertEqual([u['id'] for u in slicer.source_units(self.graph,self.result)],self.result.included)

    def test_035_source_unit_role_arrays_are_detached(self):
        units=slicer.source_units(self.graph,self.result);units[0]['roles'].clear();self.assertTrue(slicer.symbol_roles(self.result,'demo.target'))

    def test_036_zero_callee_depth_omits_transitive_calls(self):
        r=slicer.slice_for(self.graph,'demo.target',callee_depth=0,caller_depth=0);self.assertNotIn('demo.leaf',r.included)

    def test_037_zero_caller_depth_omits_reverse_dependencies(self):
        r=slicer.slice_for(self.graph,'demo.target',caller_depth=0);self.assertEqual(r.callers,[])

    def test_038_batch_slicing_deduplicates_targets_in_request_order(self):
        r=slicer.slice_many(self.graph,['demo.target','demo.caller','demo.target']);self.assertEqual(list(r),['demo.target','demo.caller'])

    def test_039_batch_slicing_rejects_missing_targets(self):
        with self.assertRaises(KeyError):slicer.slice_many(self.graph,['demo.target','missing'])

    def test_040_batch_render_matches_individual_context(self):
        r=slicer.render_many(self.graph,['demo.target']);self.assertEqual(r['demo.target'],slicer.render_slice(self.graph,self.result))

    def test_041_rendering_does_not_mutate_parsed_source(self):
        before=self.graph.symbols['demo.caller'].source;slicer.render_slice(self.graph,self.result);self.assertEqual(self.graph.symbols['demo.caller'].source,before)

    def test_042_caller_text_omits_body_but_keeps_signature(self):
        text=slicer.render_slice(self.graph,self.result);self.assertIn('def caller',text);self.assertIn('caller body omitted',text)

    def test_043_depth_validation_rejects_booleans_and_floats(self):
        for value in [True,1.5,'1',-1]:
            with self.assertRaises(ValueError):slicer.slice_for(self.graph,'demo.target',caller_depth=value)

    def test_044_batch_depth_validation_precedes_target_iteration(self):
        with self.assertRaises(ValueError):slicer.slice_many(self.graph,[],callee_depth=1.5)

    def test_045_empty_batches_return_empty_outputs(self):
        self.assertEqual(slicer.slice_many(self.graph,[]),{});self.assertEqual(slicer.render_many(self.graph,[]),{})

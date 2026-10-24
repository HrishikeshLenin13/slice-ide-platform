import json
import unittest
from backend.slicer import SliceResult

class ResultTests(unittest.TestCase):
    def result(self):
        return SliceResult('a', ['a'], [], [], [], [], False, {'a': ['dynamic']})

    def test_json_report_is_detached(self):
        result = self.result()
        report = result.to_dict()
        self.assertEqual(json.loads(json.dumps(report))['target'], 'a')
        report['included'].clear()
        report['unsound_reasons']['a'].clear()
        self.assertEqual(result.included, ['a'])
        self.assertEqual(result.unsound_reasons, {'a': ['dynamic']})

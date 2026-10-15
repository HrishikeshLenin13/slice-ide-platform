from types import SimpleNamespace
import unittest
from backend.slicer import slice_for

class DepthTests(unittest.TestCase):
    def graph(self):
        symbol = SimpleNamespace(calls=set(), type_refs=set(), global_refs=set(), bases=set(), unresolved_calls=set())
        return SimpleNamespace(symbols={'target':symbol}, callers={}, is_sound=lambda sid: True)

    def test_negative_depths_are_rejected(self):
        for options in [{'callee_depth':-1}, {'caller_depth':-1}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                slice_for(self.graph(), 'target', **options)

    def test_zero_depth_includes_target(self):
        result = slice_for(self.graph(), 'target', callee_depth=0, caller_depth=0)
        self.assertEqual(result.included, ['target'])
        self.assertTrue(result.sound)

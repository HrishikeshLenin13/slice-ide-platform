import contextlib,io,json,tempfile,unittest
from pathlib import Path
from backend.parser import PythonParser,UniversalParser
class ParseDiagnostics(unittest.TestCase):
    def test_optional_collector_keeps_output_machine_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'good.py').write_text('def target():return 1');(root/'bad.py').write_text('def broken(')
            for parser in [PythonParser,UniversalParser]:
                errors=[];out=io.StringIO()
                with contextlib.redirect_stdout(out):modules,symbols=parser.parse_repo(str(root),diagnostics=errors)
                self.assertEqual(out.getvalue(),'');self.assertEqual(set(modules),{'good'});self.assertIn('good.target',symbols);self.assertEqual(len(errors),1);self.assertEqual(errors[0]['kind'],'SyntaxError');json.dumps(errors)

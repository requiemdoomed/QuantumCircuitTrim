from contextlib import redirect_stdout,redirect_stderr
import base64
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from circuittrim import parse_circuit,simplify
from circuittrim.cli import main
from circuittrim.render import comparison_svg,report_html,report_json


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.result=simplify(parse_circuit('H 0; X 1; X 1; CX 0 1',2))

    def test_svg_escapes_text(self):
        svg=comparison_svg(self.result,subtitle='<script>alert(1)</script>')
        ET.fromstring(svg)
        self.assertNotIn('<script>',svg)
        self.assertIn('&lt;script&gt;',svg)

    def test_json(self):
        data=json.loads(report_json(self.result))
        self.assertEqual(data['gates_before'],4)
        self.assertEqual(data['gates_after'],2)
        self.assertTrue(data['verification']['equivalent'])
        self.assertEqual(data['cancellations'][0]['positions'],[2,3])

    def test_self_contained_report(self):
        html=report_html(self.result)
        self.assertIn('<svg',html)
        self.assertNotIn('<script',html)
        self.assertNotIn('src="http',html)

    def test_empty_and_maximum_size_svg(self):
        for text,n in [('',1),('H 0; X 3; '*60,4)]:
            ET.fromstring(comparison_svg(simplify(parse_circuit(text,n))))
        self.assertIn('Identity',report_html(simplify(parse_circuit('',1))))


class CLITests(unittest.TestCase):
    def run_cli(self,args):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err): code=main(args)
        return code,out.getvalue(),err.getvalue()

    def test_default_demo(self):
        code,out,err=self.run_cli([])
        self.assertEqual(code,0)
        self.assertIn('4 -> 0',out)
        self.assertEqual(err,'')

    def test_inline(self):
        self.assertEqual(self.run_cli(['--text','H 0; H 0','--qubits','1'])[0],0)

    def test_invalid_input(self):
        code,out,err=self.run_cli(['--text','CX 0 0'])
        self.assertEqual(code,2)
        self.assertIn('Line 1',err)
        self.assertNotIn('Traceback',err)

    def test_missing_file(self):
        self.assertEqual(self.run_cli(['does-not-exist.ct'])[0],2)

    def test_exports_and_paths_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='circuit trim ') as folder:
            root=Path(folder)
            source=root/'input.ct'
            source.write_text('\ufeffH 0\nH 0',encoding='utf-8')
            targets=[root/'exports'/'report.html',root/'result.json',root/'circuit.svg']
            args=[str(source),'--qubits','1','--report',str(targets[0]),'--json',str(targets[1]),'--svg',str(targets[2])]
            self.assertEqual(self.run_cli(args)[0],0)
            self.assertTrue(all(p.is_file() for p in targets))
            self.assertEqual(json.loads(targets[1].read_text())['gates_after'],0)

    def test_protect_input_and_distinct_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.ct'
            source.write_text('H 0')
            self.assertEqual(self.run_cli([str(source),'--report',str(source)])[0],2)
            self.assertEqual(source.read_text(),'H 0')
            dest=str(Path(folder)/'same')
            self.assertEqual(self.run_cli(['--json',dest,'--svg',dest])[0],2)


@unittest.skipUnless(importlib.util.find_spec('ipywidgets'),'Installing notebook extras enables widget tests.')
class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        from circuittrim.workbench import Workbench
        self.workbench=Workbench()

    def tearDown(self): self.workbench.close()

    def test_initial_result_and_download(self):
        self.assertEqual(len(self.workbench.result.simplified.gates),2)
        encoded=self.workbench.download.value.split('base64,')[1].split('"')[0]
        self.assertIn('CircuitTrim',base64.b64decode(encoded).decode())

    def test_edit_invalidates_result(self):
        self.workbench.editor.value='H 0'
        self.assertIsNone(self.workbench.result)
        self.assertEqual(self.workbench.download.value,'')
        self.assertEqual(self.workbench.output.value,'')

    def test_button_click(self):
        self.workbench.editor.value='H 0\nH 0'
        self.workbench.run.click()
        self.assertEqual(self.workbench.result.removed,2)
        self.assertFalse(self.workbench.run.disabled)

    def test_invalid_input_and_recovery(self):
        self.workbench.editor.value='<script> 0'
        self.workbench.run.click()
        self.assertIsNone(self.workbench.result)
        self.assertNotIn('<script>',self.workbench.status.value)
        self.assertEqual(self.workbench.output.value,'')
        self.workbench.editor.value=''
        self.workbench.run.click()
        self.assertEqual(len(self.workbench.result.simplified.gates),0)

    def test_preset_then_invalid_qubits(self):
        self.workbench.preset.value='Three-qubit GHZ state'
        self.assertEqual(self.workbench.qubits.value,3)
        self.assertEqual(len(self.workbench.result.simplified.gates),3)
        self.workbench.qubits.value=1
        self.workbench.run.click()
        self.assertIsNone(self.workbench.result)

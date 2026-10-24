"""Optional Jupyter controls; the core does not depend on ipywidgets."""
import base64
from html import escape
from .core import parse_circuit, simplify
from .presets import PRESETS
from .render import report_fragment, report_html


class Workbench:
    """Edit a circuit, simplify it, and download an offline report."""

    def __init__(self):
        try:
            import ipywidgets as widgets
        except ImportError as error:
            raise ImportError('Install the notebook extra: python -m pip install -e ".[notebook]"') from error
        self.result = None
        self.preset = widgets.Dropdown(options=list(PRESETS), description="Example:", layout=widgets.Layout(width="100%"))
        self.qubits = widgets.Dropdown(options=[1, 2, 3, 4], value=2, description="Qubits:")
        self.editor = widgets.Textarea(value=next(iter(PRESETS.values()))[1], placeholder="H 0\nCX 0 1", description="Circuit:",
                                       layout=widgets.Layout(width="100%", height="230px"))
        self.run = widgets.Button(description="Simplify & verify", button_style="primary", icon="check",
                                  layout=widgets.Layout(width="190px"))
        self.status = widgets.HTML()
        self.output = widgets.HTML()
        self.download = widgets.HTML()
        self.run.on_click(self._run)
        self.preset.observe(self._load, names="value")
        self.editor.observe(self._invalidate, names="value")
        self.qubits.observe(self._invalidate, names="value")
        self.view = widgets.VBox([
            widgets.HTML('<h2 style="margin-bottom:4px">CircuitTrim</h2><p>Write a small circuit. Remove redundant gates. Check the full operation.</p>'),
            self.preset, self.qubits, self.editor,
            widgets.HTML('<small>One gate per line. q0 is the lowest bit. Gates: H, X, Y, Z, S, SDG, T, TDG, CX, CZ, SWAP. Maximum: 120 gates.</small>'),
            self.run, self.status, self.download, self.output,
        ], layout=widgets.Layout(width="100%"))
        self._run()

    def _invalidate(self, change):
        self.result = None
        self.output.value = ""
        self.download.value = ""
        self.status.value = '<p>Input changed. Select <strong>Simplify &amp; verify</strong> to update the result.</p>'

    def _load(self, change):
        count, text = PRESETS[change["new"]]
        self.qubits.value = count
        self.editor.value = text
        self._run()

    def _run(self, button=None):
        self.run.disabled = True
        try:
            result = simplify(parse_circuit(self.editor.value, self.qubits.value))
            self.output.value = report_fragment(result)
            payload = base64.b64encode(report_html(result).encode("utf-8")).decode("ascii")
            self.download.value = f'<a download="circuittrim-report.html" href="data:text/html;base64,{payload}">Download this report</a>'
            self.result = result
            self.status.value = '<p style="color:#247963">Comparison complete.</p>'
        except ValueError as error:
            self.result = None
            self.output.value = ""
            self.download.value = ""
            self.status.value = f'<p role="alert" style="color:#a23832">{escape(str(error))}</p>'
        finally:
            self.run.disabled = False

    def close(self):
        for widget in self.view.children:
            widget.close()
        self.view.close()


def launch():
    """Display and return a workbench so it can also be controlled from code."""
    from IPython.display import display
    workbench = Workbench()
    display(workbench.view)
    return workbench

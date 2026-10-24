# Setup and troubleshooting

The command-line demo runs directly from the extracted project folder:

```bash
python -m circuittrim examples/bell.ct --qubits 2
```

Use Python 3.10 or newer. `python --version` prints the active version.

## Windows virtual environment

Open PowerShell in the project folder:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[notebook]"
.venv\Scripts\python -m jupyterlab
```

These commands use the environment directly and do not require changing PowerShell's execution policy. If `py` is unavailable, replace it with `python`.

## macOS or Linux virtual environment

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[notebook]"
.venv/bin/python -m jupyterlab
```

## Choosing the right notebook kernel

If imports fail despite a successful installation, the notebook may be using a different Python environment. Register the project environment:

Windows:

```powershell
.venv\Scripts\python -m ipykernel install --user --name circuittrim --display-name "Python (CircuitTrim)"
```

macOS/Linux:

```bash
.venv/bin/python -m ipykernel install --user --name circuittrim --display-name "Python (CircuitTrim)"
```

Select **Python (CircuitTrim)** in Jupyter, restart the kernel, and run the notebook from the beginning. Run `import sys; print(sys.executable)` in a cell if you need to check which Python it uses.

## Common problems

| Problem | Fix |
|---|---|
| `No module named circuittrim` | Run from the folder containing `pyproject.toml`, or install with `python -m pip install .`. |
| Notebook cannot find the project | Keep the `notebooks` folder inside the extracted project; do not move the notebook alone. |
| Controls display as plain text | Install the notebook extra in the Jupyter environment, use JupyterLab 4, and restart it. GitHub cannot run widgets. |
| Download link does nothing | Some notebook hosts restrict data links. Use the notebook's export cell or the CLI `--report` option instead. |
| A qubit index is out of range | With two qubits, valid indices are 0 and 1. Increase the selector or correct the input. |
| A gate is not simplified | Only adjacent inverse pairs on the same qubits are removed. CX direction matters. |
| A tiny nonzero verification error appears | Floating-point arithmetic introduces small rounding differences. The default tolerance is `1e-9`. |
| Notebook check cannot bind a socket | Run `python scripts/check_notebook.py --in-process` in a restricted environment. |
| Image regeneration reports missing Cairo | The included assets remain usable. Install Cairo for your platform only if regenerating PNG/GIF files. |

Commands starting with `python -m` go in a terminal. Python API examples go in Python or notebook code cells. Run notebook cells in order.

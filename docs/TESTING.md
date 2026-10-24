# Validation record

Validated locally on **2026-10-24**, using **Python 3.12 on Linux**.

## Completed checks

- **38 unittest methods passed**, including the five optional notebook-control tests.
- **500 seeded randomized circuits** preserved their complete operations after simplification and produced the same result on a second simplification pass.
- Every supported inverse pair was checked on every valid ordered wire combination for 1–4 qubits.
- Individual gates were compared with an independent reference calculation; known gate columns, control directions, Bell states, and GHZ states were also checked.
- Invalid instructions, invalid states, empty circuits, maximum-size circuits, phase differences, file errors, and paths containing spaces were tested.
- HTML, SVG, and JSON exports were checked. SVG files were parsed and the included PNG diagrams were visually inspected.
- All **8 notebook code cells** ran successfully in an in-process IPython kernel. The workbench's preset changes, button callbacks, input errors, recovery, download payload, and stale-result handling were exercised programmatically.
- Demo animation frames were generated from actual intermediate circuits, each verified against the original.

## Packaging and platform scope

A wheel and source distribution are built during release validation. The wheel is installed in a fresh virtual environment and exercised outside the source folder before packaging the ZIP.

Windows and macOS were not available for direct local testing. The included GitHub Actions workflow schedules core tests on Windows, macOS, and Linux with Python 3.10, 3.12, and 3.13. Those remote jobs have not been run as part of this local build.

This environment restricts local socket binding, so notebook execution uses `scripts/check_notebook.py --in-process`. A separate live Jupyter browser session was not exercised here. The standard kernel execution path is included in GitHub Actions.

Passing tests support the documented behavior; they are not a guarantee that no undiscovered defects exist.

## Reproduce

```bash
python -m unittest discover -s tests -v
python -m pip install -e ".[notebook,dev]"
python scripts/check_notebook.py
python scripts/make_demo.py
```

In environments that do not permit notebook kernel sockets:

```bash
python scripts/check_notebook.py --in-process
```

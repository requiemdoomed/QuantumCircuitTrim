# QuantumCircuitTrim

**Simplify small quantum circuits. Check that their operations stay the same.**

By **Swayam Shakya** · Python 3.10+ · MIT License

QuantumCircuitTrim removes adjacent inverse gates, draws the before-and-after circuits, and verifies the complete circuit operation. It is a compact quantum computing project with a command-line tool and an interactive Jupyter notebook.

The core uses only Python's standard library. No dataset, API key, cloud account, or quantum hardware is required.

## Demo

![Step-by-step gate cancellation](docs/images/demo.gif)

This animation is rendered from actual simplifier results, one cancellation at a time. The Bell-state example goes from **12 gates to 2**, an **83.3% reduction**, while preserving its operation on all four basis inputs.

- **Interactive demo:** [notebooks/CircuitTrim.ipynb](notebooks/CircuitTrim.ipynb). Run it locally to use the controls; GitHub displays the static notebook preview.
- **Saved report:** [docs/demo.html](docs/demo.html). Download the project and open this file in a browser. It is a self-contained report, not a hosted application.
- **Vector diagram:** [docs/images/comparison.svg](docs/images/comparison.svg).

## Quick start

1. Install Python 3.10 or newer.
2. Extract the ZIP and open a terminal in the folder containing this README.
3. Run the example:

```bash
python -m circuittrim examples/bell.ct --qubits 2
```

On macOS or Linux, use `python3` if `python` is unavailable. On Windows, `py` may be used instead. The core command works directly from the extracted folder without installing anything else.

Expected summary:

```text
CircuitTrim 1.0.0 | 2 qubit(s)
Gates: 12 -> 2 (83.3% removed)
Equivalent: True | inputs checked: 4 | max error: ...

Simplified circuit:
H 0
CX 0 1
```

The final floating-point error can vary slightly by platform. It must be below the reported tolerance, `1e-9`.

### Open the interactive notebook

From the project folder:

```bash
python -m pip install -e ".[notebook]"
python -m jupyterlab
```

Open `notebooks/CircuitTrim.ipynb`, select a Python kernel from the same environment, and run the cells from the top. The workbench includes:

- Four example circuits and an editable instruction box.
- A qubit count selector and **Simplify & verify** button.
- Before-and-after diagrams, gate counts, and a cancellation log.
- Full-operation verification and calculated measurement probabilities.
- A downloadable HTML report.

Editing the circuit clears the previous result until it is recomputed. Invalid instructions produce an explanatory message rather than leaving an old result on screen.

See [SETUP.md](docs/SETUP.md) for virtual environments and Jupyter troubleshooting. The notebook dependencies need an internet connection to install; the application runs locally afterward.

## Write a circuit

Use one gate per line, or separate instructions with semicolons:

```text
H 0
X 1
X 1
CX 0 1
```

This becomes:

```text
H 0
CX 0 1
```

Gate names are case-insensitive. `H q0` and `CX q0, q1` also work. `#` starts a comment. An empty circuit means the identity operation.

| Gate | Arguments | Cancels with |
|---|---|---|
| H, X, Y, Z | One qubit | The same gate on the same qubit |
| S | One qubit | SDG |
| SDG | One qubit | S |
| T | One qubit | TDG |
| TDG | One qubit | T |
| CX | Control, target | CX with the same control and target |
| CZ | Two different qubits | CZ on the same pair |
| SWAP | Two different qubits | SWAP on the same pair |

CZ and SWAP are symmetric, so reversing their listed wires does not change the gate. Reversing CX changes its control direction and is not treated as the same gate.

**Bit order:** q0 is the least significant bit. `X 0` on a three-qubit all-zero state produces `001`. Diagrams show q0 at the top; probability labels read q(n−1)…q0.

## Why verification matters

A probability chart alone does not prove two circuits are equivalent. For example, applying Z to `|0⟩` and doing nothing produce the same measurement probabilities, but the operations differ on other inputs.

CircuitTrim compares complex output amplitudes for **every computational basis input**. These outputs form the columns of the operator, so checking them checks its action on any input superposition. The comparison uses a tolerance of `1e-9` and includes phase. It is deliberately stricter than equivalence up to a global phase.

The simplifier itself is a stack-based pass: each gate is pushed once and popped at most once. See [ALGORITHM.md](docs/ALGORITHM.md) for a worked example and the exact scope.

## Scope

- Supporting **1–4 qubits** and **up to 120 gates** keeps full verification quick.
- Only adjacent inverse pairs are removed, including pairs exposed by earlier removals. Gates are not commuted or rearranged.
- `S; S` is not rewritten as Z, and arbitrary rotation angles are not supported.
- This version does not include measurement instructions, reset, classical conditions, noise, or hardware execution.
- Gate count reduction is not a measurement of hardware speed or fidelity.
- The result is not guaranteed to be the globally smallest circuit.

## References

- [IBM Quantum: inverse cancellation](https://eu-de.quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.InverseCancellation)
- [IBM Quantum: Hadamard gate](https://quantum.cloud.ibm.com/docs/en/api/qiskit/1.1/qiskit.circuit.library.HGate)
- [Python: unittest](https://docs.python.org/3/library/unittest.html)

These references describe the underlying concepts and test tooling. CircuitTrim implements its own small simulator and does not require Qiskit.

## License

MIT License. Copyright © 2026 **Swayam Shakya**. See [LICENSE](LICENSE).

"""Circuit parsing, adjacent inverse cancellation, and exact-state simulation."""

from dataclasses import dataclass
import cmath
import math

MAX_QUBITS = 4
MAX_GATES = 120
ARITY = {"H": 1, "X": 1, "Y": 1, "Z": 1, "S": 1, "SDG": 1,
         "T": 1, "TDG": 1, "CX": 2, "CZ": 2, "SWAP": 2}
INVERSE = {"H": "H", "X": "X", "Y": "Y", "Z": "Z", "S": "SDG",
           "SDG": "S", "T": "TDG", "TDG": "T", "CX": "CX",
           "CZ": "CZ", "SWAP": "SWAP"}
ROOT_HALF = 1 / math.sqrt(2)
MATRICES = {
    "H": ((ROOT_HALF, ROOT_HALF), (ROOT_HALF, -ROOT_HALF)),
    "X": ((0, 1), (1, 0)),
    "Y": ((0, -1j), (1j, 0)),
    "Z": ((1, 0), (0, -1)),
    "S": ((1, 0), (0, 1j)),
    "SDG": ((1, 0), (0, -1j)),
    "T": ((1, 0), (0, cmath.exp(1j * math.pi / 4))),
    "TDG": ((1, 0), (0, cmath.exp(-1j * math.pi / 4))),
}


@dataclass(frozen=True)
class Gate:
    name: str
    qubits: tuple[int, ...]

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise ValueError("A gate name must be text.")
        name = self.name.upper()
        if name not in ARITY:
            raise ValueError(f"Unknown gate {name!r}. Use: {', '.join(ARITY)}.")
        try:
            qubits = tuple(self.qubits)
        except TypeError as error:
            raise ValueError("Qubits must be a sequence of integers.") from error
        if len(qubits) != ARITY[name]:
            raise ValueError(f"{name} needs {ARITY[name]} qubit index(es).")
        if any(type(q) is not int or q < 0 for q in qubits):
            raise ValueError("Qubit indices must be nonnegative integers.")
        if len(set(qubits)) != len(qubits):
            raise ValueError("A two-qubit gate needs two different qubits.")
        # Treating the two symmetric gates consistently.
        if name in {"CZ", "SWAP"}:
            qubits = tuple(sorted(qubits))
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "qubits", qubits)

    def __str__(self):
        return f"{self.name} {' '.join(map(str, self.qubits))}"


@dataclass(frozen=True)
class Circuit:
    n_qubits: int
    gates: tuple[Gate, ...] = ()

    def __post_init__(self):
        if type(self.n_qubits) is not int or not 1 <= self.n_qubits <= MAX_QUBITS:
            raise ValueError(f"Choose between 1 and {MAX_QUBITS} qubits.")
        try:
            gates = tuple(self.gates)
        except TypeError as error:
            raise ValueError("Gates must be a sequence of Gate objects.") from error
        if len(gates) > MAX_GATES:
            raise ValueError(f"Use at most {MAX_GATES} gates.")
        for gate in gates:
            if not isinstance(gate, Gate):
                raise ValueError("Each circuit entry must be a Gate object.")
            if any(q >= self.n_qubits for q in gate.qubits):
                raise ValueError(f"{gate}: indices must be below {self.n_qubits}.")
        object.__setattr__(self, "gates", gates)

    def to_text(self):
        return "\n".join(map(str, self.gates))


def parse_circuit(text: str, n_qubits: int = 2) -> Circuit:
    """Read one gate per line; semicolons and # comments are also accepted."""
    Circuit(n_qubits)
    if not isinstance(text, str):
        raise ValueError("Circuit input must be text.")
    if len(text) > 16000:
        raise ValueError("Circuit input is too long (maximum 16,000 characters).")
    gates = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for instruction in line.split("#", 1)[0].split(";"):
            tokens = instruction.replace(",", " ").split()
            if not tokens:
                continue
            try:
                qubits = tuple(int(token[1:] if token.lower().startswith("q") else token)
                               for token in tokens[1:])
                gate = Gate(tokens[0], qubits)
                if any(q >= n_qubits for q in gate.qubits):
                    raise ValueError(f"Qubit indices must be below {n_qubits}.")
                gates.append(gate)
                if len(gates) > MAX_GATES:
                    raise ValueError(f"Use at most {MAX_GATES} gates.")
            except ValueError as error:
                raise ValueError(f"Line {line_number}: {error}") from error
    return Circuit(n_qubits, tuple(gates))


@dataclass(frozen=True)
class Cancellation:
    left_index: int
    right_index: int
    left: Gate
    right: Gate

    @property
    def reason(self):
        return f"{self.left} + {self.right} = identity"


@dataclass(frozen=True)
class Optimization:
    original: Circuit
    simplified: Circuit
    cancellations: tuple[Cancellation, ...]

    @property
    def removed(self):
        return len(self.original.gates) - len(self.simplified.gates)

    @property
    def reduction_percent(self):
        return 100 * self.removed / len(self.original.gates) if self.original.gates else 0.0


def simplify(circuit: Circuit) -> Optimization:
    """Cancel adjacent inverse pairs, including pairs exposed by removals."""
    stack = []
    cancellations = []
    for index, gate in enumerate(circuit.gates):
        if stack and INVERSE[gate.name] == stack[-1][1].name and gate.qubits == stack[-1][1].qubits:
            left_index, left = stack.pop()
            cancellations.append(Cancellation(left_index, index, left, gate))
        else:
            stack.append((index, gate))
    result = Circuit(circuit.n_qubits, tuple(gate for _, gate in stack))
    return Optimization(circuit, result, tuple(cancellations))


def _apply(state: list[complex], gate: Gate) -> list[complex]:
    result = state.copy()
    if len(gate.qubits) == 1:
        mask = 1 << gate.qubits[0]
        matrix = MATRICES[gate.name]
        for index in range(len(state)):
            if index & mask:
                continue
            other = index | mask
            a, b = state[index], state[other]
            result[index] = matrix[0][0] * a + matrix[0][1] * b
            result[other] = matrix[1][0] * a + matrix[1][1] * b
        return result
    first, second = (1 << q for q in gate.qubits)
    for index, amplitude in enumerate(state):
        if gate.name == "CX":
            target = index ^ second if index & first else index
            result[target] = amplitude
        elif gate.name == "CZ":
            result[index] = -amplitude if index & first and index & second else amplitude
        else:
            different = bool(index & first) != bool(index & second)
            target = index ^ first ^ second if different else index
            result[target] = amplitude
    return result


def evolve(circuit: Circuit, state) -> tuple[complex, ...]:
    """Apply a circuit to a normalized state; q0 is the least significant bit."""
    try:
        values = [complex(value) for value in state]
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("State amplitudes must be complex-compatible numbers.") from error
    if len(values) != 2 ** circuit.n_qubits:
        raise ValueError("The state length must equal 2 ** n_qubits.")
    if not all(math.isfinite(x.real) and math.isfinite(x.imag) for x in values):
        raise ValueError("State amplitudes must be finite.")
    if not math.isclose(sum(abs(x) ** 2 for x in values), 1, abs_tol=1e-9, rel_tol=1e-9):
        raise ValueError("State probabilities must sum to 1.")
    for gate in circuit.gates:
        values = _apply(values, gate)
    return tuple(values)


def statevector(circuit: Circuit, basis: int = 0) -> tuple[complex, ...]:
    if type(basis) is not int or not 0 <= basis < 2 ** circuit.n_qubits:
        raise ValueError("The initial basis index is outside the circuit's state space.")
    state = [0j] * (2 ** circuit.n_qubits)
    state[basis] = 1 + 0j
    return evolve(circuit, state)


def probabilities(circuit: Circuit, basis: int = 0) -> dict[str, float]:
    return {format(i, f"0{circuit.n_qubits}b"): abs(a) ** 2
            for i, a in enumerate(statevector(circuit, basis))}


@dataclass(frozen=True)
class Verification:
    equivalent: bool
    max_error: float
    inputs_checked: int
    tolerance: float


def verify(original: Circuit, simplified: Circuit, tolerance: float = 1e-9) -> Verification:
    """Compare every operator column, not only measurement probabilities."""
    if original.n_qubits != simplified.n_qubits:
        raise ValueError("Both circuits must have the same number of qubits.")
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Tolerance must be a positive finite number.")
    max_error = 0.0
    for basis in range(2 ** original.n_qubits):
        before, after = statevector(original, basis), statevector(simplified, basis)
        max_error = max(max_error, max(abs(a - b) for a, b in zip(before, after)))
    return Verification(max_error <= tolerance, max_error, 2 ** original.n_qubits, tolerance)

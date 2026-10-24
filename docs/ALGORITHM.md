# How CircuitTrim works

## Cancellation rule

For two adjacent gates acting on the same wires, remove them if their matrices multiply to the identity. The implemented inverse pairs are:

- H/H, X/X, Y/Y, Z/Z.
- S/SDG and SDG/S.
- T/TDG and TDG/T.
- CX/CX with identical control and target.
- CZ/CZ and SWAP/SWAP on the same unordered pair.

CZ and SWAP wire lists are canonicalized when parsed. CX wire order is preserved.

## Stack pass

Read instructions from left to right. If the incoming gate is the inverse of the last retained gate on the same wires, remove that last gate. Otherwise retain the new gate.

For `H 0; X 0; X 0; H 0`:

1. Retain H and then X.
2. The next X cancels the retained X.
3. The last H cancels the retained H.
4. No gates remain; the circuit is the identity.

The log stores original zero-based positions internally and shows one-based instruction positions in the interface. Comments and blank lines do not count as instructions.

Each instruction is considered once. Simplification takes O(g) time and O(g) storage for g gates. A second pass produces the same result.

## Simulation and bit order

A state vector contains 2ⁿ complex amplitudes. The simulator applies a 2×2 matrix to each amplitude pair for a single-qubit gate. CX and SWAP permute amplitudes. CZ changes the sign where both affected bits are 1.

Qubit zero is the least significant bit. Circuit text is applied in the order written; drawings read left to right.

## Verification

For n qubits, simulate both circuits on all 2ⁿ computational basis inputs. Compare each complex amplitude of the outputs. The largest absolute difference must be no larger than `1e-9`.

The basis outputs are all columns of the circuit operator. Agreement on all columns implies agreement on arbitrary input superpositions, up to numerical tolerance. The check includes complex phase and does not merely compare probabilities.

A single simulation costs O(g × 2ⁿ). Full verification costs O(g × 4ⁿ). State storage is O(2ⁿ), since operator columns are checked one at a time. The implementation limits circuits to four qubits and 120 gates.

This check is stricter than physical equivalence up to a global phase. The supported cancellation rules preserve the operator itself, so strict comparison is appropriate here.

## Deliberate limits

The pass does not commute gates, fuse rotations, rewrite S/S into Z, or optimize according to device connectivity. `X 0; H 1; X 0` remains unchanged even though more advanced reasoning could simplify it. Measurements and noisy channels need different circuit semantics and are outside this project.

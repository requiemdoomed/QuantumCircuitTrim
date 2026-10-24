"""CircuitTrim: small circuits, fewer gates."""
from .core import (Circuit, Gate, Optimization, Verification, evolve,
                   parse_circuit, probabilities, simplify, statevector, verify)

__version__ = "1.0.0"
__author__ = "Swayam Shakya"
__all__ = ["Circuit", "Gate", "Optimization", "Verification", "evolve", "parse_circuit",
           "probabilities", "simplify", "statevector", "verify"]

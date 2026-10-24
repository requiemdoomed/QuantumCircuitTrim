"""Run a circuit comparison from a terminal."""
import argparse
from pathlib import Path
import sys
from . import __version__
from .core import parse_circuit, simplify, verify
from .render import comparison_svg, report_html, report_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="Remove adjacent inverse gates and verify the resulting circuit.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("file", nargs="?", type=Path, help="Circuit text file (.ct or .txt)")
    source.add_argument("--text", help='Circuit text, for example "H 0; X 0; X 0; H 0"')
    parser.add_argument("--qubits", type=int, default=2, help="Number of qubits, 1–4 (default: 2)")
    parser.add_argument("--report", type=Path, help="Write a self-contained HTML report")
    parser.add_argument("--json", dest="json_path", type=Path, help="Write the result as JSON")
    parser.add_argument("--svg", type=Path, help="Write a circuit diagram as SVG")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        text = args.file.read_text(encoding="utf-8-sig") if args.file else args.text
        if text is None:
            text = "H 0; X 0; X 0; H 0"
        result = simplify(parse_circuit(text, args.qubits))
        check = verify(result.original, result.simplified)
        destinations = [path.resolve() for path in (args.report, args.json_path, args.svg) if path]
        if len(destinations) != len(set(destinations)):
            raise ValueError("Choose a different path for each output format.")
        if args.file and args.file.resolve() in destinations:
            raise ValueError("An output cannot overwrite the input circuit file.")
        print(f"CircuitTrim {__version__} | {args.qubits} qubit(s)")
        print(f"Gates: {len(result.original.gates)} -> {len(result.simplified.gates)} ({result.reduction_percent:.1f}% removed)")
        print(f"Equivalent: {check.equivalent} | inputs checked: {check.inputs_checked} | max error: {check.max_error:.3e}")
        for step in result.cancellations:
            print(f"  Positions {step.left_index+1}, {step.right_index+1}: {step.reason}")
        print("\nSimplified circuit:\n" + (result.simplified.to_text() or "Identity (no gates)"))
        for path, content in ((args.report, report_html), (args.json_path, report_json), (args.svg, comparison_svg)):
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content(result), encoding="utf-8")
                print(f"Saved: {path}")
        return 0 if check.equivalent else 1
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

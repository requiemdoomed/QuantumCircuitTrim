"""Self-contained circuit drawings and a printable comparison report."""

from html import escape
import json
from .core import Optimization, Verification, probabilities, verify

INK = "#202434"
MUTED = "#697186"
PURPLE = "#6355d9"
ORANGE = "#c66b3e"


def _text(x, y, text, size=14, color=INK, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(str(text))}</text>')


def _drawing(circuit, y, width, removed=()):
    pieces = []
    x0, spacing = 142, 66
    for q in range(circuit.n_qubits):
        row = y + q * 54
        pieces.append(f'<line x1="113" y1="{row}" x2="{width - 42}" y2="{row}" stroke="#d9dce6" stroke-width="2"/>')
        pieces.append(_text(58, row + 5, f"q{q}", 15, MUTED, 600))
    if not circuit.gates:
        pieces.append(f'<rect x="132" y="{y-17}" width="198" height="34" rx="7" fill="white"/>')
        pieces.append(_text(142, y + 5, "Identity · no gates", 16, MUTED))
    for i, gate in enumerate(circuit.gates):
        x = x0 + i * spacing
        color = ORANGE if i in removed else PURPLE
        fill = "#fff0e7" if i in removed else "#eeecff"
        pieces.append(f'<g><title>{escape(str(gate))}</title>')
        positions = [y + q * 54 for q in gate.qubits]
        if len(positions) == 1:
            row = positions[0]
            pieces.append(f'<rect x="{x-22}" y="{row-18}" width="44" height="36" rx="9" fill="{fill}" stroke="{color}"/>')
            label = {"SDG": "S†", "TDG": "T†"}.get(gate.name, gate.name)
            pieces.append(_text(x, row + 5, label, 15, color, 600, "middle"))
        else:
            pieces.append(f'<line x1="{x}" y1="{min(positions)}" x2="{x}" y2="{max(positions)}" stroke="{color}" stroke-width="2"/>')
            if gate.name == "SWAP":
                for row in positions:
                    pieces.append(f'<path d="M{x-7},{row-7} L{x+7},{row+7} M{x-7},{row+7} L{x+7},{row-7}" stroke="{color}" stroke-width="2.5"/>')
            else:
                pieces.append(f'<circle cx="{x}" cy="{positions[0]}" r="6" fill="{color}"/>')
                if gate.name == "CZ":
                    pieces.append(f'<circle cx="{x}" cy="{positions[1]}" r="6" fill="{color}"/>')
                else:
                    row = positions[1]
                    pieces.append(f'<circle cx="{x}" cy="{row}" r="13" fill="{fill}" stroke="{color}" stroke-width="2"/>')
                    pieces.append(f'<path d="M{x-8},{row} H{x+8} M{x},{row-8} V{row+8}" stroke="{color}" stroke-width="2"/>')
            pieces.append(_text(x, min(positions) - 19, gate.name, 10, color, 600, "middle"))
        pieces.append(_text(x, y + circuit.n_qubits * 54 - 17, i + 1, 10, MUTED, anchor="middle"))
        pieces.append('</g>')
    return "".join(pieces)


def comparison_svg(result: Optimization, check: Verification | None = None,
                   subtitle: str = "Adjacent inverse gates, removed safely.") -> str:
    check = check or verify(result.original, result.simplified)
    width = max(1060, 190 + 66 * len(result.original.gates))
    panel_height = 102 + 54 * result.original.n_qubits
    height = 294 + 2 * panel_height
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
              '<title id="title">CircuitTrim: circuit comparison</title>',
              '<desc id="desc">Original and simplified circuits. Qubit zero is shown on the top wire.</desc>',
              f'<rect width="{width}" height="{height}" rx="20" fill="#f6f7fb"/>',
              '<g font-family="DejaVu Sans, Arial, sans-serif">',
              _text(38, 43, "CIRCUITTRIM", 13, PURPLE, 700),
              _text(38, 82, "Quantum circuit simplifier", 30, INK, 600),
              _text(38, 109, subtitle, 14, MUTED)]
    tile_width = (width - 100) / 4
    stats = [("ORIGINAL GATES", str(len(result.original.gates))),
             ("REMAINING GATES", str(len(result.simplified.gates))),
             ("GATE REDUCTION", f"{result.reduction_percent:.1f}%"),
             ("FULL OPERATOR CHECK", "Equivalent" if check.equivalent else "Different")]
    for index, (label, value) in enumerate(stats):
        x = 38 + index * (tile_width + 8)
        pieces.append(f'<rect x="{x}" y="134" width="{tile_width}" height="82" rx="12" fill="white" stroke="#e4e6ee"/>')
        pieces.append(_text(x + 16, 158, label, 10, MUTED, 600))
        pieces.append(_text(x + 16, 192, value, 25, "#247963" if index == 3 and check.equivalent else INK, 600))
    removed = {i for c in result.cancellations for i in (c.left_index, c.right_index)}
    for index, (name, circuit) in enumerate((("Original circuit", result.original), ("Simplified circuit", result.simplified))):
        top = 238 + index * (panel_height + 14)
        pieces.append(f'<rect x="38" y="{top}" width="{width-76}" height="{panel_height}" rx="14" fill="white" stroke="#e4e6ee"/>')
        pieces.append(_text(58, top + 29, name, 15, INK, 600))
        if index == 0:
            pieces.append(_text(width - 58, top + 29, "Orange = removed", 12, ORANGE, anchor="end"))
        pieces.append(_drawing(circuit, top + 69, width, removed if index == 0 else ()))
    pieces.append(_text(38, height - 17,
                        f"Checking all {check.inputs_checked} basis inputs · tolerance {check.tolerance:g} · Swayam Shakya", 11, MUTED))
    pieces.append('</g></svg>')
    return "".join(pieces)


def report_data(result: Optimization) -> dict:
    check = verify(result.original, result.simplified)
    return {
        "project": "CircuitTrim", "version": "1.0.0", "author": "Swayam Shakya",
        "qubits": result.original.n_qubits,
        "original": result.original.to_text(), "simplified": result.simplified.to_text(),
        "gates_before": len(result.original.gates), "gates_after": len(result.simplified.gates),
        "removed": result.removed, "reduction_percent": result.reduction_percent,
        "verification": {"equivalent": check.equivalent, "max_error": check.max_error,
                         "inputs_checked": check.inputs_checked, "tolerance": check.tolerance},
        "cancellations": [{"positions": [c.left_index + 1, c.right_index + 1], "reason": c.reason}
                          for c in result.cancellations],
        "probabilities_from_zero": {"original": probabilities(result.original),
                                    "simplified": probabilities(result.simplified)},
        "bit_order": "q(n-1)...q0; q0 is the least significant bit",
    }


def report_json(result: Optimization) -> str:
    return json.dumps(report_data(result), indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def report_fragment(result: Optimization) -> str:
    check = verify(result.original, result.simplified)
    diagram = comparison_svg(result, check)
    steps = "".join(f'<li>Positions {c.left_index+1} and {c.right_index+1}: <code>{escape(c.reason)}</code></li>'
                    for c in result.cancellations)
    if not steps:
        steps = '<li>No adjacent inverse pairs were found.</li>'
    before = probabilities(result.original)
    after = probabilities(result.simplified)
    rows = "".join(f'<tr><td><code>|{key}⟩</code></td><td>{100*value:.4f}%</td><td>{100*after[key]:.4f}%</td></tr>'
                   for key, value in before.items())
    return f'''<div class="ct-report" style="font-family:system-ui,sans-serif;color:#202434;line-height:1.6">
<div style="overflow-x:auto">{diagram}</div>
<h3>Cancellation log</h3><ol>{steps}</ol>
<p>Positions refer to the original instruction list. Later removals can expose another pair.</p>
<h3>Verification</h3><p>All {check.inputs_checked} computational basis inputs checked.
Maximum complex-amplitude difference: <code>{check.max_error:.3e}</code>.
Tolerance: <code>{check.tolerance:g}</code>. Result: <strong>{"equivalent" if check.equivalent else "different"}</strong>.</p>
<p>This compares the full operation, including phase. Matching a single probability chart would not be sufficient.</p>
<h3>Measurement probabilities from the all-zero input</h3>
<table style="border-collapse:collapse;text-align:left" cellpadding="8"><thead><tr><th>State</th><th>Original</th><th>Simplified</th></tr></thead><tbody>{rows}</tbody></table>
<p>Bit strings read q(n−1)…q0. These are calculated probabilities, not hardware measurements.</p>
<h3>Simplified instructions</h3><pre style="background:#f1f2f7;padding:16px;border-radius:10px">{escape(result.simplified.to_text() or '# Identity: no gates')}</pre>
</div>'''


def report_html(result: Optimization) -> str:
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CircuitTrim · circuit report</title>
<style>body{max-width:1200px;margin:32px auto;padding:0 20px;background:#fff}h3{margin-top:30px}td,th{border-bottom:1px solid #e5e7ee}code,pre{font-family:ui-monospace,monospace}footer{margin:36px 0;color:#697186;font:14px system-ui}@media print{body{margin:0;padding:0}.ct-report svg{max-width:100%;height:auto}}</style>
</head><body>''' + report_fragment(result) + '<footer>CircuitTrim · Swayam Shakya · MIT License</footer></body></html>'

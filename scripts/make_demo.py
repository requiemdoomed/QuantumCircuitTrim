"""Render the included walkthrough from actual optimization results."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from circuittrim import Circuit,parse_circuit,simplify,verify
from circuittrim.core import Optimization
from circuittrim.render import comparison_svg,report_html,report_json


def main():
    import cairosvg
    from PIL import Image
    import io
    assets=ROOT/'docs'/'images'
    assets.mkdir(parents=True,exist_ok=True)
    original=parse_circuit((ROOT/'examples'/'bell.ct').read_text(encoding='utf-8'),2)
    result=simplify(original)
    svg=comparison_svg(result)
    (assets/'comparison.svg').write_text(svg,encoding='utf-8')
    cairosvg.svg2png(bytestring=svg.encode(),write_to=str(assets/'comparison.png'),output_width=1272)
    (ROOT/'docs'/'demo.html').write_text(report_html(result),encoding='utf-8')
    (ROOT/'docs'/'demo.json').write_text(report_json(result),encoding='utf-8')
    frames=[]
    for count in range(len(result.cancellations)+1):
        steps=result.cancellations[:count]
        removed={i for step in steps for i in (step.left_index,step.right_index)}
        remaining=Circuit(original.n_qubits,tuple(g for i,g in enumerate(original.gates) if i not in removed))
        partial=Optimization(original,remaining,steps)
        assert verify(original,remaining).equivalent
        caption='Starting with the original circuit.' if count==0 else f'Step {count} of {len(result.cancellations)}: {steps[-1].reason}'
        drawing=comparison_svg(partial,subtitle=caption)
        png=cairosvg.svg2png(bytestring=drawing.encode(),output_width=1060)
        frames.append(Image.open(io.BytesIO(png)).convert('RGB'))
    frames[0].save(assets/'demo.gif',save_all=True,append_images=frames[1:],
                   duration=[1600]+[1500]*(len(frames)-2)+[3000],loop=0,disposal=2)
    identity=simplify(parse_circuit('H 0; X 0; X 0; H 0',1))
    identity_svg=comparison_svg(identity)
    (assets/'identity.svg').write_text(identity_svg,encoding='utf-8')
    cairosvg.svg2png(bytestring=identity_svg.encode(),write_to=str(assets/'identity.png'),output_width=1272)
    print('Rendered comparison.png, identity.png, demo.gif, SVGs, and the offline report.')


if __name__=='__main__':
    main()

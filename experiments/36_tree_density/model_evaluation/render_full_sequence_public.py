"""Render report-only SVG figures; private trajectory JSON stays local/mirror."""
from pathlib import Path
import json,html,shutil
R=Path(__file__).resolve().parents[1];D=R/'data/full-sequence';P=R/'data/full-sequence-public';P.mkdir(exist_ok=True);s=json.loads((D/'scores.json').read_text());features=['Water (kg)','Dry fuel (kg)','Gas release (kg/s)','Heating index (K)'];style='<style>body{font:16px/1.5 system-ui;background:#f4f6f8;color:#182637}main{max-width:1100px;margin:auto;padding:20px}svg{width:100%;background:white}select,button{padding:8px}a{color:#165aa5}.plots{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:12px}.case{display:none}</style>'
intro='<p><b>One initialization at t=0; all subsequent states are model-fed. No later simulation-state resets.</b> Known forcing, geometry and time intervals remain supplied. Linear axes, straight segments through all saved samples; no chart smoothing or clipping. Blue: derived simulation reference. Orange: model. Gray: simulation’s actual state at the preceding saved time (refreshed each step). This baseline receives fresh truth; the model does not.</p>'
links=' · '.join('<a href="'+m['slug']+'.html">'+html.escape(m['name'])+'</a>' for m in s['models'])
for m in s['models']:
 rows=json.loads((D/(m['slug']+'.json')).read_text())['records'];parts=['<!doctype html><meta charset="utf-8"><title>'+m['name']+' full sequence</title>'+style+'<main><h1>'+m['name']+' · full sequence</h1>'+intro+'<p><a href="index.html">Matching scorecard</a></p><p>'+links+'</p><button onclick="step(-1)">Previous</button> <select id="pick" onchange="show(+this.value)">'+''.join(f'<option value="{i}">History {q["id"]}</option>' for i,q in enumerate(rows))+'</select> <button onclick="step(1)">Next</button>']
 for i,q in enumerate(rows):
  parts.append(f'<div class="case" id="c{i}"><h2>History {q["id"]} · {i+1} / {len(rows)} · 0–{q["time"][-1]:.3f} seconds</h2><div class="plots">')
  for f in range(len(q['truth'][0])):
   arrays=[q[k] for k in ['truth','prediction','baseline']];values=[v[f] for a in arrays for v in a];lo=min(values);hi=max(values);pad=(hi-lo or 1)*.06;lo-=pad;hi+=pad
   parts.append(f'<section><h3>{features[f]}</h3><svg viewBox="0 0 540 240" role="img" aria-label="{features[f]} full continuous trajectory"><text x="3" y="30">{hi:.3g}</text><text x="3" y="195">{lo:.3g}</text><text x="70" y="225">0 s</text><text x="465" y="225">180 s</text>')
   for a,color in zip(arrays,['#1766b5','#d66610','#888']):
    path=' '.join(('M' if j==0 else 'L')+f'{70+440*q["time"][j]/q["time"][-1]:.6f},{195-165*(v[f]-lo)/(hi-lo):.6f}' for j,v in enumerate(a));parts.append(f'<path d="{path}" stroke="{color}" fill="none" stroke-width="1.4"/>')
   parts.append('</svg></section>')
  parts.append('</div></div>')
 parts.append('<p>Simulation values are derived/resampled FDS quantities, not physical validation. Different models can have different test populations; see scorecard. Heating is an index in K, not energy. Gas is fuel-gas release, not heat release.</p></main><script>let current=0;const total='+str(len(rows))+';function show(i){document.getElementById("c"+current).style.display="none";current=i;document.getElementById("c"+current).style.display="block";document.getElementById("pick").value=current}function step(d){show((current+d+total)%total)}show(0)</script>');(P/(m['slug']+'.html')).write_text(''.join(parts))
(P/'gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>Full-sequence galleries</title>'+style+'<main><h1>Full-sequence visual comparisons</h1>'+intro+'<p><a href="index.html">Matching simplified scorecard</a></p>'+''.join('<p><a href="'+m['slug']+'.html">'+html.escape(m['name'])+'</a> — '+str(m['histories'])+' held-out histories</p>' for m in s['models'])+'</main>')
for name in ['index.html','scores.json','historical-scores.json']:shutil.copyfile(D/name,P/name)
print('Rendered figures only:',len(list(P.iterdir())),'files; trajectory data excluded')

"""Overlay matched previous autonomous gated predictions, with common axes."""
from pathlib import Path
import json,re,math,hashlib
import numpy as np
R=Path(__file__).resolve().parent;D=R/'data/prior-overlay';D.mkdir(exist_ok=True)
original=(R/'data/scorecard-addition/integral-gated.html').read_text()
newrecords=json.loads((R/'data/analysis/integral-comparison.json').read_text())['records']
oldrecords=json.loads((R.parent/'36_tree_density/data/full-sequence/stridegated.json').read_text())['records']
prior={q['id']:q for q in oldrecords};current={q['id']:q for q in newrecords};assert set(prior)==set(current)
prefix,rest=original.split(',content=',1);payload,tail=rest.split(';let page=',1);pages=json.loads(payload)
colors=['#159447','#9854bc','#1878c8','#e67e13']
for page in pages:
 for row in page:
  q=current[row['info']['index']];old=prior[q['id']]
  assert np.array_equal(old['time'],q['time']) and np.allclose(old['truth'],q['truth'],rtol=0,atol=0)
  charts=[]
  for f,chart in enumerate(re.findall(r'<div class="chart">.*?</svg></div>',row['charts'])):
   threshold=[.001,.01,.00001,.1][f]
   def T(v):return math.copysign(math.log10(1+abs(v)/threshold),v)
   truth=q['truth'];arrays=[truth,[truth[0]]+truth[:-1],q['prediction'],old['prediction']]
   allv=[T(v[f]) for a in arrays for v in a];lo=min(allv);hi=max(allv);pad=(hi-lo or 1)*.08;lo-=pad;hi+=pad
   out=chart.split('<svg',1)[0]+'<svg viewBox="0 0 280 175">'
   for j in range(5):
    z=lo+(hi-lo)*j/4;v=math.copysign(threshold*(10**abs(z)-1),z);out+=f'<text x="47" y="{142-j*30}" text-anchor="end" font-size="8" fill="#627082">{v:.3g}</text>'
   for t in [0,60,120,180]:out+=f'<text x="{51+t/180*220}" y="154" text-anchor="middle" font-size="9" fill="#627082">{t}</text>'
   out+='<text x="161" y="169" text-anchor="middle" font-size="9" fill="#627082">Target time (s)</text>'
   for series,a in enumerate(arrays):
    path=' '.join(('M' if j==0 else 'L')+f'{51+q["time"][j]/180*220:.6f},{139-(T(v[f])-lo)/(hi-lo)*120:.6f}' for j,v in enumerate(a));out+=f'<path data-series="{series}" d="{path}" fill="none" stroke="{colors[series]}" stroke-width=".9"/>'
   charts.append(out+'</svg></div>')
  row['charts']=''.join(charts)
new=prefix+',content='+json.dumps(pages,separators=(',',':'))+';let page='+tail
new=new.replace('visible=[true,false,true]','visible=[true,false,true,true]')
new=new.replace('</div><main id="rows">','<button data-series="3" aria-pressed="true" style="color:#e67e13">Previous stride-one gated · split 0</button></div><main id="rows">',1)
new=new.replace('Boxes: whole-sequence','Blue: new integral-loss model; orange: previous stride-one gated model. Boxes score the new blue model. Both models share the same simulation and timestamps; axes include both curves. Boxes: whole-sequence',1)
assert new[new.index('function info(d)'):]==original[original.index('function info(d)'):]
assert re.findall(r'<style>.*?</style>',new,re.S)==re.findall(r'<style>.*?</style>',original,re.S)
assert sum(row['charts'].count('data-series="3"') for p in pages for row in p)==832
(D/'integral-gated.html').write_text(new)
(R/'results/prior-overlay-build.json').write_text(json.dumps(dict(passed=True,histories=208,prior_curves=832,truth_times_identical=True,controls_rubric_css_preserved=True,common_axes_include_all_series=True,sha256=hashlib.sha256(new.encode()).hexdigest()),indent=2)+'\n')
print('Verified 832 previous-model curves, matched truth/timestamps; CSS, controls and rubric preserved')

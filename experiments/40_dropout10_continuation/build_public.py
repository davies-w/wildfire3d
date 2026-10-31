"""New additive comparison pages; preserve old pages and exact gallery controls/rubric."""
from pathlib import Path
import json,re,math,html,hashlib
import numpy as np
R=Path(__file__).resolve().parent;OLD=R.parent/'36_tree_density';D=R/'data/public';D.mkdir(exist_ok=True)
r=json.loads((R/'data/analysis/integral-comparison.json').read_text());records=r['records'];byid={q['id']:q for q in records};assert len(byid)==208
original=(OLD/'data/stride-integral/stridegated.html').read_text();prefix,rest=original.split(',content=',1);payload,tail=rest.split(';let page=',1);pages=json.loads(payload)
schema=json.loads((R/'data/training02/schema.json').read_text())
rows=[]
for q in records:
 c=schema['cases'][q['id']];h,m,l,w,angle=c['physical_key']
 rows.append({'info':dict(index=q['id'],case=c['case'],fold=c['fold'],height=h,loading=l,wind=w,angle=angle,water=q['truth'][0][0],fuel=q['truth'][0][1]),'charts':''})
pages=[rows[i:i+3] for i in range(0,len(rows),3)]
prefix=prefix.replace('total=208','total=208')
colors=['#159447','#9854bc','#1878c8'];titles=['Water · kg','Dry fuel · kg','Fuel gas · kg/s','Heating index · K']
for page in pages:
 for row in page:
  q=byid[row['info']['index']];truth=q['truth'];prediction=q['prediction'];baseline=[truth[0]]+truth[:-1];charts=[]
  for f in range(4):
   threshold=[.001,.01,.00001,.1][f]
   def T(v):return math.copysign(math.log10(1+abs(v)/threshold),v)
   arrays=[truth,baseline,prediction];allv=[T(v[f]) for a in arrays for v in a];lo=min(allv);hi=max(allv);pad=(hi-lo or 1)*.08;lo-=pad;hi+=pad
   out='<div class="chart"><h3>'+titles[f]+' <span class="integral-badge" title="Whole-sequence integral of absolute physical error / (duration × simulation range)">'+f'{q["percent"][f]:.2f}%</span></h3><svg viewBox="0 0 280 175">'
   for j in range(5):
    z=lo+(hi-lo)*j/4;v=math.copysign(threshold*(10**abs(z)-1),z);out+=f'<text x="47" y="{142-j*30}" text-anchor="end" font-size="8" fill="#627082">{v:.3g}</text>'
   for t in [0,60,120,180]:out+=f'<text x="{51+t/180*220}" y="154" text-anchor="middle" font-size="9" fill="#627082">{t}</text>'
   out+='<text x="161" y="169" text-anchor="middle" font-size="9" fill="#627082">Target time (s)</text>'
   for series,a in enumerate(arrays):
    path=' '.join(('M' if j==0 else 'L')+f'{51+q["time"][j]/180*220:.6f},{139-(T(v[f])-lo)/(hi-lo)*120:.6f}' for j,v in enumerate(a));out+=f'<path data-series="{series}" d="{path}" fill="none" stroke="{colors[series]}" stroke-width=".9"/>'
   charts.append(out+'</svg></div>')
  row['charts']=''.join(charts)
new=prefix+',content='+json.dumps(pages,separators=(',',':'))+';let page='+tail
new=new.replace('Stride-one gated · split 0','10% dropout continuation · rotation 0')
new=new.replace('Continuous full-sequence predictions', 'Eight prior four-state samples, one 64-unit GRU, shared Linear64→64 + SiLU, four delta and three gate heads (25,159 parameters). Continuation from selected experiment39 epoch159, full90-step training with10% dropout after shared SiLU before both delta/gate heads. Dropout is disabled for evaluation. One origin per history and seven updates per epoch. Parent epochs160–189 are a separate branch. Selected model is the inherited experiment39 epoch159 checkpoint: none of the dropout checkpoints improved validation. The displayed predictions therefore equal the parent model. Same rotation-0 split; historically examined data. Continuous full-sequence predictions')
assert original[original.index('function info(d)'):]==new[new.index('function info(d)'):],'Controls/rubric JS changed'
assert re.findall(r'<style>(.*?)</style>',original,re.S)==re.findall(r'<style>(.*?)</style>',new,re.S)
assert len(pages)==70 and all(len(p)==3 for p in pages[:-1]) and len(pages[-1])==1
(D/'gated.html').write_text(new)

proof=dict(passed=True,history_count=208,pages=70,charts_per_row=4,rows_per_page=3,original_controls_css_rubric_preserved=True)
(R/'results02/public-build.json').write_text(json.dumps(proof,indent=2)+'\n')

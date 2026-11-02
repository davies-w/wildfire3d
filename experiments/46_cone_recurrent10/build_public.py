"""New additive comparison pages; preserve old pages and exact gallery controls/rubric."""
from pathlib import Path
import json,re,math,html,hashlib
import numpy as np
R=Path(__file__).resolve().parent;OLD=R.parent/'36_tree_density';D=R/'data/public';D.mkdir(exist_ok=True)
r=json.loads((R/'data/analysis/integral-comparison.json').read_text());records=r['records'];byid={q['id']:q for q in records};assert len(byid)==208
original=(OLD/'data/stride-integral/stridegated.html').read_text();prefix,rest=original.split(',content=',1);payload,tail=rest.split(';let page=',1);pages=json.loads(payload)
schema=json.loads((R/'data/training03/schema.json').read_text())
cones=np.load(R/'data/training03/data/cones.npz');forecasts=np.load(R/'data/pool03-results/fold00-test-predictions.npz');prediction_index={int(v):i for i,v in enumerate(forecasts['case_indices'])}
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
   out=out.replace('data-series="2"','data-series="2" stroke-dasharray="3 2"')
   charts.append(out+'</svg></div>')
  n=row['info']['index'];idx=prediction_index[n];truthcone=cones['parameters'][n,1:];predcone=forecasts['cone_parameters'][idx];tm=cones['active'][n,1:];pm=forecasts['cone_presence_probability'][idx]>=.5
  lengths=np.concatenate([truthcone[tm,2],predcone[pm,2]]);temps=np.concatenate([truthcone[tm,4],predcone[pm,4]])
  lmax=max(1.,float(lengths.max()) if len(lengths) else 1.);tmax=max(1.,float(temps.max()) if len(temps) else 1.)
  out='<div class="chart"><h3>Cone length / peak °C</h3><svg viewBox="0 0 280 175">'
  for j in range(5):
   out+=f'<text x="37" y="{142-j*30}" text-anchor="end" font-size="8" fill="#2563eb">{lmax*j/4:.2g}m</text><text x="247" y="{142-j*30}" font-size="8" fill="#dc2626">{tmax*j/4:.3g}°</text>'
  for t in [0,60,120,180]:out+=f'<text x="{42+t/180*200}" y="154" text-anchor="middle" font-size="9">{t}</text>'
  for arr,mask,series,dash in [(truthcone,tm,0,''),(predcone,pm,2,' stroke-dasharray="3 2"')]:
   for f,maxv,color in [(2,lmax,'#2563eb'),(4,tmax,'#dc2626')]:
    path='';connected=False
    for j,value in enumerate(arr[:,f]):
     if not mask[j]:connected=False;continue
     path+=(' L' if connected else ' M')+f'{42+q["time"][j+1]/180*200:.4f},{139-value/maxv*120:.4f}';connected=True
    out+=f'<path data-series="{series}" d="{path}" fill="none" stroke="{color}" stroke-width="1"{dash}/>'
  charts.append(out+'</svg><small>Blue: metres · red: °C. Solid reference; dashed prediction; gaps: absent (p&lt;0.5).</small></div>')
  row['charts']=''.join(charts)
new=prefix+',content='+json.dumps(pages,separators=(',',':'))+';let page='+tail
new=new.replace('Stride-one gated · split 0','Ten-value recurrent cone GRU64 · rotation 0')
new=new.replace('Continuous full-sequence predictions', 'Eight prior ten-value states, one 64-unit GRU, shared Linear64→64 + SiLU, four delta, three internal gate and six cone outputs (34,765 parameters). Fresh seed3516 training from epoch1 with one GRU64 with ten-value history and no dropout. All ten predictions are fed back. Curriculum1/8/16/32/64/full90 at epochs1/21/41/61/110/130. Full90 has one origin/history and seven updates/epoch. Same historically examined rotation0 population; not pristine confirmation, independent-seed replication or isolated hardware comparison. Continuous full-sequence predictions')
assert original[original.index('function info(d)'):]==new[new.index('function info(d)'):],'Controls/rubric JS changed'
assert re.findall(r'<style>(.*?)</style>',original,re.S)==re.findall(r'<style>(.*?)</style>',new,re.S)
new=new.replace('repeat(4,minmax(0,1fr))','repeat(5,minmax(0,1fr))')
assert len(pages)==70 and all(len(p)==3 for p in pages[:-1]) and len(pages[-1])==1
(D/'gated.html').write_text(new)

proof=dict(passed=True,history_count=208,pages=70,charts_per_row=5,rows_per_page=3,original_controls_rubric_preserved=True,only_grid_extended_to_five=True)
(R/'results03/public-build.json').write_text(json.dumps(proof,indent=2)+'\n')

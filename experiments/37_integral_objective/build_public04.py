"""New additive comparison pages; preserve old pages and exact gallery controls/rubric."""
from pathlib import Path
import json,re,math,html,hashlib
import numpy as np
R=Path(__file__).resolve().parent;OLD=R.parent/'36_tree_density';D=R/'data/public04';D.mkdir(exist_ok=True)
r=json.loads((R/'data/analysis04/integral-comparison.json').read_text());records=r['records'];byid={q['id']:q for q in records};assert len(byid)==210
original=(OLD/'data/stride-integral/stridegated.html').read_text();prefix,rest=original.split(',content=',1);payload,tail=rest.split(';let page=',1);pages=json.loads(payload)
schema=json.loads((R/'data/training04/schema.json').read_text())
rows=[]
for q in records:
 c=schema['cases'][q['id']];h,m,l,w,angle=c['physical_key']
 rows.append({'info':dict(index=q['id'],case=c['case'],fold=c['fold'],height=h,loading=l,wind=w,angle=angle,water=q['truth'][0][0],fuel=q['truth'][0][1]),'charts':''})
pages=[rows[i:i+3] for i in range(0,len(rows),3)]
prefix=prefix.replace('total=208','total=210')
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
new=new.replace('Stride-one gated · split 0','Integral-loss gated · split 1')
assert original[original.index('function info(d)'):]==new[new.index('function info(d)'):],'Controls/rubric JS changed'
assert re.findall(r'<style>(.*?)</style>',original,re.S)==re.findall(r'<style>(.*?)</style>',new,re.S)
assert len(pages)==70 and all(len(p)==3 for p in pages[:-1]) and len(pages[-1])==3
(D/'gated.html').write_text(new)
# New scorecard retains all existing cells and adds the new model's columns.
card=(OLD/'data/stride-integral/index.html').read_text();seq=np.load(R/'data/training04/data/sequences.npz');ids=np.array([q['id'] for q in records]);pred=np.array([q['prediction'] for q in records])[:,1:];truth=np.array([q['truth'] for q in records])[:,1:];base=seq['state'][ids,:-1];labels=seq['activity_labels'][ids];config=seq['configuration'][ids]
phases={}
for name,mask in [('all',np.ones(labels.shape,bool)),('active',np.isin(labels,[1,2])),('quiet',labels==0),('weak',labels==3)]:
 count=mask.sum(1);keep=count>0;vals=[]
 for a in [abs(pred-truth),abs(base-truth),abs(truth)]:
  per=np.where(mask[:,:,None],a,0).sum(1)[keep]/count[keep,None];c=config[keep];vals.append(np.stack([per[c==v].mean(0) for v in np.unique(c)]).mean(0))
 m,b,t=vals
 with np.errstate(divide='ignore',invalid='ignore'):err=100*m/t;improve=100*(1-m/b)
 phases[name]=dict(error=err,improvement=improve)
def pct(v):return f'{v:.2f}%' if np.isfinite(v) else 'Undefined'
def section(match):
 s=match[0]
 if 'Stride-one gated' not in s:return s
 name=next(k for k in phases if '<h2>'+k.title()+' periods</h2>' in s)
 s=s.replace('</tr><tr>','<th colspan="3" class="group g8">Integral-loss gated · split 1</th></tr><tr>',1)
 s=s.replace('</tr></thead>','<th class="g8">Error vs sim ↓</th><th class="g8">Improvement vs<br>no change ↑</th><th class="g8">Integral error ↓<br>Whole sequence</th></tr></thead>',1)
 f=iter(range(4))
 def row(m):
  i=next(f);return m[0][:-5]+''.join('<td class="new-rotation1-model">'+pct(v)+'</td>' for v in [phases[name]['error'][i],phases[name]['improvement'][i],r['aggregate_percent'][i]])+'</tr>'
 return re.sub(r'<tr><th>(?:Water \(kg\)|Dry fuel \(kg\)|Gas release \(kg/s\)|Heating index \(K\)).*?</tr>',row,s)
newcard=re.sub(r'<section>.*?</section>',section,card,flags=re.S)
assert newcard.count('class="new-rotation1-model"')==48
# Verify every old table cell occurs in the same order after removal of additions.
clean=re.sub(r'<td class="new-rotation1-model">.*?</td>','',newcard)
assert re.findall(r'<td.*?</td>',clean,re.S)==re.findall(r'<td.*?</td>',card,re.S)
newcard=newcard.replace('Quiet percentages rounded to one significant digit.','Previous quiet percentages use one significant digit; new-model columns show two decimals.').replace('Whole percentages.','Previous columns use whole percentages; new-model columns show two decimals.')
newcard=newcard.replace('</style>','.g8{background:#e5f5e8}</style>',1).replace('<h1>Full-sequence simplified scorecard</h1>','<h1>Integral-objective comparison</h1><p><a href="gated.html">New model gallery · 210 histories</a> · <a href="../full-sequence/stridegated.html">Previous gated gallery</a> · <a href="../full-sequence/index.html">Original scorecard (unchanged)</a></p><p>New model: frozen rotation1, 210 held-out histories / 204 configurations. Same recipe and seed as rotation0; different test population, not a matched comparison or independent-seed repeat. Previously examined dataset. Integral column uses whole-sequence values in every section, matching graph boxes.</p>',1)
newcard=newcard.replace('href="gallery.html"','href="gated.html"').replace('href="historical-scores.json"','href="../full-sequence/historical-scores.json"').replace('href="scores.json"','href="integral-comparison.json"')
(D/'index.html').write_text(newcard);(D/'integral-comparison.json').write_bytes((R/'data/analysis04/integral-comparison.json').read_bytes())
proof=dict(passed=True,history_count=210,pages=70,charts_per_row=4,rows_per_page=3,integral_badges=840,original_controls_css_rubric_preserved=True,old_table_cells_unchanged=True,original_pages_not_modified=True,files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.is_file()})
(R/'results04/public-build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

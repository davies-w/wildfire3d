"""Append rotation3 only to the integral summary and add matching gallery."""
from pathlib import Path
import json,re,hashlib,numpy as np
from huggingface_hub import HfApi,hf_hub_download
R=Path(__file__).resolve().parent;D=R/'data/scorecard-addition06';D.mkdir(exist_ok=True)
assert json.loads((R/'results/training06-collected.json').read_text())['passed']
api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
for n in ['index.html','gallery.html']:(D/('full-sequence__'+n)).write_bytes(Path(hf_hub_download(repo,'full-sequence/'+n,repo_type='space',revision=rev)).read_bytes())
old=(D/'full-sequence__index.html').read_text();assert 'integral-gated-r3.html' not in old
r=json.loads((R/'data/analysis06/integral-comparison.json').read_text());records=r['records'];a=np.load(R/'data/training06/data/sequences.npz');ids=np.array([q['id'] for q in records]);pred=np.array([q['prediction'] for q in records])[:,1:];truth=np.array([q['truth'] for q in records])[:,1:];labels=a['activity_labels'][ids];cfg=a['configuration'][ids]
phases={}
for name,mask in [('active',np.isin(labels,[1,2])),('quiet',labels==0)]:
 count=mask.sum(1);keep=count>0;vals=[]
 for x in [abs(pred-truth),abs(truth)]:
  per=np.where(mask[:,:,None],x,0).sum(1)[keep]/count[keep,None];c=cfg[keep];vals.append(np.stack([per[c==v].mean(0) for v in np.unique(c)]).mean(0))
 with np.errstate(divide='ignore',invalid='ignore'):phases[name]=(100*vals[0]/vals[1]).tolist()
def pct(v):return f'{v:.2f}%' if np.isfinite(v) else 'Undefined'
m=re.search(r'<section id="integral-objective-summary">.*?</section>',old,re.S);assert m
s=m[0];s=s.replace('</tr><tr>','<th colspan="3" class="group g8"><a href="integral-gated-r3.html">Rotation 3 · Spot T4</a> · 208 test histories</th></tr><tr>',1)
s=s.replace('</tr></thead>','<th class="g8">Integral error ↓<br>Whole sequence</th><th class="g8">Error vs sim ↓<br>Active</th><th class="g8">Error vs sim ↓<br>Quiet</th></tr></thead>',1)
i=iter(range(4))
def row(m):
 f=next(i);return m[0][:-5]+''.join('<td class="rotation3">'+pct(v)+'</td>' for v in [r['aggregate_percent'][f],phases['active'][f],phases['quiet'][f]])+'</tr>'
s=re.sub(r'<tr><th>(?:Water \(kg\)|Dry fuel \(kg\)|Gas release \(kg/s\)|Heating index \(K\)).*?</tr>',row,s)
new=old[:m.start()]+s+old[m.end():];assert new.count('class="rotation3"')==12
assert re.findall(r'<td.*?</td>',re.sub(r'<td class="rotation3">.*?</td>','',new),re.S)==re.findall(r'<td.*?</td>',old,re.S)
assert new[m.start()+len(s):]==old[m.end():]
(D/'index.html').write_text(new);(D/'integral-gated-r3.html').write_bytes((R/'data/public06/gated.html').read_bytes())
menu=(D/'full-sequence__gallery.html').read_text();assert '</main>' in menu
(D/'gallery.html').write_text(menu.replace('</main>','<p><a href="integral-gated-r3.html">Integral-loss gated · split 3 · Spot T4</a> — 208 held-out histories; same three-row, four-chart layout, toggles, rubric and integral boxes. Symlog axes; different test split.</p></main>'))
(R/'results06/scorecard-parent.json').write_text(json.dumps({'revision':rev},indent=2))
(R/'results06/scorecard-build.json').write_text(json.dumps({'passed':True,'prior_cells_preserved':True,'only_top_table_changed':True,'phase_errors':phases,'histories':208,'pages':70},indent=2))
print(json.dumps(phases))

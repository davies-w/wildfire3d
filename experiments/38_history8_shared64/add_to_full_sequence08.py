"""Append history8shared64 only to the integral summary and add matching gallery."""
from pathlib import Path
import json,re,hashlib,numpy as np
from huggingface_hub import HfApi,hf_hub_download
R=Path(__file__).resolve().parent;D=R/'data/scorecard-addition08';D.mkdir(exist_ok=True)
assert json.loads((R/'results/training08-collected.json').read_text())['passed']
api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
for n in ['index.html','gallery.html']:(D/('full-sequence__'+n)).write_bytes(Path(hf_hub_download(repo,'full-sequence/'+n,repo_type='space',revision=rev)).read_bytes())
old=(D/'full-sequence__index.html').read_text();assert 'history8-shared64-r0.html' not in old
r=json.loads((R/'data/analysis08/integral-comparison.json').read_text());records=r['records'];a=np.load(R/'data/training08/data/sequences.npz');ids=np.array([q['id'] for q in records]);pred=np.array([q['prediction'] for q in records])[:,1:];truth=np.array([q['truth'] for q in records])[:,1:];labels=a['activity_labels'][ids];cfg=a['configuration'][ids]
phases={}
for name,mask in [('active',np.isin(labels,[1,2])),('quiet',labels==0)]:
 count=mask.sum(1);keep=count>0;vals=[]
 for x in [abs(pred-truth),abs(truth)]:
  per=np.where(mask[:,:,None],x,0).sum(1)[keep]/count[keep,None];c=cfg[keep];vals.append(np.stack([per[c==v].mean(0) for v in np.unique(c)]).mean(0))
 with np.errstate(divide='ignore',invalid='ignore'):phases[name]=(100*vals[0]/vals[1]).tolist()
def pct(v):return f'{v:.2f}%' if np.isfinite(v) else 'Undefined'
m=re.search(r'<section id="integral-objective-summary">.*?</section>',old,re.S);assert m
s=m[0];s=s.replace('</tr><tr>','<th colspan="3" class="group g8"><a href="history8-shared64-r0.html">Rotation 0 · History8 / GRU64 / shared64</a> · 208 test histories</th></tr><tr>',1)
s=s.replace('</tr></thead>','<th class="g8">Integral error ↓<br>Whole sequence</th><th class="g8">Error vs sim ↓<br>Active</th><th class="g8">Error vs sim ↓<br>Quiet</th></tr></thead>',1)
i=iter(range(4))
def row(m):
 f=next(i);return m[0][:-5]+''.join('<td class="history8shared64">'+pct(v)+'</td>' for v in [r['aggregate_percent'][f],phases['active'][f],phases['quiet'][f]])+'</tr>'
s=re.sub(r'<tr><th>(?:Water \(kg\)|Dry fuel \(kg\)|Gas release \(kg/s\)|Heating index \(K\)).*?</tr>',row,s)
s=s.replace('Same architecture, recipe and seed; different held-out populations, so these rotations are not matched model comparisons or independent-seed repeats.', 'Original integral-model rotations share architecture, recipe and seed but use different held-out populations. The new History8 / GRU64 / shared64 model is matched to original rotation 0: eight prior states, one 64-unit GRU and a shared 64-unit SiLU layer. It combines three architecture changes; their individual effects are not isolated. Hardware and interruptions also differ. These are not independent-seed repeats.')
new=old[:m.start()]+s+old[m.end():];assert new.count('class="history8shared64"')==12
assert re.findall(r'<td.*?</td>',re.sub(r'<td class="history8shared64">.*?</td>','',new),re.S)==re.findall(r'<td.*?</td>',old,re.S)
assert new[m.start()+len(s):]==old[m.end():]

(D/'index.html').write_text(new);(D/'history8-shared64-r0.html').write_bytes((R/'data/public08/gated.html').read_bytes())
menu=(D/'full-sequence__gallery.html').read_text();assert '</main>' in menu
(D/'gallery.html').write_text(menu.replace('</main>','<p><a href="history8-shared64-r0.html">History8 GRU64 + shared64 · rotation 0 · Spot T4</a> — 208 held-out histories; same three-row, four-chart layout, toggles, rubric and integral boxes. Symlog axes; matched rotation-0 test split; combined architecture changes, not an isolated hardware comparison.</p></main>'))
(R/'results08/scorecard-parent.json').write_text(json.dumps({'revision':rev},indent=2))
(R/'results08/scorecard-build.json').write_text(json.dumps({'passed':True,'prior_cells_preserved':True,'only_top_table_changed':True,'phase_errors':phases,'histories':208,'pages':70},indent=2))
print(json.dumps(phases))

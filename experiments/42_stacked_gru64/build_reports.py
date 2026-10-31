"""Add completed42 report and gallery, preserving every previous page/cell."""
from pathlib import Path
import json,re,hashlib,subprocess,sys
import numpy as np
from huggingface_hub import HfApi,hf_hub_download
R=Path(__file__).resolve().parent;D=R/'data/report-public';D.mkdir(exist_ok=True)
api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
old={n:Path(hf_hub_download(repo,n,repo_type='space',revision=rev)).read_text() for n in ['index.html','full-sequence/index.html','full-sequence/gallery.html']}
for n,s in old.items():(D/('parent-'+n.replace('/','__'))).write_text(s)
def readable(s):
 parts=re.split(r'(<[^>]+>)',s)
 for i in range(0,len(parts),2):
  t=parts[i];t=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',t);t=re.sub(r'([:;,])(?=[A-Za-z])',r'\1 ',t);t=re.sub(r':(?=\d)',': ',t);parts[i]=t
 return ''.join(parts)
models=[]
for number,folder,slug,label in [(42,'42_stacked_gru64','stacked42','Two recurrent GRU64 layers')]:
 r=R.parent/folder;proof=json.loads((r/'results03/collected.json').read_text());assert proof['passed'];a=json.loads((r/'data/analysis/integral-comparison.json').read_text());records=a['records'];data=np.load(r/'data/training03/data/sequences.npz');ids=np.array([q['id'] for q in records]);pred=np.array([q['prediction'] for q in records])[:,1:];truth=np.array([q['truth'] for q in records])[:,1:];labels=data['activity_labels'][ids];cfg=data['configuration'][ids];phases={}
 for name,mask in [('active',np.isin(labels,[1,2])),('quiet',labels==0)]:
  count=mask.sum(1);keep=count>0;vals=[]
  for x in [abs(pred-truth),abs(truth)]:
   per=np.where(mask[:,:,None],x,0).sum(1)[keep]/count[keep,None];c=cfg[keep];vals.append(np.stack([per[c==v].mean(0) for v in np.unique(c)]).mean(0))
  with np.errstate(divide='ignore',invalid='ignore'):phases[name]=(100*vals[0]/vals[1]).tolist()
 models.append(dict(number=number,folder=folder,slug=slug,label=label,analysis=a,phases=phases,epochs=proof['epochs'],selected=proof['selected_epoch']))
 fs=D/'full-sequence';fs.mkdir(exist_ok=True);(fs/(slug+'-r0.html')).write_bytes((r/'data/public/gated.html').read_bytes());(fs/(slug+'-r0-values.json')).write_bytes((r/'data/analysis/integral-comparison.json').read_bytes())
 doc=D/slug;doc.mkdir(exist_ok=True);subprocess.run([sys.executable,str(r/'plot_learning_curve.py'),'--output',str(doc/'learning-curve.png')],check=True)
prior39=json.loads((R.parent/'39_long_window_continuation/data/analysis/integral-comparison.json').read_text());prior40=json.loads((R.parent/'40_dropout10_continuation/data/analysis/integral-comparison.json').read_text())
prior41=json.loads((R.parent/'41_dropout10_from_start/data/analysis/integral-comparison.json').read_text())
base38=json.loads((R.parent/'38_history8_shared64/data/analysis08/integral-comparison.json').read_text())
# Match identities and simulation values across all model comparisons.
for m in models:
 for prior in [base38,prior39,prior40,prior41]:
  assert len(prior['records'])==208
  for q,b in zip(m['analysis']['records'],prior['records']):assert q['id']==b['id'] and q['truth']==b['truth'] and q['time']==b['time']
score=old['full-sequence/index.html'];match=re.search(r'<section id="integral-objective-summary">.*?</section>',score,re.S);assert match;s=match[0]
def pct(v):return f'{v:.2f}%' if np.isfinite(v) else 'Undefined'
for m in models:
 slug=m['slug'];assert slug+'-r0.html' not in score
 s=s.replace('</tr><tr>',f'<th colspan="3" class="group g8"><a href="{slug}-r0.html">Rotation 0 · {m["label"]}</a> · selected epoch {m["selected"]}</th></tr><tr>',1)
 s=s.replace('</tr></thead>','<th class="g8">Integral error ↓<br>Whole sequence</th><th class="g8">Error vs sim ↓<br>Active</th><th class="g8">Error vs sim ↓<br>Quiet</th></tr></thead>',1)
 it=iter(range(4))
 def row(hit):
  f=next(it);return hit[0][:-5]+''.join(f'<td class="{slug}">'+pct(v)+'</td>' for v in [m['analysis']['aggregate_percent'][f],m['phases']['active'][f],m['phases']['quiet'][f]])+'</tr>'
 s=re.sub(r'<tr><th>(?:Water \(kg\)|Dry fuel \(kg\)|Gas release \(kg/s\)|Heating index \(K\)).*?</tr>',row,s)
s=s.replace('</section>','<p>Fresh seed3516 training with two recurrent GRU64 layers and no dropout, continued from epoch30 after a verified Spot preemption. Curriculum1/8/16/32/64/full90 at epochs1/21/41/61/110/130. Full90 has one origin/history and seven updates/epoch. Same historically examined rotation0 population; not pristine confirmation, independent-seed replication or isolated hardware comparison.</p></section>')
new=score[:match.start()]+s+score[match.end():]
stripped=re.sub(r'<td class="(?:stacked42)">.*?</td>','',new)
assert re.findall(r'<td.*?</td>',stripped,re.S)==re.findall(r'<td.*?</td>',score,re.S)
assert new[match.start()+len(s):]==score[match.end():]
(D/'full-sequence/index.html').write_text(new)
menu=old['full-sequence/gallery.html'];links=''.join(f'<p><a href="{m["slug"]}-r0.html">{m["label"]} · rotation0 · selected epoch{m["selected"]}</a> —208 histories, three cases/page, four plots/row; matching controls and rubric.</p>' for m in models);assert '</main>' in menu;(D/'full-sequence/gallery.html').write_text(menu.replace('</main>',links+'</main>',1))
css='body{font:17px/1.6 system-ui;color:#182637;background:#f3f5f8;margin:0}main{max-width:1100px;margin:auto;padding:32px 24px}h1{font-size:38px;line-height:1.2}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;text-align:left;border-bottom:1px solid #dce3eb}img{width:100%}a{color:#205bb0}@media(max-width:600px){table{font-size:12px}th,td{padding:6px}}'
features=['Water (kg)','Dry fuel (kg)','Fuel gas (kg/s)','Heating index (K)'];rows=''.join('<tr><th>'+name+'</th>'+''.join('<td>'+pct(v)+'</td>' for v in [base38['prior_aggregate_percent'][i],base38['aggregate_percent'][i],prior39['aggregate_percent'][i],prior40['aggregate_percent'][i],prior41['aggregate_percent'][i],models[0]['analysis']['aggregate_percent'][i]])+'</tr>' for i,name in enumerate(features))
limits='The source simulations use simplified conical vegetation crowns (approximately3m crown diameter above a2m base, categorical total heights4/6/8/10m),1,600 weighted vegetation particles and0.5m mesh. Ignition is imposed at1,500°C for20seconds. No buildings or embers are modeled. This does not validate realistic trees, property-scale fire, a new physical ignition criterion or material behavior. Gas is vegetation fuel-gas release, not combustion heat; heating is a surface-heating index in kelvin, not stored energy. Gallery schematics are categorical renderer encodings, not validated species or proportional fuel distributions.'
for m in models:
 result=f"Training completed {m['epochs']} epochs and selected epoch {m['selected']} by validation before test evaluation. Selected validation error was4.322010%. Matched test errors are worse than experiment39 for water, dry fuel and gas, but better for heating. The second recurrent layer did not produce a uniform improvement."
 change="Fresh seed3516 weights and empty AdamW, two GRU64 recurrent layers, and no dropout. Window curriculum1/8/16/32/64/full90 at epochs1/21/41/61/110/130, minimum160/maximum400/patience30. Both recurrent states are carried and both teacher-prefix states are detached without future truth. This differs from experiment39 checkpoint continuation, so the comparison does not isolate recurrent depth alone."
 recovery="Pool01 failed before epoch1 because cuDNN required contiguous hidden-state inputs. Pool02 fixed only tensor layout, passed all seven startup proofs, and completed30 epochs before confirmed Spot preemption in Iowa. Pool03 resumed epoch31 on Oregon with identical model, data and optimizer recipe; exact restored first-batch optimizer/RNG replay passed. All seven proofs passed; the original epoch1 proof was inherited. No completed epoch was retrained."
 body=f'<nav><a href="../index.html">All reports</a> · <a href="../full-sequence/index.html">Scorecard</a> · <a href="../full-sequence/{m["slug"]}-r0.html">208-history gallery</a></nav><h1>{m["label"]}</h1><p>Experiment{m["number"]} · rotation0 · completed31October2026 · selected epoch{m["selected"]}</p><p><strong>{result}</strong></p><h2>Changes and preserved recipe</h2><p>{change}</p><p>History8 four-state samples plus9 external inputs, two64-unit recurrent GRU layers, shared64 SiLU, four-delta/three-gate heads:50,119 parameters. Both recurrent memories have64 units; the combined hidden tensor is [2,batch,64]. The dense layer has no recurrent memory. Split:1,662 training,210 validation,208 test histories representing204 test configurations. Same seed3516, integral loss plus gate BCE0.1, AdamW LR0.0003, weight decay0.0001, clip1, batch256. Water/fuel gates scale changes; gas gate scales candidate gas output; heating is ungated.</p><p>Full90-step training has one window per history and7 optimizer updates/epoch. At64steps there are27 origins/history and176 updates/epoch. This changes both gradient horizon and update exposure. Full-sequence training starts from the initial state and feeds back predictions, without future truth.</p><h2>Matched selected-model test results</h2><p>Exact identical208 test IDs and simulation values; mean replicas within each configuration, then equal configuration weights. Percent is exact integral of absolute piecewise-linear prediction error divided by duration times that simulation feature’s range. Lower is better.</p><table><thead><tr><th>Feature</th><th>37 baseline</th><th>38 wider/history8</th><th>39 long windows</th><th>40 selected parent</th><th>41 dropout from start</th><th>42 stacked GRU</th></tr></thead><tbody>{rows}</tbody></table><h2>Learning curve</h2><img src="learning-curve.png" alt="Verified full-rollout training and validation learning curve"><p>Four-feature mean range-normalized full-sequence integral errors, equal configuration weighting, no smoothing or gate BCE. No dropout is used during training or evaluation. The final epoch is not necessarily the selected checkpoint.</p><h2>Recovery and verification</h2><p>{recovery} Three regional queues competed, but ownership gating permitted optimizer work only after loser cleanup. Every completed model/optimizer/RNG/selection checkpoint was retained and hashed. Selection preceded test evaluation; all jobs, VMs and disks were verified empty.</p><h2>Limits</h2><p>Historically examined data, not pristine confirmation or independent-seed replication. This fresh run and the earlier checkpoint branches differ in optimization history; this is not an isolated recurrent-depth or hardware comparison.</p><p>{limits}</p><p>The gallery preserves three cases/page, four plots/row, toggles, categorical rubric and symlog axes. Its no-change reference uses previous actual simulation states, unlike autonomous model rollout. Earlier pages remain available.</p><footer><a href="https://github.com/davies-w/wildfire3d/tree/codex/ignition-surrogate-pilot/experiments/{m["folder"]}">Source and DVC pointers</a> · <a href="../full-sequence/{m["slug"]}-r0-values.json">Derived per-history values</a></footer>'
 body=readable(body)
 (D/m['slug']/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+m['label']+'</title><style>'+css+'</style></head><body><main>'+body+'</main></body></html>')
cards=''.join(f'<a class="card" href="{m["slug"]}/index.html" target="_blank" rel="noopener noreferrer"><span class="tag">Experiment{m["number"]} · completed</span><h2>{m["label"]} →</h2><p>Matched results, learning curve, checkpoint lineage and limitations. '+'Fresh two-layer recurrent model, no dropout, full curriculum and matched results.'+'</p></a>' for m in models)
index=old['index.html'];assert '<div class="cards">' in index and 'stacked42/index.html' not in index
updated=index.replace('<div class="cards">','<div class="cards">'+cards,1);assert updated.replace(cards,'',1)==index;(D/'index.html').write_text(updated)
(R/'results03/report-build.json').write_text(json.dumps(dict(passed=True,parent_revision=rev,prior_cells_preserved=True,prior_index_preserved=True,matched_test_histories=208,fresh_initialization=True,models=[{k:v for k,v in m.items() if k not in ['analysis','phases']} for m in models]),indent=2)+'\n')
print('Built stacked GRU report/card/gallery; prior reports preserved.')

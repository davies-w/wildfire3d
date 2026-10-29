"""Move integral-objective rotations into a concise top table, preserving old models."""
from pathlib import Path
import json,re,hashlib
from huggingface_hub import HfApi,hf_hub_download
R=Path(__file__).resolve().parent;D=R/'data/scorecard-layout';D.mkdir(exist_ok=True)
api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
old=Path(hf_hub_download(repo,'full-sequence/index.html',repo_type='space',revision=rev)).read_text()
assert 'id="integral-objective-summary"' not in old
(D/'before.html').write_text(old)
sections=re.findall(r'<section>.*?</section>',old,re.S)
phase={name:next(s for s in sections if '<h2>'+name.title()+' periods</h2>' in s) for name in ['active','quiet','all','weak']}
models=[('new-integral-model','g7','0',208,'integral-gated.html'),('new-rotation1-model','g8','1',210,'integral-gated-r1.html')]
values={}
for cls,g,rotation,count,url in models:
 for name,s in phase.items():
  cells=re.findall(r'<td class="'+cls+r'">(.*?)</td>',s);assert len(cells)==12
  values[cls,name]=[cells[i:i+3] for i in range(0,12,3)]
 for name in ['quiet','all','weak']:assert [row[2] for row in values[cls,name]]==[row[2] for row in values[cls,'active']]
features=['Water (kg)','Dry fuel (kg)','Gas release (kg/s)','Heating index (K)']
summary='<section id="integral-objective-summary"><h2>Integral-objective gated GRU</h2><p>Whole-sequence integral error matches the graph boxes. Error vs simulation is reported separately for active and quiet periods. Lower is better for every column.</p><div class="table-wrap"><table><thead><tr><th rowspan="2">Output</th>'
for cls,g,rotation,count,url in models:summary+=f'<th colspan="3" class="group {g}"><a href="{url}">Rotation {rotation}</a> · {count} test histories</th>'
summary+='</tr><tr>'
for cls,g,rotation,count,url in models:summary+=f'<th class="{g}">Integral error ↓<br>Whole sequence</th><th class="{g}">Error vs sim ↓<br>Active</th><th class="{g}">Error vs sim ↓<br>Quiet</th>'
summary+='</tr></thead><tbody>'
for i,feature in enumerate(features):
 summary+='<tr><th>'+feature+'</th>'
 for cls,g,rotation,count,url in models:
  summary+=''.join('<td>'+v+'</td>' for v in [values[cls,'active'][i][2],values[cls,'active'][i][0],values[cls,'quiet'][i][0]])
 summary+='</tr>'
summary+='</tbody></table></div><p>Same architecture, recipe and seed; different held-out populations, so these rotations are not matched model comparisons or independent-seed repeats. Each has 204 configurations, weighted equally. Previously examined dataset.</p></section>'
new=old
for cls,g,rotation,count,url in models:
 new=re.sub(r'<th colspan="3" class="group '+g+r'">.*?</th>','',new)
 new=re.sub(r'<th class="'+g+r'">.*?</th>','',new)
 new=re.sub(r'<td class="'+cls+r'">.*?</td>','',new)
new=re.sub(r'<p><strong>Integral-loss gated.*?</p>','',new)
assert re.findall(r'<td.*?</td>',new,re.S)==re.findall(r'<td.*?</td>',re.sub(r'<td class="(?:new-integral-model|new-rotation1-model)">.*?</td>','',old),re.S)
new=new.replace('</h1>','</h1>'+summary,1)
assert 'Improvement' not in summary and summary.count('<td>')==24
(D/'index.html').write_text(new)
proof=dict(passed=True,parent=rev,scope='Integral-objective rotations only',values_unchanged=True,old_model_cells_preserved=True,galleries_untouched=True,columns_per_rotation=['whole-sequence integral','active error vs sim','quiet error vs sim'],sha256=hashlib.sha256(new.encode()).hexdigest())
(R/'results/scorecard-layout.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

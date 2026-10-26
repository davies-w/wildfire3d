from pathlib import Path
import json, math, hashlib, shutil
R=Path(__file__).resolve().parent
src=R/'inputs'
a=json.loads((src/'mlp-comparison.json').read_text())
b=json.loads((src/'gru-scorecard.json').read_text())
models=['3-state MLP','4-state plain GRU','4-state gated GRU']
features=['Water','Dry fuel','Gas release','Heating']
data={}
for phase in ['active','quiet']:
 m=a['summary']['3-state MLP'][phase]
 data[phase]={models[0]:{'error':m['error_vs_sim_percent'],'improvement':m['reduction_vs_no_change_percent'],'mae':m['model_mae'],'truth':m['mean_truth'],'baseline':m['no_change_mae']}}
 for arm,name in [('control',models[1]),('gated',models[2])]:
  v=b['horizons']['16']['v1_'+phase][arm]
  data[phase][name]={'error':v['error_vs_sim_percent'],'improvement':v['improvement_vs_no_change_percent'],'mae':v['MAE'],'truth':v['mean_absolute_truth'],'baseline':v['no_change_MAE']}
  for key in ['truth','baseline']:
   assert all(math.isclose(x,y,rel_tol=1e-5,abs_tol=1e-9) for x,y in zip(data[phase][models[0]][key],data[phase][name][key]))
def pct(v,quiet=False):
 if quiet and v:
  v=round(v,-int(math.floor(math.log10(abs(v)))))
  return '≈ '+(f'{v:,.0f}' if abs(v)>=1 else f'{v:g}')+'%'
 return f'{v:.0f}%'
sections=[]
for phase in ['active','quiet']:
 active=phase=='active'; span=2 if active else 1
 s=f'<section><h2>{phase.title()} periods</h2><p>'+('Whole percentages. Error vs simulation: lower is better. Improvement vs no change: higher is better.' if active else 'Error vs simulation, rounded to one significant digit. Lower is better.')+'</p><div class="table-wrap"><table><thead><tr><th rowspan="2">State</th>'
 s+=''.join(f'<th colspan="{span}" class="group g{i}">{name}</th>' for i,name in enumerate(models))+'</tr><tr>'
 for i in range(3):
  s+=f'<th class="g{i}">Error vs sim ↓</th>'+(f'<th class="g{i}">Improvement vs<br>no change ↑</th>' if active else '')
 s+='</tr></thead><tbody>'
 for j,f in enumerate(features):
  s+=f'<tr><th>{f}</th>'
  for name in models:
   v=data[phase][name]
   if j>=len(v['error']):s+=f'<td colspan="{span}" class="missing">Not predicted</td>';continue
   s+='<td>'+pct(v['error'][j],not active)+'</td>'
   if active:s+='<td>'+pct(v['improvement'][j])+'</td>'
  s+='</tr>'
 s+='</tbody></table></div>'
 if not active:s+='<p class="note">Gas percentages are huge because simulated release is almost zero. Holding the state constant beats all three models on every quiet-period output they predict.</p>'
 sections.append(s+'</section>')
# Raw values remain available without crowding the primary tables.
raw='<details><summary>Exact values and physical scale</summary><p>MAE = mean absolute error. Percentages use the aggregated simulation magnitude, not per-case percentage averages.</p>'
for phase in data:
 raw+=f'<h3>{phase.title()}</h3><div class="table-wrap"><table><tr><th>State / units</th><th>Mean |simulation|</th><th>No-change MAE</th>'+''.join(f'<th>{m} MAE</th>' for m in models)+'</tr>'
 for j,unit in enumerate(['kg','kg','kg/s','K']):
  base=data[phase][models[1]];raw+=f'<tr><th>{features[j]} ({unit})</th><td>{base["truth"][j]:.6g}</td><td>{base["baseline"][j]:.6g}</td>'
  raw+=''.join('<td>'+ (f'{data[phase][m]["mae"][j]:.6g}' if j<len(data[phase][m]['mae']) else 'Not predicted')+'</td>' for m in models)+'</tr>'
 raw+='</table></div>'
raw+='</details>'
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Fire prediction scorecard</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#182637;font:16px/1.5 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:32px 20px}h1{font-size:32px;line-height:1.15;margin-bottom:10px}h2{font-size:23px;margin:0}p{color:#526173}section{background:white;border:1px solid #dce3eb;border-radius:12px;padding:22px;margin:22px 0}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{text-align:right;padding:12px 14px;border-bottom:1px solid #e1e6ec;white-space:nowrap}th:first-child{text-align:left}thead th{font-size:13px;white-space:normal}.group{text-align:center;font-size:16px}.g0{background:#eef1f5}.g1{background:#eaf3fd}.g2{background:#e9f5ee}td{font-size:21px;font-weight:600}.missing{color:#8793a1;font-size:14px;font-weight:400}.note{font-size:14px;margin-bottom:0}details{margin:20px 0;border-top:1px solid #cdd7e2;padding-top:16px}summary{cursor:pointer;font-weight:600}details td{font-size:14px;font-weight:400}footer{font-size:13px;color:#526173}a{color:#205bb0}@media(max-width:700px){main{padding:18px 10px}section{padding:14px}th,td{padding:10px 8px}td{font-size:18px}}
</style></head><body><main><h1>Fire prediction scorecard</h1><p><strong>16 seconds ahead · ten test folds · active and quiet periods</strong><br>Eight two-second prediction steps, feeding predictions back after observed history. Each rotation trains on eight folds, validates on one and tests on one.</p>'''
page+=''.join(sections)+raw+'''<details><summary>Definitions and comparison limits</summary><p>Active: trailing 10-second water loss or dry-fuel-equivalent gas release is at least 0.1% of the relevant initial mass per 10 seconds. Quiet: both are below 0.01%. Every predicted step must qualify for the stable category. Weak activity and transitions are excluded from these two tables, not relabelled quiet. Heating alone does not count as activity. These are engineering tolerances, not a validated extinction criterion.</p><p>Error vs sim = 100 × aggregate MAE / aggregate mean absolute simulation value. Improvement vs no change = 100 × (1 − model MAE / no-change MAE). Histories are averaged within configurations, then configurations within folds, then eligible folds equally; replicas remain grouped.</p><p>The MLP is the three-state model from attempt18, evaluated with frozen scorecard v1 in attempt22. Plain and gated GRUs are the matched four-state models from attempt24. Their common simulation denominators and no-change baselines agree within numerical tolerance. This comparison spans experiments and changes states as well as architecture; it does not isolate an architecture effect. No four-state MLP was trained. The 520 histories cover 480 configurations; these historically examined, reshuffled test sets are not pristine.</p><p>Heating is a mass-weighted particle surface-heating index in K, not stored energy in joules. Gas release means vegetation fuel gas, not combustion heat. Water and dry fuel are derived using audited integration and a 0.75 fuel-gas yield; char is treated as inert ash.</p></details><footer><p>Simulation scope: generic 3 m-wide conical vegetation crowns, 4/6/8/10 m high above a 2 m base; 1600 weighted particles; 0.5 m mesh in a 24 × 16 × 16 m domain; 180-second histories; imposed 1500°C ignition source for 20 seconds. 48 legacy geometries are retained. No trunks, buildings or embers; no physical validation.</p><p><a href="values.json">Download exact scorecard values</a> · <a href="sources.json">Source hashes</a> · <a href="https://huggingface.co/spaces/wdavies/fire-prediction-gallery">Scenario gallery</a></p></footer></main></body></html>'''
out=R/'data';out.mkdir(exist_ok=True)
(out/'index.html').write_text(page)
(out/'values.json').write_text(json.dumps({'horizon_seconds':16,'models':models,'features':features,'metrics':data},indent=2))
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(src.glob('*.json'))},indent=2))
assert page.count('<h2>')==2 and '52,000' not in page
print(out/'index.html')
# Publish a self-contained report hub; keep the simple scorecard at a stable subpath.
score=out/'scorecard';score.mkdir(exist_ok=True)
for name in ['index.html','values.json','sources.json']:
 shutil.copy2(out/name,score/name)
for folder in ['learning-curve','detailed-scorecard','architecture-comparison']:
 shutil.copytree(src/folder,out/folder,dirs_exist_ok=True)
cards=[
 ('scorecard/index.html','Simple scorecard','Start here','Active and quiet periods together. Three-state MLP, plain four-state GRU and gated four-state GRU. 16-second forecasts across ten test folds.'),
 ('https://huggingface.co/spaces/wdavies/fire-prediction-gallery','Prediction gallery','Explore scenarios','Simulation, no-change, linear extrapolation and recursive gated-GRU predictions. Water, dry fuel, gas release and heating across 520 held-out histories.'),
 ('learning-curve/report.html','Does more training data help?','Learning curve','One fixed validation/test split, with one through eight training folds. Plain four-state GRU; this is one learning curve, not ten-fold uncertainty.'),
 ('https://huggingface.co/spaces/wdavies/fire-state-storyboards','Simulation storyboards','Simulation reference','The previously published 48-history simulation storyboard collection.'),
 ('detailed-scorecard/report.html','Detailed gate comparison','Supporting report','The original detailed plain-versus-gated GRU scorecard, including additional phase and scenario diagnostics.'),
 ('architecture-comparison/report.html','Earlier architecture comparison','Supporting report','Frozen v1 comparison of three-state MLP, three-state GRU and four-state GRU. Different experiments; no four-state MLP was trained.'),
 ('https://github.com/davies-w/wildfire3d/blob/codex/ignition-surrogate-pilot/experiments/35_surrogate_diagnostics/FINAL_REPORT.md','Experiment findings','GitHub','Research findings and experiment history, including unsuccessful additions and scientific limitations.')]
hub='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire prediction reports</title><style>*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#182637;font:17px/1.55 system-ui,sans-serif}main{max-width:1050px;margin:auto;padding:48px 24px}h1{font-size:40px;line-height:1.1;margin:0 0 16px}.intro{max-width:750px;color:#526173}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-top:32px}.card{display:block;background:white;color:inherit;text-decoration:none;padding:24px;border:1px solid #dce3eb;border-radius:14px}.card:hover{border-color:#2870b8;box-shadow:0 5px 18px #18263712}.card:first-child{border-top:5px solid #2870b8}.tag{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#2870b8}h2{font-size:22px;line-height:1.25}p{color:#526173}.card p{font-size:15px}.foot{font-size:13px;border-top:1px solid #dce3eb;margin-top:32px;padding-top:20px}a{color:#205bb0}</style></head><body><main><h1>Fire prediction reports</h1><p class="intro">A single index for the model scorecards, scenario gallery, training-data learning curve and simulation references.</p><div class="cards">'''
import html
for href,title,tag,desc in cards:
 hub+=f'<a class="card" href="{html.escape(href)}"><span class="tag">{tag}</span><h2>{title} →</h2><p>{desc}</p></a>'
hub+='''</div><div class="foot"><p>These reports concern simplified simulated vegetation fires, not validated real-tree fire forecasts. Heating is a surface-heating index, not stored energy; gas is vegetation fuel-gas release, not heat release. Geometry, ignition and evaluation limitations are documented in each report. Older reports retain their original models and definitions.</p><p><a href="https://github.com/davies-w/wildfire3d/tree/codex/ignition-surrogate-pilot/experiments/35_surrogate_diagnostics/simple_scorecard">Report source and provenance on GitHub</a></p></div></main></body></html>'''
(out/'index.html').write_text(hub)

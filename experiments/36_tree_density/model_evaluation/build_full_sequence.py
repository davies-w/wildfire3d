"""New full-sequence reports from archived autonomous forecasts; no inference or fitting."""
from pathlib import Path
import json,hashlib,html
import numpy as np
R=Path(__file__).resolve().parents[1];O=R.parent/'35_surrogate_diagnostics';D=R/'data/full-sequence';D.mkdir(exist_ok=True)
features=['Water (kg)','Dry fuel (kg)','Gas release (kg/s)','Heating index (K)']
specs=[('mlp3','3-state MLP',O/'attempt18/data/collected',O/'attempt18/data/sequences.npz',range(0,20,2),520),('gru3','3-state GRU',O/'attempt18/data/collected',O/'attempt18/data/sequences.npz',range(1,20,2),520),('plain4','4-state plain GRU',O/'attempt24/data/collected',O/'attempt24/data/sequences.npz',range(0,20,2),520),('gated4','4-state gated GRU',O/'attempt24/data/collected',O/'attempt24/data/sequences.npz',range(1,20,2),520),('dense','Dense plain GRU',R/'data/model-training-results',R/'data/learning/sequences.npz',range(10),2080),('strideplain','Stride-one plain · split 0',R/'data/pair-sequence-r0-results',R/'data/learning/sequences.npz',[0],208),('stridegated','Stride-one gated · split 0',R/'data/pair-sequence-r0-results',R/'data/learning/sequences.npz',[1],208)]
provenance={};models=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def grouped(v,c):return np.stack([v[c==k].mean(0) for k in np.unique(c)]).mean(0)
def numbers(x):return [float(v) if np.isfinite(v) else None for v in x]
for slug,name,root,seq,folds,expected in specs:
 a=np.load(seq);records=[];idsall=[];predall=[];truthall=[];baseall=[];labs=[];configs=[]
 labels=a['activity_labels'] if 'activity_labels' in a.files else np.load(O/'attempt22/data/activity_audit/labels.npz')['labels']
 for fold in folds:
  p=root/f'fold{fold:02}-test-predictions.npz';v=np.load(p);ids=v['case_indices'];pred=np.sinh(v['normalized_rollout']*v['std']+v['mean'])*v['physical_scales'];n=pred.shape[-1];truth=a['state'][ids,1:,:n];baseline=a['state'][ids,:-1,:n]
  assert pred.shape==truth.shape and np.array_equal(v['times'],a['time'][ids]);assert np.isfinite(pred).all(),(slug,'nonfinite requires explicit handling')
  provenance[str(p.relative_to(R.parents[1]))]=digest(p)
  for j,i in enumerate(ids):
   records.append(dict(id=int(i),fold=int(fold),time=a['time'][i].tolist(),truth=a['state'][i,:,:n].tolist(),prediction=np.concatenate([a['state'][i,:1,:n],pred[j]],0).tolist(),baseline=np.concatenate([a['state'][i,:1,:n],a['state'][i,:-1,:n]],0).tolist()))
  idsall.extend(ids.tolist());predall.append(pred);truthall.append(truth);baseall.append(baseline);labs.append(labels[ids]);configs.append(a['configuration'][ids])
 assert len(idsall)==len(set(idsall))==expected
 if expected!=208:assert sorted(idsall)==list(range(expected))
 pred=np.concatenate(predall);truth=np.concatenate(truthall);baseline=np.concatenate(baseall);lab=np.concatenate(labs);conf=np.concatenate(configs);phases={}
 for phase,mask in [('all',np.ones(lab.shape,bool)),('active',np.isin(lab,[1,2])),('quiet',lab==0),('weak',lab==3)]:
  count=mask.sum(1);keep=count>0;vals=[]
  for x in [abs(pred-truth),abs(baseline-truth),abs(truth)]:vals.append(grouped((np.where(mask[:,:,None],x,0).sum(1)[keep]/count[keep,None]),conf[keep]))
  m,b,t=vals
  with np.errstate(divide='ignore',invalid='ignore'):err=100*m/t;imp=100*(1-m/b)
  phases[phase]=dict(MAE=numbers(m),no_change_MAE=numbers(b),mean_absolute_truth=numbers(t),error_percent=numbers(err),improvement_percent=numbers(imp),points=int(mask.sum()),histories=int(keep.sum()),configurations=len(np.unique(conf[keep])))
 records.sort(key=lambda x:x['id']);payload=dict(name=name,records=records);(D/f'{slug}.json').write_text(json.dumps(payload,separators=(',',':'),allow_nan=False))
 # Read back exactly what the gallery consumes and independently recompute all-period MAE.
 loaded=json.loads((D/f'{slug}.json').read_text())['records'];rr=np.array([np.abs(np.array(q['prediction'])[1:]-np.array(q['truth'])[1:]).mean(0) for q in loaded]);cc=a['configuration'][[q['id'] for q in loaded]];assert np.allclose(grouped(rr,cc),phases['all']['MAE'],rtol=1e-6,atol=1e-7)
 models.append(dict(slug=slug,name=name,histories=expected,configurations=len(np.unique(conf)),phases=phases,negative_prediction_elements=(pred<0).sum((0,1)).tolist(),nonfinite_prediction_elements=0))
old=O/'simple_scorecard/data/scorecard/values.json';historical=json.loads(old.read_text());(D/'historical-scores.json').write_text(json.dumps(historical,indent=2));provenance[str(old.relative_to(R.parents[1]))]=digest(old)
report=dict(baseline='At each target time, predict the actual simulation state from the preceding saved time. This baseline receives fresh truth; the model does not.',protocol='One initial simulated state at t=0; 90 recursive prediction steps; no later truth resets. Known geometry, ignition schedule and time intervals remain supplied. Initial state excluded from errors.',aggregation='Average eligible target transitions within each history; average replicas within configuration; equal weight configurations. Active/quiet are frozen truth-based labels at each transition, NOT all-origin forecast-window masks. No clamping or finite-only filtering.',scope='Different populations: earlier 520 histories/480 configurations; dense 2080/2040; stride pair shared 208/204 single split. Previously examined reshuffled test data, not pristine. No matched architecture/data-effect claim.',models=models,source_sha256=provenance,chart_metric_readback_passed=True)
(D/'scores.json').write_text(json.dumps(report,indent=2,allow_nan=False))
style='<style>body{margin:0;background:#f3f5f8;color:#182637;font:17px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:36px 24px}h1{font-size:34px}section{background:white;border:1px solid #dce3eb;border-radius:14px;padding:22px;margin:22px 0}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{text-align:right;padding:12px 10px;border-bottom:1px solid #e1e6ec;white-space:nowrap}th:first-child{text-align:left}thead th{font-size:13px;white-space:normal}.group{text-align:center;font-size:16px}.g0{background:#eef1f5}.g1{background:#eaf3fd}.g2{background:#e9f5ee}.g3{background:#fff2dc}.g4{background:#f1edfc}.g5{background:#e7f5f3}.g6{background:#fceee9}td{font-size:21px;font-weight:600}.missing{color:#8793a1;font-size:14px;font-weight:400}.note{font-size:14px}details{margin:20px 0;border-top:1px solid #cdd7e2;padding-top:16px}summary{cursor:pointer;font-weight:600}details td{font-size:14px;font-weight:400}a{color:#205bb0}svg{width:100%;height:230px;background:white}.plots{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:15px}@media(max-width:700px){main{padding:18px 10px}section{padding:14px}td{font-size:18px}}</style>'
intro='<p><strong>Full sequence · approximately 180 seconds · active and quiet periods</strong><br>Model initialized once at t=0, then 90 model-fed steps with no later simulation-state resets. Errors are averaged across saved target times, not just the final time. Known forcing and geometry remain supplied.</p><p><strong>No-change comparison:</strong> at each target time, use the simulation’s actual state at the preceding saved time. This baseline receives fresh simulation truth; the model predictions remain continuous.</p>'
def pct(v,quiet=False):
 if v is None:return 'Undefined'
 if quiet and v:
  import math
  v=round(v,-int(math.floor(math.log10(abs(v)))))
  return '≈ '+(f'{v:,.0f}' if abs(v)>=1 else f'{v:.12f}'.rstrip('0').rstrip('.'))+'%'
 return f'{v:,.0f}%'
def table_section(phase):
 text=f'<section><h2>{phase.title()} periods</h2><p>Error vs simulation: lower is better. Improvement vs no change: higher is better.'+(' Quiet percentages rounded to one significant digit.' if phase=='quiet' else ' Whole percentages.')+'</p><div class="table-wrap"><table><thead><tr><th rowspan="2">State</th>'+''.join(f'<th colspan="2" class="group g{i}">{html.escape(m["name"])}</th>' for i,m in enumerate(models))+'</tr><tr>'+''.join(f'<th class="g{i}">Error vs sim ↓</th><th class="g{i}">Improvement vs<br>no change ↑</th>' for i in range(len(models)))+'</tr></thead><tbody>'
 for f,title in enumerate(features):
  text+='<tr><th>'+title+'</th>'
  for m in models:
   v=m['phases'][phase]
   text+=('<td colspan="2" class="missing">Not predicted</td>' if f>=len(v['MAE']) else '<td>'+pct(v['error_percent'][f],phase=='quiet')+'</td><td>'+pct(v['improvement_percent'][f],phase=='quiet')+'</td>')
  text+='</tr>'
 return text+'</tbody></table></div><p class="note">Negative improvement means the model has more error than the previous-simulation-state baseline. Near-zero gas denominators can produce large percentages.</p></section>'
page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Full-sequence scorecard</title>'+style+'</head><body><main><h1>Full-sequence simplified scorecard</h1>'+intro+table_section('active')+table_section('quiet')+'<p><a href="gallery.html">Full-sequence visual comparisons</a> · <a href="historical-scores.json">Original 16-second scores</a> · <a href="scores.json">Download exact values and provenance</a></p>'
page+='<details><summary>All-period and weak-period scores</summary>'+table_section('all')+table_section('weak')+'</details><details><summary>Exact values and physical scale</summary>'
for phase in ['all','active','quiet','weak']:
 page+='<h3>'+phase.title()+'</h3><div class="table-wrap"><table><tr><th>Model / state</th><th>Model MAE</th><th>No-change MAE</th><th>Mean |simulation|</th></tr>'
 for m in models:
  v=m['phases'][phase]
  for f in range(len(v['MAE'])):page+='<tr><th>'+html.escape(m['name'])+' · '+features[f]+'</th>'+''.join(f'<td>{v[k][f]:.8g}</td>' for k in ['MAE','no_change_MAE','mean_absolute_truth'])+'</tr>'
 page+='</table></div>'
page+='</details><details><summary>Definitions and comparison limits</summary><p>'+report['scope']+'</p><p>'+report['aggregation']+'</p><p>Error vs sim = 100 × MAE / mean absolute simulation. Improvement = 100 × (1 − model MAE / previous-simulation-state baseline MAE). Initial state is excluded. Undefined ratios are shown explicitly.</p><p>Simulation reference: derived remaining water/fuel, summed gas release, and mass-weighted surface-heating index, aligned to actual saved timestamps. Generic 3 m conical crowns, heights 4/6/8/10 m above 2 m base; 1600 weighted particles; 0.5 m mesh in a 24 × 16 × 16 m domain; imposed 1500°C ignition for 20 s. No trunks, buildings, embers or physical validation. Heating is K, not energy; gas is kg/s, not heat.</p></details></main></body></html>'
(D/'index.html').write_text(page)
gallery='''<!doctype html><meta charset="utf-8"><title>Full-sequence comparisons</title>'''+style+'''<main><h1>Full-sequence visual comparisons</h1>'''+intro+'''<p><a href="index.html">Matching full-sequence scorecard</a></p><select id="model"></select><button id="prev">Previous</button><select id="case"></select><button id="next">Next</button><p id="info"></p><p>Blue: derived simulation reference · Orange: continuous model prediction · Gray: previous simulation state (refreshed each step). Linear axes; straight segments through all saved samples; no clipping or smoothing. Each model's own held-out population is shown.</p><div class="plots" id="plots"></div></main><script>
const models=__MODELS__, names=__FEATURES__;let data,idx=0;const model=document.getElementById('model'),cases=document.getElementById('case');models.forEach(m=>model.add(new Option(m.name,m.slug)));
async function load(){data=await(await fetch(model.value+'.json')).json();cases.innerHTML='';data.records.forEach((r,i)=>cases.add(new Option('History '+r.id+' · saved fold '+r.fold,i)));idx=0;draw()}
function draw(){cases.value=idx;const r=data.records[idx];document.getElementById('info').textContent=data.name+' · history '+r.id+' · '+(idx+1)+' / '+data.records.length+' · initialized at '+r.time[0]+' s; final time '+r.time.at(-1).toFixed(3)+' s';document.getElementById('plots').innerHTML=names.slice(0,r.truth[0].length).map((name,f)=>{let vals=[r.truth,r.prediction,r.baseline].flatMap(v=>v.map(x=>x[f])),lo=Math.min(...vals),hi=Math.max(...vals),pad=(hi-lo||1)*.06;lo-=pad;hi+=pad;let X=t=>55+440*t/r.time.at(-1),Y=v=>190-160*(v-lo)/(hi-lo);let paths=[r.truth,r.prediction,r.baseline].map((v,k)=>'<path fill="none" stroke="'+['#1766b5','#d66610','#888'][k]+'" stroke-width="1.5" d="'+v.map((x,j)=>(j?'L':'M')+X(r.time[j])+','+Y(x[f])).join(' ')+'"/>').join('');return '<section><h2>'+name+'</h2><svg viewBox="0 0 520 225"><text x="3" y="30">'+hi.toPrecision(3)+'</text><text x="3" y="190">'+lo.toPrecision(3)+'</text><text x="55" y="215">0 s</text><text x="440" y="215">'+r.time.at(-1).toFixed(1)+' s</text>'+paths+'</svg></section>'}).join('')}
model.onchange=load;cases.onchange=()=>{idx=+cases.value;draw()};document.getElementById('prev').onclick=()=>{idx=(idx+data.records.length-1)%data.records.length;draw()};document.getElementById('next').onclick=()=>{idx=(idx+1)%data.records.length;draw()};load();</script>'''
(D/'gallery.html').write_text(gallery.replace('__MODELS__',json.dumps([dict(slug=m['slug'],name=m['name']) for m in models])).replace('__FEATURES__',json.dumps(features)))
print(json.dumps(dict(models=len(models),histories=sum(m['histories'] for m in models),chart_metric_readback_passed=True)))

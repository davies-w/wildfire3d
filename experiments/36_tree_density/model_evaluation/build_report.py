"""Publishable report from verified saved results; no training or selection."""
from pathlib import Path
import json,hashlib,html
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/model-training-collected.json').read_text())['passed']
 s=json.loads((R/'results/model-four-state-summary.json').read_text());a=json.loads((R/'results/model-scenario-audit.json').read_text())
 old=json.loads((R/'../35_surrogate_diagnostics/attempt25/results/learning-curve.json').read_text())['sizes'][-1]
 report=json.loads((R/'data/model-training-results/report.json').read_text())
 out=R/'data/published-report';out.mkdir(exist_ok=True)
 names=['Water (kg)','Dry fuel (kg)','Fuel-gas release (kg/s)','Surface-heating index (K)']
 def fmt(x):return 'undefined' if x is None else f'{x:,.4g}'
 def table(headers,rows):return '<div class="scroll"><table><tr>'+''.join('<th>'+html.escape(v)+'</th>' for v in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'
 parts=['<h1>Denser simulation data: completed baseline</h1><p>2,080 histories · 2,040 configurations · ten grouped test folds · plain four-state GRU</p>', '<section><h2>What this run measures</h2><p>This run adds 1,560 simulated configurations to the original 520 histories. Each model trains on eight folds (1,658–1,670 histories), validates on one and tests on one. All ten selections were frozen before any test evaluation.</p><p><strong>Training used non-overlapping windows:</strong> the 1/8/16/32-step curriculum advances each starting point by the current window length, including a shorter final window. At 16 steps that is five full windows and one ten-step tail per history. Evaluation uses every valid starting point. The requested stride-one curriculum rerun is a separate experiment, not included in these results.</p><p>The larger dataset also changes the test distribution, fold assignment and optimizer updates per epoch. The old-versus-new table below is descriptive; it does not isolate the causal effect of adding data.</p></section>']
 for phase in ['active','quiet','weak','transition']:
  v=s['horizons']['16']['phases'][phase]
  parts.append(f'<section><h2>16 seconds ahead: {phase}</h2><p>{v["configurations"]:,} eligible configurations; {v["forecast_origins"]:,} forecast origins. Lower error is better; higher improvement is better.</p>')
  if v['defined']:
   parts.append(table(['State','MAE','No-change MAE','Mean |simulation|','Error / simulation (%)','Improvement over no change (%)'],[[n]+[fmt(v[k][i]) for k in ['MAE','no_change_MAE','mean_absolute_simulation','error_vs_simulation_percent','improvement_vs_no_change_percent']] for i,n in enumerate(names)]))
  else:parts.append('<p>'+html.escape(v['reason'])+'</p>')
  parts.append('</section>')
 parts.append('<section><h2>Earlier 520-history run versus this run</h2><p>Earlier: one fixed test fold, eight training folds, 384 training configurations. Current: ten test folds pooled, 1,632 training configurations per model. Same plain model and recipe, but different held-out populations and training work. Values are 16-second MAE in each state’s units; direct differences are not a controlled data-only effect.</p>')
 rows=[]
 for phase in ['active','quiet']:
  v=s['horizons']['16']['phases'][phase];o=old['horizons']['16']['v1_'+phase]
  for i,n in enumerate(names):rows.append([phase,n,fmt(o['MAE'][i]),fmt(v['MAE'][i]),fmt(o['no_change_MAE'][i]),fmt(v['no_change_MAE'][i])])
 parts.append(table(['Phase','State','Earlier MAE','Current MAE','Earlier no-change','Current no-change'],rows)+'</section>')
 parts.append('<section><h2>All forecast horizons</h2><p>Actual saved times are used. Nominal horizons are labels; exact duration ranges are available in the downloadable values.</p>')
 for phase in ['active','quiet']:
  rows=[]
  for h,vv in s['horizons'].items():
   v=vv['phases'][phase]
   rows.append([h+' s']+[fmt(x) for x in v.get('MAE',[None]*4)])
  parts.append('<h3>'+phase.title()+' MAE</h3>'+table(['Nominal horizon']+names,rows))
 parts.append('</section><section><h2>Scenario variation and invalid predictions</h2>')
 for phase in ['active','quiet']:
  v=a['distributions']['8']['16'][phase]
  parts.append('<h3>'+phase.title()+'</h3>'+table(['State','Median scenario MAE','90th percentile MAE','Scenarios beating no change (%)'],[[n,fmt(v['median_MAE'][i]),fmt(v['p90_MAE'][i]),fmt(100*v['fraction_beating_baseline'][i])] for i,n in enumerate(names)]))
 e=a['events']['8'];parts.append('<p>Full autonomous rollout: mean negative magnitude by state (unclamped): '+', '.join(n+': '+fmt(x) for n,x in zip(names,e['negative_mean_magnitude']))+'. Cumulative positive water/fuel increases (kg): '+', '.join(fmt(x) for x in e['mass_increase_total_kg'])+'. These invalid directions are reported, not corrected.</p></section>')
 parts.append('<section><h2>Training and preservation</h2>'+table(['Fold','Terminal epoch','Selected epoch','Optimizer updates','Stop reason'],[[f['fold'],f['epochs'],f['selected_epoch'],f['history'][-1]['optimizer_updates'],f['stop_reason']] for f in report['folds']])+'<p>Same seed3516 initialization per rotation; AdamW learning rate0.0003, weight decay0.0001, gradient clip1, batch256 windows; 100–400 epochs, patience30. Curriculum changes at epochs1/21/41/61. Train-only configuration-balanced asinh normalization. Four-state squared-error sum divided by3; selection uses the original three-state autonomous validation MSE. Reporting uses an algebraically equivalent vectorized reduction with disclosed floating-point order differences (GPU equivalence tolerance1e-5 relative/1e-7 absolute). All epoch model/optimizer/RNG checkpoints and forecasts are preserved privately with verified hashes.</p></section>')
 parts.append('<section><h2>Definitions and simulation scope</h2><p>Metrics average eligible origins within histories, replicas within configurations, then configurations equally. Error percentages divide pooled MAE by pooled mean absolute simulation magnitude; improvement compares with holding the current state unchanged. Near-zero gas denominators can produce large percentages. Active/quiet/weak/transition masks are frozen ScorecardV1 labels; selection does not use these test results. See exact values and event diagnostics below.</p><p>Generic 3m-diameter vegetation cones, heights4/6/8/10m above a2m base,1600 weighted particles;0.5m mesh in24×16×16m; imposed1500°C ignition arc for20s;180s histories. Original48 legacy geometries retained. No trunks, buildings or embers; no physical validation. Water/dry fuel are derived material estimates; gas is fuel-gas release, not combustion heat; heating is a surface index in K, not energy. Previously examined reshuffled simulations are not pristine tests.</p></section>')
 parts.append('<p><a href="values.json">Exact values</a> · <a href="scenario-audit.json">Scenario/event diagnostics</a> · <a href="sources.json">Source hashes</a> · <a href="../index.html">All fire reports</a></p>')
 css='body{font:16px/1.6 system-ui;background:#f2f5f8;color:#182637;margin:0}main{max-width:1200px;margin:auto;padding:28px}section{background:white;border:1px solid #dce3eb;border-radius:12px;padding:22px;margin:24px 0}h1{line-height:1.2}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td,th{padding:10px;border-bottom:1px solid #dce3eb;text-align:right}td:first-child,th:first-child{text-align:left}.scroll{overflow:auto}a{color:#205bb0}'
 (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Denser simulation data — non-overlapping baseline</title><style>'+css+'</style><main>'+''.join(parts)+'</main></html>')
 (out/'values.json').write_text(json.dumps({'current':s,'earlier_fixed_split':old},indent=2,allow_nan=False))
 (out/'scenario-audit.json').write_text(json.dumps(a,indent=2,allow_nan=False))
 sources=['results/model-training-collected.json','results/model-four-state-summary.json','results/model-scenario-audit.json','data/model-training-results/report.json','model_evaluation/build_report.py']
 (out/'sources.json').write_text(json.dumps({p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in sources},indent=2))
 print(out)
if __name__=='__main__':main()

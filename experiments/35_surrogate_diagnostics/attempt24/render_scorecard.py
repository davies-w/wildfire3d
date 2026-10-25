"""Readable static frozen-v1 report for all four outputs."""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parent;s=json.loads((R/'results/scorecard-summary.json').read_text());a=json.loads((R/'results/scenario-audit.json').read_text()) if (R/'results/scenario-audit.json').exists() else None
parts=['<!doctype html><html><meta charset="utf-8"><title>Gated GRU comparison</title><style>body{font:17px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#182535;background:#f8fafc}h1{font-size:34px}h2{margin-top:40px}table{border-collapse:collapse;width:100%;background:white;margin:18px 0}td,th{text-align:right;padding:12px;border-bottom:1px solid #dae1e8}th:first-child,td:first-child{text-align:left}p{line-height:1.55}small{color:#526273}.box{background:#e9eff8;padding:18px;border-radius:8px}</style><body><h1>Do learned gates reduce quiet-period drift?</h1><p class="box"><b>Yes, with a tradeoff.</b> At 16 seconds ahead, quiet errors fall about 89% for water, 92% for dry fuel and 93% for gas versus the control. Active-period errors rise about 16%, 14% and 9%. Quiet predictions still lose to holding the last state unchanged.</p><p>Both models predict water, dry fuel, vegetation fuel-gas release, and a surface-heating index. The index is not heat energy; gas release is not combustion heat. Same grouped test folds and validation selection rule. Previously examined, reshuffled simulations are not a pristine benchmark.</p>']
features=['Water','Dry fuel','Fuel-gas release','Surface-heating index']
def table(title,rows):
 parts.append('<h3>'+title+'</h3><table><tr><th>Model</th>'+''.join('<th>'+x+'</th>' for x in features)+'</tr>')
 for name,values in rows:parts.append('<tr><td>'+name+'</td>'+''.join('<td>'+('undefined' if x is None else f'{x:,.2f}%')+'</td>' for x in values)+'</tr>')
 parts.append('</table>')
for phase,label in [('v1_active','Active throughout the forecast'),('v1_quiet','Quiet throughout the forecast'),('v1_weak','Weak residual activity'),('v1_transition','Activity category changes')]:
 d=s['horizons']['16'][phase];parts.append('<h2>16 seconds ahead · '+label+'</h2>')
 table('Error relative to simulation — lower is better',[(k.title(),v['error_vs_sim_percent']) for k,v in d.items()])
 table('Error reduction versus “no change” — higher is better',[(k.title(),v['improvement_vs_no_change_percent']) for k,v in d.items()])
 parts.append('<p><b>Negative reduction means worse than no change.</b> Percentages use aggregate absolute error divided by aggregate absolute simulation value; they are not averages of individual percentage errors. Near-zero quiet gas values produce very large percentages.</p><table><tr><th>Absolute MAE / denominator</th><th>Water kg</th><th>Dry fuel kg</th><th>Gas kg/s</th><th>Heating K</th></tr>')
 for name,v in [('Control error',d['control']['MAE']),('Gated error',d['gated']['MAE']),('No-change error',d['control']['no_change_MAE']),('Simulation denominator',d['control']['mean_absolute_truth'])]:parts.append('<tr><td>'+name+'</td>'+''.join(f'<td>{x:.6g}</td>' for x in v)+'</tr>')
 parts.append('</table>')
 if a:
  parts.append('<h3>Across eligible physical configurations</h3><table><tr><th>Model · statistic</th>'+''.join('<th>'+x+'</th>' for x in features)+'</tr>')
  for kind in ['control','gated']:
   x=a['distributions'][kind]['16'][phase.removeprefix('v1_')]
   for key,label2 in [('median_MAE','Median MAE'),('p90_MAE','90th-percentile MAE'),('wins','Wins vs no change'),('ties','Ties'),('losses','Losses')]:parts.append('<tr><td>'+kind.title()+' · '+label2+f" (n={x['configurations']})</td>"+''.join(f'<td>{z:.6g}</td>' for z in x[key])+'</tr>')
  parts.append('</table>')
parts.append('<h2>Scope and interpretation</h2><p>520 histories, 480 physical configurations, ten grouped rotations: eight folds train, one validation, one test. Seed replicas stay together. Activity is defined from simulation history using frozen engineering thresholds, not a physical extinction claim. Gates can reopen; heating remains ungated. Both models remain unconstrained and can predict invalid negative quantities or increasing material mass.</p><p>Generic 3 m wide vegetation cones, heights 4/6/8/10 m above a 2 m base, 1,600 weighted particles, 0.5 m grid in a 24×16×16 m domain, 180 s histories and an imposed 1500°C ignition source for 20 s. No trunks, buildings or embers; 48 legacy histories retain their documented geometry. Water/fuel are derived with a 0.75 fuel-gas yield; char is treated as inert ash. These results are not physical validation.</p></body></html>')
v=R/'data/scorecard';v.mkdir(exist_ok=True);(v/'report.html').write_text(''.join(parts));print(v/'report.html')

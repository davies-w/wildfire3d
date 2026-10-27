"""Separate denser scorecard/gallery from verified saved predictions; no fitting."""
from pathlib import Path
import json,numpy as np,shutil
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/model-training-collected.json').read_text())['passed']
 D=R/'data/denser';D.mkdir(exist_ok=True);G=D/'gallery';G.mkdir(exist_ok=True)
 a=np.load(R/'data/learning/sequences.npz');meta=json.loads((R/'learning-schema.json').read_text());root=R/'data/model-training-results';records=[];seen=[]
 for fold in range(10):
  one=np.load(root/f'fold{fold:02}-horizon01-predictions.npz');six=np.load(root/f'fold{fold:02}-horizon16-predictions.npz');full=np.load(root/f'fold{fold:02}-test-predictions.npz');ids=one['case_indices'];seen.extend(ids.tolist());assert np.array_equal(ids,six['case_indices']) and np.array_equal(ids,full['case_indices'])
  ramp=np.sinh(full['normalized_rollout']*full['std']+full['mean'])*full['physical_scales']
  assert np.allclose(ramp[:,0],one['predicted_physical'][:,0],rtol=.002,atol=.002)
  assert np.allclose(ramp[:,15],six['predicted_physical'][:,0],rtol=.002,atol=.002)
  targets=np.arange(1,91);steps=np.minimum(targets,16);origins=targets-steps
  for j,i in enumerate(ids):
   state=a['state'][i];recursive=np.concatenate([ramp[j,:15],six['predicted_physical'][j]],0)
   series=np.stack([state[1:],state[origins],state[origins]+steps[:,None]*(one['predicted_physical'][j,origins]-state[origins]),recursive]);assert series.shape==(4,90,4) and np.isfinite(series).all()
   key=meta['cases'][i]['physical_key']
   records.append(dict(index=int(i),case=meta['cases'][i]['case'],fold=fold,source=meta['cases'][i]['source'],height=key[0],loading=key[2],wind=key[3],angle=key[4],water=float(state[0,0]),fuel=float(state[0,1]),time=a['time'][i,1:].tolist(),values=series.tolist()))
 assert sorted(seen)==list(range(2080));records.sort(key=lambda x:x['index'])
 for p in range((len(records)+2)//3):(G/f'page-{p}.js').write_text('window.receivePage('+str(p)+','+json.dumps(records[p*3:p*3+3],separators=(',',':'),allow_nan=False)+');')
 template=(R.parent/'35_surrogate_diagnostics/attempt24/gallery.html').read_text().replace('__TOTAL__','2080').replace('Test fire scenarios','Denser · prediction gallery').replace('Held-out scenarios · water, fuel, gas & heating','Denser · prediction gallery').replace('Gated GRU','Plain GRU · non-overlapping training baseline')
 template=template.replace('<p class="desc">','<p class="desc"><a href="../index.html">Denser scorecard</a> · ')
 template=template.replace('Formerly examined','Previously examined')
 template=template.replace('Cone schematic, not a species; no trunk implied.','Cone schematic, not a species; no trunk implied. Simulation: 3m-wide crowns above a 2m base, 1600 weighted particles, 0.5m mesh, imposed 1500°C ignition for 20s; no buildings, embers or physical validation.')
 (G/'index.html').write_text(template)
 verification=dict(histories=2080,configurations=2040,pages=694,held_out_once=True,saved_gpu_forecasts_only=True,initial_ramp_endpoint_checks=True,training_changed=False,scope='Initial1..15 predictions from saved autonomous rollout; later rolling16-step predictions from saved horizon16; first-step extrapolation is a visual comparator, not a separately trained model.')
 (G/'verification.json').write_text(json.dumps(verification,indent=2))
 s=json.loads((R/'results/model-four-state-summary.json').read_text());names=['Water','Dry fuel','Gas release','Heating']
 def pct(x):return 'undefined' if x is None else f'{x:,.0f}%'
 parts=['<h1>Denser · simple scorecard</h1><p><strong>16 seconds ahead · plain four-state GRU · ten test folds</strong><br>2,080 histories / 2,040 configurations. Completed non-overlapping training baseline.</p><p><a class="button" href="gallery/index.html">Open denser prediction gallery →</a></p>']
 for phase in ['active','quiet']:
  v=s['horizons']['16']['phases'][phase];active=phase=='active';parts.append('<section><h2>'+phase.title()+' periods</h2><p>Error versus simulation: lower is better.'+(' Improvement over no change: higher is better.' if active else '')+'</p><table><tr><th>State</th><th>Error vs simulation</th>'+('<th>Improvement over no change</th>' if active else '')+'</tr>')
  for i,n in enumerate(names):parts.append('<tr><th>'+n+'</th><td>'+pct(v['error_vs_simulation_percent'][i])+'</td>'+('<td>'+pct(v['improvement_vs_no_change_percent'][i])+'</td>' if active else '')+'</tr>')
  parts.append('</table>'+('' if active else '<p>Holding the current state unchanged beats the model on all four quiet-period outputs. Gas percentages are large because simulated gas release is nearly zero.</p>')+'</section>')
 parts.append('<details><summary>Exact values, definitions and scope</summary><p>Errors are pooled configuration-balanced MAE divided by mean absolute simulation magnitude. Improvement =100×(1−model MAE/no-change MAE). Frozen active/quiet labels exclude weak and transitional periods; these remain in the detailed report. Training used the1/8/16/32-step curriculum with non-overlapping windows and a shorter final tail; evaluation uses every valid origin. The requested overlapping rerun is not shown here.</p><p>Water/dry fuel in kg, fuel gas in kg/s (not heat), heating index in K (not energy). Generic3m-wide cones4/6/8/10m above2m base,1600 weighted particles,0.5m mesh,24×16×16m domain,1500°C ignition for20s,180s histories;48 legacy geometries retained. No trunks/buildings/embers or physical validation. Previously examined reshuffled data.</p><a href="values.json">Exact values</a> · <a href="../density36-baseline/index.html">Detailed report and older-data comparison</a></details>')
 css='body{font:17px/1.5 system-ui;background:#f3f5f8;color:#182637;margin:0}main{max-width:900px;margin:auto;padding:30px 20px}section{background:white;border:1px solid #dce3eb;border-radius:12px;padding:24px;margin:24px 0}table{width:100%;border-collapse:collapse}th,td{padding:14px;border-bottom:1px solid #ddd;text-align:right}th:first-child{text-align:left}td{font-size:27px;font-weight:600}a{color:#205bb0}h1{margin-bottom:8px}details{font-size:14px}summary{cursor:pointer;font-weight:bold}'
 (D/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Denser · simple scorecard</title><style>'+css+'</style><main>'+''.join(parts)+'</main></html>')
 (D/'values.json').write_text(json.dumps(s,indent=2));print('Built denser scorecard and 2080-history gallery')
if __name__=='__main__':main()

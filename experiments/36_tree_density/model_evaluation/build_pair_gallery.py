"""New shared-test-fold gallery from saved cloud forecasts, no model inference."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/pair-sequence-r0-collected.json').read_text())['passed']
 root=R/'data/pair-sequence-r0-results';a=np.load(R/'data/learning/sequences.npz');meta=json.loads((R/'data/pair-sequence/rotation0/schema.json').read_text());expected=meta['rotations'][0]['test'];arms=[]
 for fold in (0,1):
  one=np.load(root/f'fold{fold:02}-horizon01-predictions.npz');six=np.load(root/f'fold{fold:02}-horizon16-predictions.npz');full=np.load(root/f'fold{fold:02}-test-predictions.npz');ids=full['case_indices'];assert ids.tolist()==expected and np.array_equal(ids,one['case_indices']) and np.array_equal(ids,six['case_indices'])
  ramp=np.sinh(full['normalized_rollout']*full['std']+full['mean'])*full['physical_scales'];assert np.allclose(ramp[:,0],one['predicted_physical'][:,0],rtol=.002,atol=.002) and np.allclose(ramp[:,15],six['predicted_physical'][:,0],rtol=.002,atol=.002)
  arms.append(np.concatenate([ramp[:,:15],six['predicted_physical']],axis=1))
 assert len(expected)==208;records=[];targets=np.arange(1,91);origins=targets-np.minimum(targets,16)
 for j,i in enumerate(expected):
  state=a['state'][i];values=np.stack([state[1:],state[origins],arms[0][j],arms[1][j]]);assert values.shape==(4,90,4) and np.isfinite(values).all();case=meta['cases'][i];key=case['physical_key']
  records.append(dict(index=int(i),case=case['case'],fold=0,source=case['source'],height=key[0],loading=key[2],wind=key[3],angle=key[4],water=float(state[0,0]),fuel=float(state[0,1]),time=a['time'][i,1:].tolist(),values=values.tolist()))
 records.sort(key=lambda x:x['index']);D=R/'data/pair-gallery';D.mkdir(exist_ok=True)
 for page in range((len(records)+2)//3):(D/f'page-{page}.js').write_text('window.receivePage('+str(page)+','+json.dumps(records[page*3:page*3+3],separators=(',',':'),allow_nan=False)+');')
 template=(R.parent/'35_surrogate_diagnostics/attempt24/gallery.html').read_text().replace('__TOTAL__','208')
 template=template.replace('Test fire scenarios','Stride-one · plain and gated').replace('Held-out scenarios · water, fuel, gas & heating','Stride-one · plain and gated')
 template=template.replace('Held-out predictions across all 10 test folds · Gated GRU','Shared test fold 1 (rotation 0) · 208 histories / 204 configurations · plain and soft-gated GRUs · stride-one training')
 template=template.replace('First predicted change × steps','Plain GRU').replace('Recursive model','Soft-gated GRU').replace('data-series="2" aria-pressed="false"','data-series="2" aria-pressed="true"').replace('visible=[true,false,false,true]','visible=[true,false,true,true]')
 template=template.replace('Cone schematic, not a species; no trunk implied.','Cone schematic, not a species; no trunk implied. Generic3m crowns above2m base;1600weightedparticles;0.5m mesh;1500°C20s ignition; no buildings/embers/physical validation. Single split, not ten-fold aggregate.')
 (D/'index.html').write_text(template)
 (D/'verification.json').write_text(json.dumps(dict(histories=208,configurations=204,pages=70,rotation=0,arms=['control','gated'],shared_test_indices_exact=True,saved_forecasts_only=True,initial_ramp_endpoint_checks=True,scope='First15steps from saved autonomous rollout, thereafter rolling16-step forecasts; approximately32s. Scorecard headline remains16s.'),indent=2)+'\n')
 print('Built new70page shared-test gallery for both models')
if __name__=='__main__':main()

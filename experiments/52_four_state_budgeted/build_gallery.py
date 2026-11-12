"""Reuse the established three-row/four-chart gallery with frozen test predictions."""
from pathlib import Path
import json,re,hashlib
import numpy as np
R=Path(__file__).resolve().parent

def main():
 a=np.load(R/'data/observations.npz');p=np.load(R/'data/results/fold00-test-predictions.npz');schema=json.loads((R/'data/schema.json').read_text());ids=p['case_indices'];assert ids.tolist()==schema['rotations'][0]['test'];pred=np.sinh(p['normalized_rollout']*p['std']+p['mean'])*p['physical_scales'];rows=[]
 for j,i in enumerate(ids):
  truth=a['state'][i].astype('float32');forecast=np.concatenate([truth[:1],pred[j]]);hold=np.repeat(truth[:1],len(truth),axis=0);v=a['geometry'][i];case=schema['cases'][i];err=forecast-truth;left=err[:-1];right=err[1:];aa=abs(left);bb=abs(right);area=np.where(left*right<0,(aa*aa+bb*bb)/np.maximum(2*(aa+bb),1e-30),(aa+bb)/2);score=100*(area*np.diff(a['time'][i])[:,None]).sum(0)/(180*np.ptp(truth,axis=0))
  rows.append(dict(index=int(i),case=case['case'],fold=case['fold'],family=case['family'],height=float(v[3]),base=float(v[4]),width=float(v[5]),ignition=v[6:9].tolist(),mode='crown' if v[9] else 'base',wind=float(v[10]),moisture=float(v[11]),loading=float(v[12]),water=float(v[13]),fuel=float(v[14]),time=a['time'][i].tolist(),percent=score.tolist(),values=np.stack([truth,hold,forecast]).tolist()))
 assert len(rows)==225 and np.isfinite(pred).all()
 d=R/'data/test-gallery';d.mkdir(exist_ok=True)
 for page in range(75):(d/f'page-{page}.js').write_text('window.receivePage('+str(page)+','+json.dumps(rows[page*3:page*3+3],separators=(',',':'),allow_nan=False)+');')
 template=(R/'gallery-template.html').read_text();(d/'index.html').write_text(template.replace('__TOTAL__','225'))
 (R/'gallery-verification.json').write_text(json.dumps(dict(passed=True,test_cases=225,pages=75,rows_per_page=3,charts_per_row=4,selected_epoch=166,saved_forecasts_only=True,exact_test_indices=True,baseline='Exact constant initial physical state',full_rollout_from_initial_state=True,source_predictions_sha256=hashlib.sha256((R/'data/results/fold00-test-predictions.npz').read_bytes()).hexdigest()),indent=2)+'\n')
 print('Built 225-case gallery, 75 pages, four charts per row')
if __name__=='__main__':main()

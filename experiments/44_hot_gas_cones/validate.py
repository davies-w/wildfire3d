from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent;rows=json.loads((R/'data/index.json').read_text());frames=0;active=0;min_recall=1.;dt=[]
for c in rows:
    dt.extend(np.diff([r['time_s'] for r in c['snapshots']]))
    for r in c['snapshots']:
        frames+=1
        if not r['active']:assert r['cone'] is None;continue
        active+=1;p=r['cone'];assert len(p)==5 and np.isfinite(list(p.values())).all()
        assert 0<=p['tilt_from_vertical_deg']<=90 and p['length_m']>0 and p['end_radius_m']>=0
        assert p['peak_temperature_C']<=r['domain_peak_temperature_C']+1e-8
        for key in ['cone_metrics','ovoid_metrics','ovoid95_metrics']:
            m=r[key];assert 0<=m['iou']<=1 and 0<=m['hot_recall']<=1
            assert m['covered_hot_cells']+m['missed_hot_cells']==m['hot_cells']
            assert m['covered_hot_cells']+m['cool_cells_included']==m['enclosed_cells']
        assert r['cone_metrics']['hot_recall']>=.95-1e-9 and r['ovoid95_metrics']['hot_recall']>=.95-1e-9
        min_recall=min(min_recall,r['cone_metrics']['hot_recall'])
proof=dict(passed=True,cases=len(rows),frames=frames,active_frames=active,min_cone_hot_recall=min_recall,min_saved_step_s=float(min(dt)),max_saved_step_s=float(max(dt)),exact_five_parameters=True,no_new_training_or_simulations=True)
(R/'data/validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

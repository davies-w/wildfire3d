"""Train-only audit of exact overlapping-window multiplicities and phase weights."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
def multiplicity(h):
 m=np.zeros(90)
 for j in range(91-h):m[j:j+h]+=1
 assert m.sum()==h*(91-h) and (m>0).all()
 return m

def main():
 root=R/'data/pair-sequence/rotation0';meta=json.loads((root/'schema.json').read_text());a=np.load(root/'data/sequences.npz');ids=np.array(meta['rotations'][0]['train']);assert not set(ids)&set(meta['rotations'][0]['validation']+meta['rotations'][0]['test'])
 state=a['state'][ids];times=a['time'][ids];cfg=a['configuration'][ids];active=(state[:,1:,2]>1e-6)|(np.abs(np.diff(state[:,:,:2],axis=1)).max(-1)>1e-5);weights=np.zeros_like(active,dtype=float)
 for j,c in enumerate(cfg):
  ac=active[j];na=ac.sum();nq=90-na;groups=int(na>0)+int(nq>0);rep=(cfg==c).sum();weights[j]=np.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/rep
 masks={'first10s':times[:,1:]<=10.2,'source_on20s':times[:,1:]<=20.2,'startup32s':times[:,1:]<=32.2,'after90s':times[:,1:]>90.2,'active':active,'quiet':~active}
 out={'train_histories':len(ids),'train_configurations':len(np.unique(cfg)),'validation_or_test_used_in_statistics':False,'scope':'Exact coefficient exposure, not measured gradients or causal proof. Phase masks overlap. Source timing tolerances only classify actual timestamps.','horizons':{}}
 for h in [1,8,16,32]:
  m=multiplicity(h);effective=weights*m[None];normalizer=effective.sum()/weights.sum();corrected=weights*normalizer;ratio=normalizer/m
  # A correction multiplying each target by this factor cancels multiplicity exactly.
  assert np.allclose(effective*ratio,corrected)
  def shares(w):return {k:float((w*v).sum()/w.sum()) for k,v in masks.items()}
  out['horizons'][str(h)]={'windows_per_history':91-h,'first_transition_appearances':int(m[0]),'middle_transition_appearances':int(m[44]),'zero_prefix_window_fraction':1/(91-h),'raw_phase_shares':shares(effective),'multiplicity_corrected_phase_shares':shares(corrected),'correction_multiplier_min_max':[float(ratio.min()),float(ratio.max())],'multiplicity':m.tolist()}
 # Source condition support, balanced by configuration.
 groups={}
 for n in ids:
  c=meta['cases'][int(n)];groups.setdefault(int(a['configuration'][n]),c['physical_key'])
 out['train_condition_counts']={name:{str(v):sum(key[k]==v for key in groups.values()) for v in sorted(set(key[k] for key in groups.values()))} for k,name in enumerate(['height','moisture','loading','wind','angle'])}
 out['input_sha256']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'schema.json',root/'coverage-plan.json',root/'worker.py']}
 (R/'results/training-exposure-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['train_condition_counts','input_sha256']},indent=2))
if __name__=='__main__':main()

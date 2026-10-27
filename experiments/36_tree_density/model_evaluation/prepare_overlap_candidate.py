"""User-requested stride-one curriculum candidate and offline workload audit."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/report-publication.json').read_text())['report_only']
 src=R/'data/model-training/worker.py';old=src.read_text();before='for j in range(0,90,h)';after='for j in range(0,91-h)'
 assert old.count(before)==1
 new=old.replace(before,after);assert new.replace(after,before)==old
 dst=R/'data/model-overlap-candidate';dst.mkdir(exist_ok=True)
 (dst/'worker.py').write_text(new);(dst/'model.py').write_bytes((R/'data/model-training/model.py').read_bytes())
 checks={}
 for h in [1,8,16,32]:
  starts=list(range(91-h));assert len(starts)==91-h and starts[0]==0 and starts[-1]+h==90
  assert all(b-a==1 for a,b in zip(starts,starts[1:]));checks[str(h)]={'full_windows_per_history':len(starts),'first_origin':0,'last_origin':starts[-1],'short_tail_windows':0}
 p=json.loads((R/'results/model-training-runtime-plan03.json').read_text());f=json.loads((R/'data/grouped-folds.json').read_text());projections={}
 for epochs in [100,400]:
  batches={h:sum(math.ceil(len(r['train'])*(91-h)/256) for r in f['rotations'])*n for h,n in [(1,20),(8,20),(16,20),(32,epochs-60)]}
  seconds=2*(sum(batches[h]*p['batch_seconds_upper_observed'][str(h)] for h in batches)+10*epochs*p['evaluation_seconds_per_epoch'])+10*epochs*2+1800
  projections[str(epochs)]={'updates_by_horizon':batches,'conservative_hours':seconds/3600,'compute_ceiling_usd_at_0_80_hour':seconds/3600*.8}
 result={'prepared_only':True,'launched':False,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest(),'only_change':{'before':before,'after':after},'curriculum_unchanged':[1,8,16,32],'window_checks':checks,'projections':projections,'limitations':['Timing reuses prior GPU batch measurements, not a full stride-one epoch measurement.','Overlapping full windows repeat interior transitions more often; no compensating loss reweighting is silently introduced. Existing active/quiet and replica weights remain unchanged.','No partial tail windows in the rerun.','All architecture, optimizer, learning rate, selection and fold choices remain frozen.','Worst-case estimate needs budget reconciliation and bounded continuation design; not launch approval.']}
 (R/'results/model-overlap-candidate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

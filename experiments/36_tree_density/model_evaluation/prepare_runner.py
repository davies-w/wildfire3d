"""Adapt the prior worker's dataset cardinality and reporting only. No fitting."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[1]
OLD=R.parent/'35_surrogate_diagnostics/attempt25'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 original=(OLD/'worker.py').read_text()
 patches=[
 ("assert external.shape==(520,90,9)","assert external.shape==(2080,90,9)\nassert len(meta['rotations'])==10\nassert all(len(set(meta['cases'][i]['fold'] for i in rot['train']))==8 for rot in meta['rotations'])"),
 ("weights=torch.zeros(520,90,device=device)","weights=torch.zeros(2080,90,device=device)"),
 ("rotation['training_fold_count']","8"),
 ("rot['training_fold_count']","8"),
 ("assert len(reports)==8","assert len(reports)==10"),
 ("Plain four-state GRU learning curve: eight nested training sizes, fixed validation/test; scorecard-v1; one split, previously examined data.","Plain four-state GRU on2080 histories: ten grouped8/1/1 rotations; frozen scorecard-v1; previously examined reshuffled data, not pristine. More histories change optimizer updates per epoch; not compute-matched."),
 ("folds=8))","folds=10))")]
 adapted=original
 for before,after in patches:
  assert adapted.count(before)==1,(before,adapted.count(before))
  adapted=adapted.replace(before,after)
 reversed_text=adapted
 for before,after in reversed(patches):
  assert reversed_text.count(after)==1 if after!='8' else True
  # Numeric replacements require their report field context for unique reversal.
  if after=='8':
   marker='training_fold_count=8'
   pos=reversed_text.rfind(marker) if before.startswith("rot[") else reversed_text.find(marker)
   assert pos>=0
   reversed_text=reversed_text[:pos]+reversed_text[pos:].replace(marker,'training_fold_count='+before,1)
  else:reversed_text=reversed_text.replace(after,before,1)
 assert reversed_text==original,'Unexpected science or training-loop change'
 ast.parse(adapted)
 dest=R/'data/model-runner';dest.mkdir(exist_ok=True)
 (dest/'worker.py').write_text(adapted)
 model=(OLD/'model.py').read_bytes();(dest/'model.py').write_bytes(model)
 report={'source_worker_sha256':sha(original.encode()),'adapted_worker_sha256':sha(adapted.encode()),'model_sha256':sha(model),'model_byte_identical':True,'reversible_only_listed_changes':True,'patches':[{'before':a,'after':b} for a,b in patches],'training_launched':False,'launch_ready':False,'remaining':'Full1560 data audit and2080 merge, leakage/report/normalization checks, private transport and measured runtime/budget plan required. No coverage-plan or launch supplied by this stage.'}
 (R/'results/model-runner-adaptation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='patches'}))
if __name__=='__main__':main()

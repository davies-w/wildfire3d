from pathlib import Path
import json,tarfile,hashlib
import numpy as np
R=Path(__file__).parent;D=R/'data/cloud'
def main():
 done=json.loads((D/'complete.json').read_text());assert done['success'];assert hashlib.sha256((D/'outputs.tar').read_bytes()).hexdigest()==done['sha256'];assert not any(json.loads((R/'results/cleanup.json').read_text()).values())
 with tarfile.open(D/'outputs.tar') as tar:tar.extractall(R/'data/extracted',filter='data')
 report=json.loads((D/'sequence-evaluation.json').read_text());previous=json.loads((R.parent/'29_single_tree_heads/results/previous-evaluation.json').read_text());seq=report['summary']['validation'];base=previous['summary']['validation'];objective=report['selected_autonomous_validation_objective'];baseline=report['snapshot_baseline_full_objective'];peak=seq['all']['peak_error_C'];basepeak=base['all']['peak_error_C'];passed=objective<=.95*baseline and peak<=1.1*basepeak
 diagnostic=dict(autonomous_objective=objective,snapshot_objective=baseline,ratio=objective/baseline,teacher_forced_objective=float(np.mean([d['teacher_forced_one_step_objective'] for d in report['diagnostics']])),validation_sequence=seq,validation_snapshot=base,passed_predeclared_gate=passed,fit_seconds=report['training']['fit_seconds'],inference_seconds=report['inference_median_seconds_including_cpu_decode'],limitations=['Fixed identical geometry; no geometry generalization','Repeated development validation, no fresh test','2m recurrent/material state with 0.5m decoded fields','Monotone wet+solid mass is not dry-fuel state','Short training rollouts versus 90-step autonomous evaluation'])
 (R/'results/decision.json').write_text(json.dumps(diagnostic,indent=2));print(json.dumps({k:v for k,v in diagnostic.items() if not isinstance(v,(dict,list))},indent=2))
if __name__=='__main__':main()

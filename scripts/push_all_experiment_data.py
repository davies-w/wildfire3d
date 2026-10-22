"""Push recorded experiment outputs to local DVC mirror without rerunning stages."""
import json,subprocess,time
from pathlib import Path
import yaml
R=Path(__file__).resolve().parents[1];targets=[]
for p in sorted((R/'experiments').rglob('dvc.lock')):
 if 'data' in p.relative_to(R/'experiments').parts:continue
 for stage,spec in (yaml.safe_load(p.read_text()) or {}).get('stages',{}).items():
  if any(o.get('md5') for o in spec.get('outs',[])):targets.append(str(p.with_name('dvc.yaml').relative_to(R))+':'+stage)
for p in sorted((R/'experiments').rglob('*.dvc')):targets.append(str(p.relative_to(R)))
report={'started_unix':time.time(),'targets':targets,'completed':[],'failures':[]}
out=R/'docs/all-experiment-archive-status.json'
for t in targets:
 p=subprocess.run([str(R/'.venv/bin/dvc'),'push','-r','mirror',t],cwd=R,text=True,capture_output=True)
 if p.returncode:report['failures'].append({'target':t,'error':p.stderr[-3000:]})
 else:report['completed'].append(t)
 out.write_text(json.dumps(report,indent=2)+'\n')
report['finished_unix']=time.time();out.write_text(json.dumps(report,indent=2)+'\n');print(len(targets),'targets;',len(report['failures']),'failures',flush=True)

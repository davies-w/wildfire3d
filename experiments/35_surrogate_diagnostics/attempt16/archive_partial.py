"""Preserve a failed run after its existing collector finishes; never launches compute."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path(__file__).resolve().parent;repo=R.parents[2]
def run(args):subprocess.run([str(x) for x in args],cwd=repo,check=True)
def main():
 assert (R/'results/collection-error.json').exists()
 assert not any(json.loads((R/'results/cleanup.json').read_text()).values())
 assert json.loads((R/'results/permission-removed.json').read_text())['removed']
 files=sorted((R/'data/collected').glob('*'));inventory={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files if p.is_file()}
 reports=[]
 for p in sorted((R/'data/collected').glob('fold*-report.json')):
  x=json.loads(p.read_text());assert (R/f"data/collected/fold{x['fold']:02}-selected.pt").exists();reports.append({k:x[k] for k in ['fold','rotation','kind','epochs','selected_epoch','stop_reason']})
 assert len(reports)==15
 assert 'fold15-epoch373.pt' in inventory
 (R/'results/partial-inventory.json').write_text(json.dumps(dict(files=inventory,completed_models=reports,resume_checkpoint='fold15-epoch373.pt',tests_not_started=True),indent=2))
 dvc=repo/'.venv/bin/dvc';stage=str(R/'dvc.yaml')
 run([dvc,'commit','-f',stage+':cloud_collect']);run([dvc,'push','-r','mirror',stage+':prepare_data',stage+':package',stage+':cloud_collect'])
 run([repo/'.venv/bin/hf','buckets','sync',repo/'FDS/hf_dvc_mirror','hf://buckets/wdavies/dvc_storage/wildfire3d','--no-delete','--ignore-existing'])
 run([repo/'.venv/bin/python',repo/'scripts/verify_public_model_archive.py'])
 proof=json.loads((repo/'experiments/33_representation_loss/results/public-archive-verification.json').read_text())
 (R/'results/partial-archive-complete.json').write_text(json.dumps(dict(partial_preserved=True,experiment_complete=False,files=len(inventory),completed_models=15,resume_checkpoint='fold15-epoch373.pt',public_archive=proof,completed_unix=time.time()),indent=2))
 run(['git','add',R,repo/'experiments/33_representation_loss/budget.json',repo/'experiments/33_representation_loss/results/public-archive-verification.json',repo/'docs/billing-audit-2026-10-23/runtime-reconciliation.json',repo/'docs/billing-audit-2026-10-23/vm-runtime.json'])
 run(['git','commit','-m','Preserve interrupted memory comparison checkpoints and diagnosis']);run(['git','push'])
if __name__=='__main__':main()

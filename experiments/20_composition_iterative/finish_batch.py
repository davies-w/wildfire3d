"""One-shot local completion: wait, verify cleanup, fetch, preserve and diagnose."""
import argparse,json,subprocess,time
from pathlib import Path
import control
ROOT=Path(__file__).resolve().parent
PYTHON=ROOT.parents[1]/'.venv/bin/python';DVC=ROOT.parents[1]/'.venv/bin/dvc'
def main(name):
    folder=ROOT/'batches'/name;failures=0
    while True:
        try:s=control.status(name);failures=0
        except Exception:
            failures+=1
            if failures>=5:raise
            time.sleep(60);continue
        if s['state']!='ACTIVE':break
        time.sleep(60)
    cleanup=json.loads((folder/'results/cleanup.json').read_text());assert not any(cleanup.values()),'Cloud resources remain; inspect cleanup'
    control.fetch(name)
    (folder/'restore.py').write_text("import tarfile\nfrom pathlib import Path\np=Path(__file__).resolve().parent\nwith tarfile.open(p/'data/cloud-evidence.tar.gz') as t:t.extractall(p/'data',filter='data')\n")
    (folder/'dvc.yaml').write_text('''stages:
  restore:
    cmd: ../../../../.venv/bin/python restore.py
    deps:
    - restore.py
    - data/cloud-evidence.tar.gz
    outs:
    - data/cloud
  diagnose:
    cmd: ../../../../.venv/bin/python ../../analyze_batch.py '''+name+'''
    deps:
    - ../../analyze_batch.py
    - batch.json
    - data/cloud
    - ../../../../FDS/install/bin/fds2ascii
    outs:
    - data/boundary
    - results/diagnosis.json:
        cache: false
''')
    subprocess.run([str(DVC),'add','data/cloud-evidence.tar.gz'],cwd=folder,check=True)
    subprocess.run([str(DVC),'commit','-f','restore'],cwd=folder,check=True)
    subprocess.run([str(DVC),'repro','diagnose'],cwd=folder,check=True)
    campaign=json.loads((folder/'data/cloud/campaign.json').read_text())
    report=dict(state='ready_for_review',campaign_status=campaign['status'],error=campaign.get('error'),completed=len(campaign['results']),cleanup_verified=True)
    (folder/'results/completion.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');main(p.parse_args().batch)

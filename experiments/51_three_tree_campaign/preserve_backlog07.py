"""Serial bounded scientific preservation from the current pinned proof inventory."""
from cloud07 import *
import argparse
import shutil
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--max-groups',type=int,default=24)
args=parser.parse_args()
assert 1<=args.max_groups<=24
with (P/'backlog-preservation.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for _ in range(args.max_groups):
  receipts={f.stem.replace('preservation-','') for f in P.glob('preservation-group*.json')}
  pending=[f.name for f in P.glob('collection-group*.json') if f.stem.replace('collection-','') not in receipts]
  assert not pending,('Inspect pending collection before proceeding',pending)
  proofs=json.loads((P/'worker-proofs.json').read_text())
  jobs={v['name'].split('/')[-2] for v in proofs if '/job-status.json.' in v['name'] and v['proof'].get('status',{}).get('state')=='SUCCEEDED'}
  eligible=[v for v in proofs if v['name'].endswith('/completion.json') and v['proof']['passed'] and v['name'].split('/')[-3] in jobs and not (R/'data/completed07'/v['name'].split('/')[-3]/'proof.json').exists()]
  if not eligible:print('BACKLOG COMPLETE for pinned inventory',flush=True);break
  while shutil.disk_usage(R).free<12*1024**3:
   candidates=sorted(int(g.removeprefix('group')) for g in receipts if not (P/f'eviction-{g}.json').exists())
   if not candidates:break
   subprocess.run([sys.executable,str(R/'evict_preserved07.py'),'--group',str(candidates[0]),'--apply'],cwd=R,check=True)
  if shutil.disk_usage(R).free<12*1024**3:print('STOP local disk guard; preserve existing outputs',flush=True);break
  group=1+max([int(x.removeprefix('group')) for x in receipts],default=0)
  print('START group',group,'eligible',len(eligible),flush=True)
  subprocess.run([sys.executable,str(R/'preserve_completed07.py'),'--group',str(group)],cwd=R,check=True)
  receipt=json.loads((P/f'preservation-group{group:03d}.json').read_text())
  assert receipt['passed'] and receipt['remote_size_and_xet_verified'] and receipt['directory_anonymous_readback']
  subprocess.run(['git','add','dvc.yaml','dvc.lock'],cwd=R,check=True)
  subprocess.run(['git','commit','-m',f'Preserve verified Experiment 51 backlog group {group:03d}'],cwd=R,check=True)
  branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
  subprocess.run(['git','push','origin','HEAD'],cwd=R,check=True)
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
  remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=R,text=True).split()[0]
  assert head==remote
  subprocess.run([sys.executable,str(R/'summarize_progress07.py')],cwd=R,check=True,stdout=subprocess.DEVNULL)
  save('backlog-preservation-progress.json',dict(group=group,git=head,verified_complete=json.loads((P/'progress-summary.json').read_text())['verified_complete']))
  print('VERIFIED group',group,'git',head,flush=True)

"""Read only checkpoint/replay proofs, never model test outcomes or submit compute."""
from pathlib import Path
import sys,json,base64,hashlib,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,save,download_summary
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--rotation',type=int,choices=(0,1),default=0);rotation=parser.parse_args().rotation
prefix='gs://'+BUCKET+f'/density36/pair-sequence01/rotation{rotation}/'
names=subprocess.run([G,'storage','ls',prefix],capture_output=True,text=True,check=True).stdout.splitlines();names={n.rsplit('/',1)[-1] for n in names}
proofs={}
for name in ('optimizer-resume-check.json','fold00-checkpoint-replay.json','fold01-checkpoint-replay.json'):
 if name not in names:continue
 meta=gc('storage','objects','describe',prefix+name);dest=R/'results'/(f'pair-sequence-r{rotation}-startup-'+name);download_summary(prefix+name,dest);data=dest.read_bytes();assert len(data)==int(meta['size']) and base64.b64encode(hashlib.md5(data).digest()).decode()==meta['md5_hash'];proof=json.loads(data);assert proof['passed']
 if name=='optimizer-resume-check.json':assert {x['kind'] for x in proof['checks']}=={'control','gated'} and all(x['nonempty_optimizer'] and x['next_update_bitwise_equal'] for x in proof['checks'])
 else:assert proof['optimizer_nonempty'] and proof['epoch']==1
 proofs[name]=dict(sha256=hashlib.sha256(data).hexdigest(),generation=meta['generation'],proof=proof)
report=dict(proofs=proofs,bootstrap_error_present='bootstrap-error.txt' in names,test_outcomes_not_read=True,training_started='fold00-epoch001.pt' in names)
report['rotation']=rotation;report['source_prefix']=prefix
save(f'results/pair-sequence-r{rotation}-startup-audit.json',report);print(json.dumps(report))

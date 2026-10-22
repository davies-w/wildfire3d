"""Source-removal causal control: preserve ignitor and unlit receiver exactly."""
import copy,hashlib,json,re,os,subprocess
from scene import ROOT
from sampling_test import BINARY
p=ROOT/'component-development.json';doc=json.loads(p.read_text());name='b21_transfer_hot_source_control';ledger=json.loads((ROOT/'budget-overnight.json').read_text());assert name not in ledger['reservations']
c=copy.deepcopy(next(c for c in doc['cases'] if c['case']=='b21_transfer_hot'));s=(ROOT/'decks/b21_transfer_hot.fds').read_text().replace("CHID='b21_transfer_hot'",f"CHID='{name}'")
removed=[]
def filt(m):
 block=m[0]
 if block.startswith('&INIT') and "XYZ=13.5,12,3," in block and "contact ignitor" not in block:removed.append(block);return ''
 if block.startswith('&DEVC') and "ID='v0 " in block:return ''
 return block
s=re.sub(r'&(?:INIT|DEVC)\b.*?/',filt,s,flags=re.S);assert len(removed)==4
c.update(case=name,split='diagnostic',family='source_removal',canopies=[c['canopies'][1]],control_note='Removed source vegetation only; original artificial source retained at13.5,12,3.1. Receiver remains uninitialized. Not a training configuration.',deck_sha256=hashlib.sha256(s.encode()).hexdigest())
(ROOT/'decks'/f'{name}.fds').write_text(s);doc['cases']=[v for v in doc['cases'] if v['case']!=name]+[c];p.write_text(json.dumps(doc,indent=2))
w=ROOT/'data/component_preflight'/name;w.mkdir(exist_ok=True);(w/'check.fds').write_text(s.replace('T_END=90','T_END=.6').replace('DT_RESTART=10.','DT_RESTART=100000.'))
with (w/'run.log').open('w') as f:r=subprocess.run([str(BINARY),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=300)
assert r.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower()
(ROOT/'results/transfer-source-control-preflight.json').write_text(json.dumps(dict(case=name,passed=True,removed_source_classes=len(removed),deck_sha256=c['deck_sha256'],allowance_usd=.25),indent=2));print('PASS',name)

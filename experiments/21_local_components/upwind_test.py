"""One separately authorized $0.15 follow-up. No automatic retries or extra runs."""
import ast,base64,csv,hashlib,json,os,re,subprocess,time,urllib.request
from pathlib import Path
import yaml
from control import gc,ROOT
NAME='a21_single_upstream';FOLDER=ROOT/'jobs'/NAME

def prepare():
 FOLDER.mkdir(exist_ok=True)
 old=(ROOT/'decks/a21_single.fds').read_text();s=old.replace("CHID='a21_single'",f"CHID='{NAME}'")
 assert s.count("XB=10,12,11,13,0,0, SURF_ID='IGNITOR'")==1
 s=s.replace("XB=10,12,11,13,0,0, SURF_ID='IGNITOR'","XB=7.5,9.5,11,13,0,0, SURF_ID='IGNITOR'").replace('SAMPLING_FACTOR=10','SAMPLING_FACTOR=1').replace('DT_PART=5.','DT_PART=1.')
 extra=[]
 for fuel in ('foliage','small roundwood','medium roundwood','large roundwood'):
  extra.append(f"&DEVC ID='fuel_release {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', XB=0,24,0,24,0,24, SPATIAL_STATISTIC='SURFACE INTEGRAL' /")
 s=s.replace('&TAIL /','\n'.join(extra)+'\n&TAIL /');(ROOT/'decks'/f'{NAME}.fds').write_text(s)
 r=json.loads((ROOT/'data/cloud/a21_single/result.json').read_text());keys=['kind','direction','cells','domain_m','dx_m','horizon_s','variant','profile','source_kw','source_energy_kj','nominal_dry_fuel_kg','canopy_patches'];r={k:r[k] for k in keys};r.update(case=NAME,deck_sha256=hashlib.sha256(s.encode()).hexdigest(),source_center_x_m=8.5)
 (FOLDER/'case.json').write_text(json.dumps(r,indent=2))
 w=ROOT/'data/upwind_preflight';w.mkdir(exist_ok=True);(w/'check.fds').write_text(s.replace('T_END=180','T_END=1.05'))
 with (w/'run.log').open('w') as log:p=subprocess.run([str(ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=log,stderr=subprocess.STDOUT,timeout=180)
 assert p.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower(),(w/'run.log').read_text()[-3000:]
 with (w/(NAME+'_devc.csv')).open() as f:
  it=csv.reader(f);next(it);ks=next(it);rows=list(it);assert len(rows)>=2 and sum(k.startswith('fuel_release') for k in ks)==4
 workflow=yaml.safe_load((ROOT/'jobs/a21_single/workflow.yaml').read_text());task=workflow['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec'];b=task['runnables'][0]['container']['commands'][1]
 payload=next(ast.literal_eval(n.value) for n in ast.parse(b).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='payload' for t in n.targets));payload={k:base64.b64decode(v).decode() for k,v in payload.items()};payload.pop('decks/a21_single.fds');payload[f'decks/{NAME}.fds']=s;payload['case.json']=json.dumps(r);payload['runner.py']=payload['runner.py'].replace("'a21_single/'",repr(NAME+'/'))
 for k,v in payload.items():
  if k.endswith('.py'):compile(v,k,'exec')
 enc={k:base64.b64encode(v.encode()).decode() for k,v in payload.items()};task['runnables'][0]['container']['commands'][1]="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(enc)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
 raw=json.dumps(workflow).replace('c21-a21-single','c21-a21-single-upstream').replace('components21/a21_single/','components21/'+NAME+'/');workflow=json.loads(raw);(FOLDER/'workflow.yaml').write_text(yaml.safe_dump(workflow,sort_keys=False))
 (FOLDER/'spec.json').write_text(json.dumps(dict(case=NAME,wave=3,workflow='fds-c21-a21-single-upstream',allowance_usd=.15,reserved_vm_hours=1,deck_sha256=r['deck_sha256']),indent=2))
 (ROOT/'results/upwind-preflight.json').write_text(json.dumps(dict(passed=True,device_rows=len(rows),new_fuel_release_channels=4,deck_sha256=r['deck_sha256']),indent=2));print('Prepared and startup-checked upwind test',flush=True)
def launch():
 ledger=ROOT/'budget-upwind.json';assert not ledger.exists(),'Already reserved; never resubmit'
 assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1')
 for w in gc('workflows','list','--location=us-central1'):
  assert not gc('workflows','executions','list',w['name'].split('/')[-1],'--location=us-central1','--filter=state=ACTIVE')
 raw=urllib.request.urlopen('https://cloud.google.com/spot-vms/pricing?hl=en',timeout=45).read().decode();i=raw.index('c3-standard-4');price=float(re.search(r'\$(\d+\.\d+)',re.sub('<[^>]+>',' ',raw[i:i+1000]))[1]);assert price<=.08;assert 'aria-selected="true" data-value="Iowa (us-central1)"' in raw[max(0,i-100000):i]
 spec=json.loads((FOLDER/'spec.json').read_text());sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy',spec['workflow'],'--location=us-central1','--source='+str(FOLDER/'workflow.yaml'),'--service-account='+sa)
 assert yaml.safe_load(gc('workflows','describe',spec['workflow'],'--location=us-central1')['sourceContents'])==yaml.safe_load((FOLDER/'workflow.yaml').read_text())
 record=dict(total_authorized_usd=.15,scope='One upwind-burner follow-up; separately authorized by user go',reservation=spec,price_usd_per_vm_hour=price,state='reserved',automatic_retries=False,reserved_unix=time.time());ledger.write_text(json.dumps(record,indent=2))
 result=gc('workflows','execute',spec['workflow'],'--location=us-central1');(FOLDER/'execution.json').write_text(json.dumps(result,indent=2));record.update(state='submitted',execution=result['name']);ledger.write_text(json.dumps(record,indent=2));print(result['name'],flush=True)
if __name__=='__main__':
 import sys
 globals()[sys.argv[1]]()

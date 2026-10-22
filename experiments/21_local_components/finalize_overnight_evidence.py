"""Read-only cloud audit and common-time evidence; retain all budget reservations."""
import datetime,fcntl,hashlib,json
import numpy as np
from scene import ROOT
from control import gc
from finish_sampling import read
freeze=json.loads((ROOT/'results/component-test-prediction-freeze.json').read_text())
for name,digest in freeze['files'].items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
inventory={k:gc(*args) for k,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
assert not any(inventory.values()),'Cloud resources remain'
names=['overnight21_grid_coarse_v2','overnight21_grid_fine_v2','overnight21_grid_fine_bare_v2']
common={}
for name in names:
 d=read(name);t=d['Time'];assert t[-1]>=38
 # DEVC surface-integral values are interval averages in kg/s.
 weights=np.maximum(0,np.minimum(t[1:],38)-np.maximum(t[:-1],22))
 common[name]={tag:float(np.sum(sum(v for k,v in d.items() if k.startswith(tag+' fuel '))[1:]*weights)) for tag in ['small','large']}
fine=ROOT/'data/cloud/overnight21_grid_fine_v2'
m=json.loads((fine/'checkpoint-manifest.json').read_text());assert m['files']
for f in m['files']:assert hashlib.sha256((fine/f['name']).read_bytes()).hexdigest()==f['sha256']
r=json.loads((fine/'result.json').read_text());assert r['stopped_by_budget'] and not r['full_horizon'] and r['returncode']==0
with (ROOT/'data/overnight-budget.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 p=ROOT/'budget-overnight.json';b=json.loads(p.read_text());old=b['reserved_usd'];entry=b['reservations']['overnight21_grid_fine_v2']
 assert r['deck_sha256']==entry['case']['sha256']
 entry['state']='partial_horizon_cleanup_verified'
 entry['completion_evidence']='results/overnight21_grid_fine_v2-collected.json'
 entry['physical_seconds_reached']=r['physical_seconds_reached']
 assert b['reserved_usd']==old
 p.write_text(json.dumps(b,indent=2))
out=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inventory=inventory,frozen_hashes_verified=len(freeze['files']),checkpoint_files_verified=len(m['files']),fine_complete=False,fine_horizon_s=r['physical_seconds_reached'],common_fuel_window_s=[22,38],fuel_vapor_kg=common,reserved_usd=b['reserved_usd'],reservation_recycled=False,limitations='Partial38s fine run, not completed40s or physical validation. Fuel vapor release is not measured gas HRR; time-averaged gas slices provide separate combustion evidence. Generic10/16m canopy patches,20mm wood facade,artificial20s source; no trunks,groundcover,embers.')
(ROOT/'results/overnight-final-evidence.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

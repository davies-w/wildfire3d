"""Prepare (never launch) matched initialization diagnostics for the overnight decision."""
import hashlib,json,re
from scene import ROOT

def prepare():
 source=(ROOT/'decks/sampling21_dense.fds').read_text()
 # Keep the physical ring sources unchanged in all cases; vary gas-grid/sampling only.
 source=source.replace('T_END=90','T_END=40')
 extra="&SLCF PBY=18., QUANTITY='TEMPERATURE' /\n&SLCF PBY=18., QUANTITY='VELOCITY' /\n&SLCF PBY=18., QUANTITY='HRRPUV' /\n"
 source=source.replace('&TAIL /',extra+'&TAIL /')
 out=ROOT/'inputs/overnight_grid_candidates';out.mkdir(exist_ok=True)
 cases=[]
 for name,fine,bare,hours,allowance in [('overnight21_grid_coarse',False,False,2,.25),('overnight21_grid_fine',True,False,4,.50),('overnight21_grid_fine_bare',True,True,2,.25)]:
  s=source.replace("CHID='sampling21_dense'",f"CHID='{name}'")
  if fine:s=s.replace('IJK=48,48,48','IJK=96,96,96').replace('N_PARTICLES_PER_CELL=8','N_PARTICLES_PER_CELL=1')
  if bare:
   # Retain PART/SURF definitions and diagnostics, remove only vegetation INIT blocks.
   s=re.sub(r"&INIT\b(?:(?!/).)*?/",lambda m:'' if "PART_ID='contact ignitor'" not in m[0] else m[0],s,flags=re.S)
  assert s.count("SHAPE='RING'")==2
  p=out/(name+'.fds');p.write_text(s)
  cases.append(dict(case=name,path=str(p.relative_to(ROOT)),grid_m=.25 if fine else .5,vegetation_particles_per_cell=1 if fine else 8,vegetation_present=not bare,horizon_s=40,max_vm_hours=hours,allowance_usd=allowance,sha256=hashlib.sha256(s.encode()).hexdigest()))
 report=dict(status='prepared_not_launched_not_reserved',incremental_allowance_usd=sum(c['allowance_usd'] for c in cases),cases=cases,
 purpose='Resolve early initialization grid dependence with new large-canopy slices, and test direct artificial-source facade ignition on fine grid. These 40s tests do not replace full180s Stage A convergence/context validation.',
 controls='Original two1600-particle1500C rings, off20.1s/removed21s, unchanged3m/s wind and materials. Nominal vegetation particle number density matched coarse8/cell vs fine1/cell. Positions and cone voxelization are not identical.',
 required_before_launch=['Interpret stronger-source result first; do not duplicate cases unnecessarily.','Actual deck startup validation.','Matching Linux checkpoint/resume preflight within reserved VM runtime, gate main solve on success.','Use central budget-overnight.json reservations before submission and fit full worker allowance before end_unix.','Fine compressed archive allowance at least2GiB; increase upload timeout and ensure sufficient upload/cleanup margin.','Collector must filter its own job/VM labels if cases run concurrently; old collector asserts project-wide zero and cannot do that.'],
 analysis=['Raw facade boundary burning vs device traces, including matched fine bare control.','Separate canopy fuel release and mass after22s; no reliance on aggregate HRR.','Read y18 temperature/HRRPUV slices with fds2ascii before physical mechanism claims.','Compare same time windows and original facade error criteria; partial output remains censored.'])
 (ROOT/'results/overnight-grid-candidates.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':prepare()

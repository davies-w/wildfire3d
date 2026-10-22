"""Prepare, but never launch, minimal corrections suggested by existing evidence."""
import hashlib,json
from pathlib import Path
from rerun_contact import make
from scene import ROOT
folder=ROOT/'inputs/corrective_candidates';folder.mkdir(exist_ok=True)
# Isolate exterior domain from the building-mass change in prior comparisons.
c=dict(case='candidate_domain_only',kind='single',direction=270,expanded=True)
s,r=make(c)
extra="&OBST XB=16.5,24,8,16,0,6, SURF_ID='HOUSE', BNDF_OBST=T /"
assert s.count(extra)==1;s=s.replace(extra,'! Building geometry held identical to compact single case.')
(folder/(c['case']+'.fds')).write_text(s)
record=dict(case=c['case'],deck_sha256=hashlib.sha256(s.encode()).hexdigest(),compare_to=['ac21_single','ac21_single_expanded'],purpose='Separate domain extent from added rear building geometry.',horizon_s=180,incremental_allowance_usd=.25,reserved_vm_hours=2,solver_limit_s=6600)
# The larger ring has 1.5 times circumference but previously unchanged igniter count.
c=dict(case='candidate_large_crown_density',kind='double',direction=270)
s,r=make(c,horizon=90)
old="XYZ=8,18,5.1, RADIUS=2.25, SHAPE='RING', N_PARTICLES=1600"
assert old in s;s=s.replace(old,old.replace('1600','2400'))
# Per-crown instrumentation prevents a successful small crown masking the large one.
from scene import CLASSES
for tag,box in [('small','0,24,0,14.99,0,24'),('large','0,24,15,24,0,24')]:
 extra=''
 for fuel,_ in CLASSES:
  extra+=f"&DEVC ID='{tag} mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /\n"
  extra+=f"&DEVC ID='{tag} fuel {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /\n"
 s=s.replace('&TAIL /',extra+'&TAIL /')
(folder/(c['case']+'.fds')).write_text(s)
second=dict(case=c['case'],deck_sha256=hashlib.sha256(s.encode()).hexdigest(),compare_to=['ac21_double'],purpose='Test unchanged hot-particle linear density on the larger ring; add per-crown mass/fuel diagnostics.',horizon_s=90,incremental_allowance_usd=.125,reserved_vm_hours=.75,solver_limit_s=2100,limitations='Large-ring prescribed thermal and chemical input increase50%; not a neutral instrumentation change. Does not prove natural ignition or realistic intensity. Local preflight not yet performed.')
report=dict(status='UNLAUNCHED_CANDIDATES_PENDING_FINE_GRID',cases=[record,second],combined_planning_allowance_usd=.375,pricing_basis='Existing $0.08/VM-hour planning ceiling plus ancillary allowances; reverify before paid launch.',decision='Inspect fine-grid outcome before recommending both. Domain-only case is a three-way contrast reusing existing compact and expanded runs. Large-ring source remains a hypothesis; local validation precedes any paid sampling.',preserved='Analytic10m/16m canopy tops with3m/5m bases, generic vegetation and wood facade,3m/s wind,.5m grid,no trunks/ground cover/embers. Igniters removed21s. Not real-property validation.')
(ROOT/'results/corrective-candidates.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

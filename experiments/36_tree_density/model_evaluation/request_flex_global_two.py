"""User-requested global increase matching the newly approved regional Flex quota."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import G,PROJECT,gc,save,R
p='results/flex-global-two-request.json';assert not (R/p).exists()
ident='372adac7-559a-4615-b3df-079a62ad6c89';before=gc('beta','quotas','preferences','describe',ident,'--billing-project='+PROJECT);assert not before.get('reconciling')
regional=gc('beta','quotas','preferences','describe','density36-flex-l4-4','--billing-project='+PROJECT);assert int(regional['quotaConfig']['grantedValue'])==3
email=subprocess.check_output([G,'config','get-value','account'],text=True).strip()
save(p,dict(state='submission_pending',before=before,regional_approval=regional))
reason='Requesting 2 total GPUs globally (one additional), reduced from the denied3, specifically to match the preemptible L4 regional quota Google has JUST APPROVED to3 in us-central1 (preference density36-flex-l4-4, trace3bd1b7c7-1290-4c74-a64d-8a62a26f89ab). Google also approved16preemptible CPUs. Work uses Google Batch FLEX_START, accepts24hour allocation delays, and consists of fixed scientific model folds with checkpoints, cloud deadlines and zero automatic paid retries. The global limit1 currently prevents using the newly approved regional3. Cumulative experiment capUSD125 and budget-gated launches remain enforced. Please grant the minimum one additional GPU globally so two temporary Flex-start workers can use part of the approved regional quota. User explicitly requests pursuit of usable Flex-start capacity; no increase to the spending cap.'
r=subprocess.run([G,'beta','quotas','preferences','update',ident,'--preferred-value=2','--quota-id=GPUS-ALL-REGIONS-per-project','--service=compute.googleapis.com','--project='+PROJECT,'--billing-project='+PROJECT,'--email='+email,'--justification='+reason,'--format=json'],text=True,capture_output=True)
save(p,dict(before=before,regional_approval=regional,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));print(r.stdout or r.stderr);assert r.returncode==0

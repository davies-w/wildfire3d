"""Submit the user's explicit scientific-purpose and runtime clarification once."""
from pathlib import Path
import sys,subprocess,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,PROJECT,gc,save
out='results/flex-purpose-request.json';assert not (R/out).exists(),'Inspect saved request instead of duplicating'
ident='372adac7-559a-4615-b3df-079a62ad6c89'
before=gc('beta','quotas','preferences','describe',ident,'--billing-project='+PROJECT)
reason=('We are developing small, computationally efficient models to predict vegetation-fire behaviour, with the longer-term aim of helping prevent wildfires and improve wildfire risk reduction. This is simulation-based scientific research, not yet validated for operational wildfire decisions. We train and compare plain and soft-gated recurrent neural networks (approximately 5800 parameters) on 2080 preserved simulation histories, using fixed grouped training/validation/test folds. We request 2 GPUs total globally (one additional) for Google Batch FLEX_START. Google has already approved 3 preemptible NVIDIA L4 GPUs and 16 preemptible CPUs in us-central1, but the global limit of 1 prevents using that regional allowance. The first matched plain/gated pair took approximately 4 hours on one L4; remaining pairs have the same recipe, with actual runtime depending on validation stopping. Each Batch job has an 18.25-hour maximum task runtime and an 18.5-hour VM-age watchdog, and may wait up to 24 hours for allocation. We use immutable per-epoch checkpoints, verified optimizer/RNG resume checks, cloud supervision, cleanup, and no automatic paid retries. The cumulative experiment budget is USD125; launches are gated by the remaining budget. Please reconsider the minimum global increase to 2 for this delay-tolerant wildfire-prevention research workload.')
email=subprocess.check_output([G,'config','get-value','account'],text=True).strip()
save(out,dict(state='submission_pending',before=before,justification=reason,requested_global_gpus=2))
r=subprocess.run([G,'beta','quotas','preferences','update',ident,'--preferred-value=2','--quota-id=GPUS-ALL-REGIONS-per-project','--service=compute.googleapis.com','--project='+PROJECT,'--billing-project='+PROJECT,'--email='+email,'--justification='+reason,'--format=json'],text=True,capture_output=True,timeout=180)
save(out,dict(before=before,justification=reason,requested_global_gpus=2,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
receipt=json.loads(r.stdout);print(json.dumps(receipt))
q=gc('beta','quotas','preferences','describe',ident,'--billing-project='+PROJECT);save('results/flex-purpose-readback.json',q);print('READBACK',json.dumps(q))

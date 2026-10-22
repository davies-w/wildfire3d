"""Complete held-out evidence and evaluate already-frozen models without refitting."""
import subprocess
from finish_batch import ROOT,DVC,main
main('confirmation20')
subprocess.run([str(DVC),'repro','evaluate'],cwd=ROOT,check=True)
print('Final held-out evaluation complete; see results/evaluation.json',flush=True)

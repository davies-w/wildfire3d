"""Separate state, cone, presence and joint validation curves; no test outcomes."""
from pathlib import Path
import json,argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();rows={}
for folder in ['progressor','progressia','progresssc']:
 for f in sorted((R/'data'/folder).glob('fold00-epoch*.json')):
  d=json.loads(f.read_text());e=d['epoch'];assert e not in rows or rows[e]==d;rows[e]=d
es=sorted(rows);assert not es or es==list(range(1,max(es)+1))
fig,axes=plt.subplots(2,2,figsize=(12,7),dpi=130)
for ax,(key,title,factor) in zip(axes.flat,[('objective','Four-state integral error (%)',100),('cone_parameters_loss','Cone parameter loss',1),('cone_presence_bce','Cone presence BCE',1),('joint_selection_objective','Joint selection score',1)]):
 for split,color in [('train','#2563eb'),('validation','#ea580c')]:ax.plot(es,[factor*rows[e][split]['rollout'][key] for e in es],label=split,color=color)
 if not es:ax.text(.5,.5,'Awaiting first completed epoch',ha='center',transform=ax.transAxes)
 ax.set(title=title,xlabel='Completed epoch');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Experiment46 · fresh no-dropout GRU64 · eight ten-value recurrent states');fig.tight_layout();fig.savefig(args.output)
print(json.dumps(dict(epoch=max(es) if es else None,path=args.output)))

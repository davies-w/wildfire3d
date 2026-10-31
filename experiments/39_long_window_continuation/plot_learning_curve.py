"""Plot saved full-rollout train/validation scores; no fitting or test outcomes."""
from pathlib import Path
import os,json,argparse
os.environ.setdefault('MPLCONFIGDIR','/tmp/longwindow39-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
rows={}
for folder in ['training/data/resume/archive','progressor','progressia','progresssc']:
 for f in sorted((R/'data'/folder).glob('fold00-epoch*.json')):
  d=json.loads(f.read_text());e=d['epoch']
  if e in rows:assert rows[e]==d,'Conflicting saved epoch'
  rows[e]=d
assert rows
es=sorted(rows);assert es==list(range(1,max(es)+1))
train=[100*rows[e]['train']['rollout']['objective'] for e in es];val=[100*rows[e]['validation']['rollout']['objective'] for e in es]
fig,ax=plt.subplots(figsize=(9,4.8),dpi=160)
ax.plot(es,train,label='Training — full rollout',color='#2563eb',lw=2,marker='.',ms=4)
ax.plot(es,val,label='Validation — full rollout',color='#ea580c',lw=2,marker='.',ms=4)
for e,label in [(21,'8-step training windows'),(41,'16-step training windows'),(61,'32-step training windows'),(110,'64-step training windows'),(130,'90-step full sequences')]:
 if e<=max(es):ax.axvline(e,color='#94a3b8',ls='--',lw=1);ax.text(e+.2,ax.get_ylim()[1]*.92,label,rotation=90,fontsize=8,va='top',color='#475569')
ax.set(title=f'Experiment 39 · rotation 0 · {max(es)} completed epochs',xlabel='Completed epoch',ylabel='Mean full-sequence integral error (%)')
ax.grid(alpha=.18);ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
fig.text(.08,.025,'Mean of four range-normalized integral errors, equal configuration weighting. Lower is better.\nSaved epoch values; straight connecting lines, no smoothing. Gate BCE is not included in these curves.',fontsize=8,color='#475569')
fig.tight_layout(rect=[0,.09,1,1]);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out)
print(json.dumps(dict(path=str(out),epoch=max(es),train_percent=train[-1],validation_percent=val[-1])))

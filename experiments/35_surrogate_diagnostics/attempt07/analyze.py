from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;out=R/'data/visuals';out.mkdir(exist_ok=True);plan=json.loads((R/'coverage-plan.json').read_text());summary=[]
fig,axs=plt.subplots(2,5,figsize=(20,8));fig2,axs2=plt.subplots(2,5,figsize=(20,8))
for frame,ax,ax2 in zip(plan['selected_frames'],axs.flat,axs2.flat):
 recs=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(f'time-{frame:03}-epoch-*.json'))];assert len({r['epoch'] for r in recs})==len(recs)
 for split,style in [('train','--'),('validation','-')]:
  for key,color in [('precision','tab:blue'),('recall','tab:orange'),('f1','tab:green')]:ax.plot([r['epoch'] for r in recs],[r['summary'][split][key] for r in recs],style,color=color,label=split+' '+key)
  ax2.plot([r['epoch'] for r in recs],[r['summary'][split]['balanced_BCE'] for r in recs],style,label=split)
 ax.set(title=f'{frame*2}s',xlabel='Epoch',ylim=(-.02,1.02));ax.grid(alpha=.2);ax2.set(title=f'{frame*2}s',xlabel='Epoch');ax2.grid(alpha=.2)
 report=R/'data/collected'/f'time-{frame:03}-report.json';reason=json.loads(report.read_text())['reason'] if report.exists() else 'incomplete'
 if recs:
  final=recs[-1];summary.append(dict(nominal_time_s=frame*2,epochs=final['epoch'],reason=reason,final=final['summary'],always_NOT={s:dict(precision=None,recall=0 if final['summary'][s]['hot_fraction'] else None,f1=0 if final['summary'][s]['hot_fraction'] else None,false_positive_rate=0) for s in ['train','validation']}))
axs.flat[0].legend(fontsize=7);axs2.flat[0].legend();fig.suptitle('Ten independent HOT classifiers: validation solid / training dashed; undefined scores omitted');fig.tight_layout();fig.savefig(out/'positive-class-learning-curves.png',dpi=140);fig2.suptitle('Independent per-time balanced BCE, evaluated after every epoch');fig2.tight_layout();fig2.savefig(out/'loss-learning-curves.png',dpi=140)
(R/'results/analysis.json').write_text(json.dumps(dict(models=summary,scope=plan['scope'],warning='HOT T>50C is not flame/combustion. Macro and aggregate metrics retained; validationpreviousdevelopment, notpristinetest. A deadline/epochcap is not convergence.'),indent=2))

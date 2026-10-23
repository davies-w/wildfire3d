"""Focused descriptive analysis of the frozen 20-second classifier; no fitting."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;out=R/'data/time20';out.mkdir(exist_ok=True);report=json.loads((R/'data/collected/time-010-report.json').read_text());h=report['history'];epochs=[r['epoch'] for r in h];cases=json.loads((R/'cases.json').read_text());z=np.load(R/'data/collected/time-010-epoch-300-counts.npz');lookup={str(n):v for n,v in zip(z['case'],z['counts'])};config=[]
for split in ['train','validation']:
 for cid in sorted({c['configuration'] for c in cases if c['split']==split}):
  cs=[c for c in cases if c['configuration']==cid];v=np.mean([lookup[c['case']] for c in cs],axis=0);tp,fp,fn,tn=v[:4];config.append(dict(configuration=cid,split=split,f1=float(2*tp/(2*tp+fp+fn)),precision=float(tp/(tp+fp)) if tp+fp else None,recall=float(tp/(tp+fn)) if tp+fn else None))
summary=dict(time_s=20,epochs=300,updates=13500,learning_rate=.0003,reason=report['reason'],final=h[-1]['summary'],checkpoints={str(e):h[e]['summary'] for e in [0,25,50,100,200,250,300]},configuration_f1={s:dict(zip(['min','p25','median','p75','max'],map(float,np.percentile([c['f1'] for c in config if c['split']==s],[0,25,50,75,100])))) for s in ['train','validation']},descriptive_validation_min_loss=dict(epoch=min(h,key=lambda r:r['summary']['validation']['balanced_BCE'])['epoch']),descriptive_validation_max_f1=dict(epoch=max(h,key=lambda r:r['summary']['validation']['f1'])['epoch']),late_window_means={s:{k:[float(np.mean([r['summary'][s][k] for r in h[a:b]])) for a,b in [(201,251),(251,301)]] for k in ['balanced_BCE','precision','recall','f1']} for s in ['train','validation']})
fig,axes=plt.subplots(2,2,figsize=(12,8));colors={'train':'#227c9d','validation':'#cf5535'}
for s in ['train','validation']:
 y=lambda k:[r['summary'][s][k] for r in h]
 axes[0,0].plot(epochs,y('f1'),color=colors[s],label=s)
 axes[0,1].plot(epochs,y('balanced_BCE'),color=colors[s],label=s)
 axes[1,0].plot(epochs,y('precision'),color=colors[s],label=s+' precision');axes[1,0].plot(epochs,y('recall'),color=colors[s],ls='--',label=s+' recall')
axes[0,0].set(title='HOT F1: training vs validation',ylabel='F1',ylim=(0,1));axes[0,1].set(title='Exact class-balanced training objective',ylabel='Balanced BCE (log scale)',yscale='log');axes[1,0].set(title='HOT precision and recall',ylabel='Score',ylim=(0,1))
for a in [axes[0,0],axes[0,1],axes[1,0]]:a.set_xlabel('Epoch');a.grid(alpha=.2);a.legend(fontsize=8)
for j,s in enumerate(['train','validation']):
 vals=sorted(c['f1'] for c in config if c['split']==s);x=np.linspace(j-.2,j+.2,len(vals));axes[1,1].scatter(x,vals,s=12 if s=='train' else 25,color=colors[s],alpha=.6);axes[1,1].plot([j-.25,j+.25],[np.median(vals)]*2,color='black',lw=2)
axes[1,1].set(title='Final F1 across configurations (black = median)',xticks=[0,1],xticklabels=['360 training','32 validation'],ylabel='Per-configuration F1',ylim=(0,1));axes[1,1].grid(axis='y',alpha=.2)
fig.suptitle('20-second independent 3D U-Net · HOT gas >50°C · fixed threshold0.5\n300 epochs /13,500updates; full evaluation every epoch; plateau criterion NOT met',fontsize=13)
fig.tight_layout();fig.savefig(out/'learning-curves.png',dpi=160)
(R/'results/time20-summary.json').write_text(json.dumps(summary,indent=2));(out/'configuration-metrics.json').write_text(json.dumps(config,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['final','checkpoints']},indent=2))

"""Read-only cloud progress snapshot; never touches active collector outputs or training."""
from pathlib import Path
import subprocess,json,re,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;out=R/'data/progress';out.mkdir(exist_ok=True);G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';base='gs://tmrw-wildfire-20261015-trial/diagnostics35/attempt07/'
if '--offline' not in sys.argv:
 names=subprocess.run([G,'storage','ls',base+'*.json'],capture_output=True,text=True,check=True).stdout.splitlines();reports=[n for n in names if n.endswith('-report.json')];finished={int(re.search(r'time-(\d+)-report',n)[1]) for n in reports}
 urls=reports+[n for n in names if re.search(r'time-\d+-epoch-\d+.json$',n) and int(re.search(r'time-(\d+)',n)[1]) not in finished]
 subprocess.run([G,'storage','cp',*urls,str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
frames=list(range(0,91,10));records={};summ=[]
for f in frames:
 p=out/f'time-{f:03}-report.json'
 if p.exists():x=json.loads(p.read_text());rr=x['history'];status='Plateau' if 'empirical_plateau' in x['reason'] else '300-epoch cap; no plateau'
 else:rr=[json.loads(p.read_text()) for p in sorted(out.glob(f'time-{f:03}-epoch-*.json'))];status='Running' if rr else 'Not started'
 records[f]=rr;summ.append(dict(time_s=2*f,status=status,epoch=rr[-1]['epoch'] if rr else None,metrics=rr[-1]['summary'] if rr else None))
for name,keys in [('f1',['f1']),('positive-metrics',['precision','recall','f1']),('loss',['balanced_BCE'])]:
 fig,axs=plt.subplots(2,5,figsize=(18,7.5));colors={'precision':'#2878b5','recall':'#e28728','f1':'#29915b','balanced_BCE':'#2878b5'}
 for f,ax,s in zip(frames,axs.flat,summ):
  rr=records[f]
  for split,style in [('train','--'),('validation','-')]:
   for key in keys:
    color=colors[key] if name!='loss' else ('#777777' if split=='train' else '#2878b5')
    ax.plot([r['epoch'] for r in rr],[r['summary'][split][key] for r in rr],style,color=color,linewidth=1.25,label=split+' '+key)
  ax.set_xlim(0,max(1,rr[-1]['epoch']) if rr else 300)
  ax.set_title(f'{f*2} seconds\n{s["status"]}',fontsize=10);ax.set_xlabel('Epoch');ax.grid(alpha=.2)
  if name=='loss':ax.set_yscale('log');ax.set_ylabel('Balanced BCE (log scale)')
  else:ax.set_ylim(-.03,1.03);ax.set_ylabel('Score')
  if not rr:ax.text(.5,.5,'Pending',ha='center',transform=ax.transAxes)
  elif name!='loss' and rr[-1]['summary']['train']['hot_fraction']==0 and rr[-1]['summary']['validation']['hot_fraction']==0:
   ax.text(.5,.45,'No HOT cells\nHOT recall/F1 undefined\nFinal false-positive rate: '+f'{rr[-1]["summary"]["validation"]["false_positive_rate"]:.1%}',ha='center',fontsize=9,transform=ax.transAxes)
 handles,labels=axs.flat[1].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=min(6,len(labels)),fontsize=9);fig.suptitle('Independent HOT models — validation solid, training dashed\nLive snapshot; all evaluations use full train/validation configurations',fontsize=13);fig.tight_layout(rect=[0,.06,1,.91]);fig.savefig(out/(name+'-curves.png'),dpi=140);plt.close(fig)
(out/'summary.json').write_text(json.dumps(summ,indent=2));print(json.dumps([{k:v for k,v in s.items() if k!='metrics'} for s in summ]))

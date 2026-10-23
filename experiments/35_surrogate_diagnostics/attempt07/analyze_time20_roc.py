"""Exact tied-score ROC/AP for frozen20s CPU logits. No training/threshold selection."""
from pathlib import Path
import json,hashlib
import numpy as np,torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from model import HotUNet
R=Path(__file__).parent;V=R.parent/'attempt08';out=R/'data/time20_roc';out.mkdir(exist_ok=True);cs=json.loads((R/'cases.json').read_text());g=np.load(R/'data/geometries.npz');scale=max(float(g[c['case']].max()) for c in cs if c['split']=='train');checkpoint=V/'data/models/time-010-epoch-300.pt';digest=hashlib.sha256(checkpoint.read_bytes()).hexdigest();assert digest==json.loads((V/'results/model-freeze.json').read_text())['files']['data/models/time-010-epoch-300.pt'];torch.set_num_threads(4);torch.set_grad_enabled(False)
coords=np.stack(np.meshgrid(*[(np.arange(n)+.5)/n*2-1 for n in [48,32,32]],indexing='ij')).astype(np.float32)
def x(c):
 a=np.radians(c['angle_deg']);cond=np.array([c['wind_speed']/5,c['moisture']/.3,c['loading_multiplier']/1.3,c['crown_height_m']/10,np.cos(a),np.sin(a)],np.float32);return np.concatenate([g[c['case']]/scale,coords,np.broadcast_to(cond[:,None,None,None],(6,48,32,32))])
m=HotUNet();m.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=False)['model']);m.eval();scores=[];ys=[]
for i in range(0,len(cs),4):
 batch=cs[i:i+4];scores.extend(m(torch.from_numpy(np.stack([x(c) for c in batch]))).numpy().copy());ys.extend(np.unpackbits(np.load(R/'data/labels'/(c['case']+'.npz'))['packed'][10],count=49152).astype(bool) for c in batch)
scores=np.array(scores).reshape(len(cs),-1);ys=np.array(ys);assert np.isfinite(scores).all();np.save(out/'logits.npy',scores);result={};curves={};fig,ax=plt.subplots(1,2,figsize=(11,4.7));colors={'train':'#227c9d','validation':'#cf5535'}
for split in ['train','validation']:
 ids=[i for i,c in enumerate(cs) if c['split']==split];s=scores[ids].reshape(-1);y=ys[ids].reshape(-1);nrep={c['configuration']:sum(z['configuration']==c['configuration'] for z in cs) for c in cs};w=np.repeat([1/nrep[cs[i]['configuration']] for i in ids],49152);pos=float(w[y].sum());neg=float(w[~y].sum());order=np.argsort(-s,kind='stable');ss=s[order];yy=y[order];ww=w[order];ends=np.r_[np.flatnonzero(ss[:-1]!=ss[1:]),len(ss)-1];tp=np.r_[0,np.cumsum(ww*yy)[ends]];fp=np.r_[0,np.cumsum(ww*(~yy))[ends]];rec=tp/pos;fpr=fp/neg;prec=np.divide(tp,tp+fp,out=np.ones_like(tp),where=tp+fp>0);auc=float(np.trapezoid(rec,fpr));ap=float(np.sum(np.diff(rec)*prec[1:]));mask=s>=0;at_tp=float(w[mask&y].sum());at_fp=float(w[mask&~y].sum());point=dict(fpr=at_fp/neg,recall=at_tp/pos,precision=at_tp/(at_tp+at_fp));base=pos/(pos+neg)
 result[split]=dict(ROC_AUC=auc,average_precision=ap,hot_prevalence=base,threshold_05=point,configurations=len({cs[i]['configuration'] for i in ids}),trajectories=len(ids),unique_scores=len(ends))
 # Preserve exact metrics; downsample plotted vertices only, with fixed evenly spaced indices.
 ix=np.unique(np.linspace(0,len(rec)-1,min(20000,len(rec))).astype(int));curves[split+'_fpr']=fpr[ix];curves[split+'_recall']=rec[ix];curves[split+'_precision']=prec[ix];ax[0].plot(fpr[ix],rec[ix],color=colors[split],label=f'{split}: AUC={auc:.4f}');ax[1].plot(rec[ix],prec[ix],color=colors[split],label=f'{split}: AP={ap:.4f}');ax[0].scatter(point['fpr'],point['recall'],color=colors[split],s=45,zorder=3);ax[1].scatter(point['recall'],point['precision'],color=colors[split],s=45,zorder=3);ax[1].axhline(base,color=colors[split],ls=':',alpha=.65)
 del s,y,w,order,ss,yy,ww,ends,tp,fp,rec,fpr,prec
ax[0].plot([0,1],[0,1],'--',color='gray',label='Random ranking');ax[0].set(title='ROC',xlabel='False-positive rate',ylabel='True-positive rate (recall)');ax[1].set(title='Precision–recall',xlabel='Recall',ylabel='Precision')
for a in ax:a.set(xlim=(0,1),ylim=(0,1.02));a.grid(alpha=.2);a.legend(loc='lower left',fontsize=9)
fig.suptitle('20-second frozen model · dots: existing0.5 threshold · no threshold tuning\nHOT gas>50°C; validation32configurations/40runs; replicas weighted within configuration',fontsize=11);fig.tight_layout();fig.savefig(out/'roc-pr.png',dpi=160);np.savez_compressed(out/'plot-curves.npz',**curves)
result['method']='Exact ROC trapezoid AUC and non-interpolated average precision, grouping all equal float32 logits; every cell included. Configurations equal total weight, replicas averaged. Display only downsampled to<=20000vertices; metrics use full curves. CPU inference can differ slightly from originalGPU. Class-balanced training scores are not calibrated probabilities.';result['checkpoint_sha256']=digest;(R/'results/time20-roc.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

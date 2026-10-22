"""Actual hidden states/messages of a frozen model, not physical fire timesteps."""
import hashlib,json
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
from PIL import Image
from models import ROOT,batch,model,CENTERS
CASE='confirm20_ACG_3200_s4321';OUT=ROOT/'data/visualization';OUT.mkdir(exist_ok=True);DEST=ROOT/'results/visualizations';DEST.mkdir(exist_ok=True)
record=next(r for r in json.loads((ROOT/'confirmation-inputs.json').read_text()) if r['case']==CASE)
weights=json.loads((ROOT/'results/frozen-weights.json').read_text());checkpoint=next(r for r in weights['models'] if r['kind']=='graph' and r['seed']==11)
p=ROOT/checkpoint['checkpoint'];assert hashlib.sha256(p.read_bytes()).hexdigest()==checkpoint['checkpoint_sha256']
m=model('graph');m.load_state_dict(torch.load(p,weights_only=True));m.eval();torch.set_num_threads(1)
x,edge,adj,simple=batch([record]);states=[];messages=[]
with torch.inference_mode():
 h=m.encode(x);states.append(h[0].numpy().copy());active=(x.abs().sum(-1)>0).float()
 for message,update in zip(m.messages,m.updates):
  receivers=h[:,:,None,:].expand(-1,-1,8,-1);senders=h[:,None,:,:].expand(-1,8,-1,-1)
  msg=message(torch.cat([receivers,senders,edge],-1))*adj[:,:,:,None]/4
  messages.append(msg[0].numpy().copy());h=update(torch.cat([h,msg.sum(2)],-1))*active[:,:,None];states.append(h[0].numpy().copy())
 prob=float(torch.sigmoid(m(*batch([record]))[0][0,0]))
frozen=json.loads((ROOT/'results/frozen-predictions.json').read_text());ensemble=np.mean([p['ignition_probability'] for r in frozen['models'] if r['kind']=='graph' for p in r['predictions'] if p['case']==CASE])
anchors=json.loads((ROOT/'design.json').read_text())['anchors_m'];pos=np.vstack([CENTERS[:,:2],np.array([anchors[a] for a in record['layout']])]);labels=['West wall','East wall','South wall','North wall','Roof']+['Crown '+a for a in record['layout']]
maxnorm=max(np.linalg.norm(s,axis=1).max() for s in states);maxmsg=max(np.linalg.norm(v,axis=2).max() for v in messages);paths=[]
for k,state in enumerate(states):
 fig=plt.figure(figsize=(13,7.5),facecolor='#f5f7fb');ax=fig.add_axes([.06,.20,.54,.60]);hm=fig.add_axes([.68,.26,.26,.44]);norm=np.linalg.norm(state,axis=1)
 ax.add_patch(Rectangle((14,10),6,4,facecolor='#e5eaf2',edgecolor='#b1bccb',lw=1.5));ax.text(17,11,'HOUSE',ha='center',color='#718096',fontsize=11)
 if k:
  strengths=np.linalg.norm(messages[k-1],axis=2);order=sorted([(strengths[i,j],i,j) for i in range(8) for j in range(8) if i!=j],reverse=True)[:12]
  for strength,i,j in reversed(order):
   ax.add_patch(FancyArrowPatch(pos[j],pos[i],arrowstyle='-|>',mutation_scale=10,connectionstyle='arc3,rad=.12',shrinkA=16,shrinkB=16,lw=.5+3*strength/maxmsg,color='#516c94',alpha=.25+.55*strength/maxmsg,zorder=2))
 dots=ax.scatter(pos[:,0],pos[:,1],s=350,c=norm,cmap='viridis',vmin=0,vmax=maxnorm,edgecolors='white',linewidths=2,zorder=3)
 for i,((px,py),label) in enumerate(zip(pos,labels)):ax.annotate(label,(px,py),xytext=(0,17 if i!=2 and i!=7 else -25),textcoords='offset points',ha='center',fontsize=10,color='#17293d',weight='bold')
 ax.annotate('wind direction',(12,8.8),(9.5,8.8),arrowprops=dict(arrowstyle='->',color='#718096'),fontsize=9,color='#718096')
 ax.set(xlim=(8.8,22),ylim=(8,16),xlabel='x (m)',ylabel='y (m)');ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False)
 cb=fig.colorbar(dots,ax=ax,orientation='horizontal',fraction=.045,pad=.16);cb.set_label('Node colour: hidden-state magnitude (learned units)',fontsize=9)
 heat=hm.imshow(state,cmap='coolwarm',vmin=-1,vmax=1,aspect='auto');hm.set_xticks(range(8),[str(i+1) for i in range(8)]);hm.set_yticks(range(8),labels,fontsize=9);hm.set_xlabel('Eight hidden features (no physical units)',fontsize=9);hm.set_title('Actual internal feature values',fontsize=11,pad=12)
 fig.colorbar(heat,ax=hm,fraction=.05,pad=.04)
 title=['0  Encode the initial scene','1  First message-passing round','2  Second message-passing round'][k]
 fig.text(.055,.93,'Inside the graph model',fontsize=24,weight='bold',color='#17293d');fig.text(.055,.87,title,fontsize=16,color='#285980')
 fig.text(.67,.86,f'Final prediction: {prob:.1%} ignition',fontsize=15,weight='bold',color='#17293d');fig.text(.67,.82,f'Five-model average: {ensemble:.1%}',fontsize=11,color='#516c94')
 fig.text(.055,.075,'Computational stages — NOT seconds or a simulated spread of fire.',fontsize=12,weight='bold',color='#963e2c')
 fig.text(.055,.037,'Frozen graph, training seed 11 (first predefined seed). Arrows: 12 strongest of 56 messages; width = magnitude.\nHidden-state magnitude is neither heat nor causal importance. Same A+C+G scene as the Smokeview animation.',fontsize=9,color='#516c94')
 path=OUT/f'graph_stage_{k}.png';fig.savefig(path,dpi=120);plt.close(fig);paths.append(path)
images=[Image.open(p).convert('RGB') for p in paths];images[0].save(DEST/'graph_messages.gif',save_all=True,append_images=images[1:],duration=[2200,2200,3500],loop=0);images[-1].save(DEST/'graph_messages.png')
(OUT/'graph_trace.json').write_text(json.dumps(dict(case=CASE,checkpoint=checkpoint['checkpoint'],checkpoint_sha256=checkpoint['checkpoint_sha256'],single_prediction=prob,ensemble_prediction=float(ensemble),states=[v.tolist() for v in states],messages=[v.tolist() for v in messages]),indent=2)+'\n')
print('Saved graph visualization',prob,ensemble)

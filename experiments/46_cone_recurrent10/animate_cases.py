"""Two reproducibly random test histories: actual gas cells and predicted/reference cones."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from matplotlib.colors import TwoSlopeNorm
from PIL import Image
R=Path(__file__).resolve().parent;D=R/'data/animations';D.mkdir(exist_ok=True)
sys.path.insert(0,str(R.parent/'44_hot_gas_cones'));from extract_training import source_frames,xyz
assert json.loads((R/'results03/collected.json').read_text())['passed']
schema=json.loads((R/'data/training03/schema.json').read_text());pred=np.load(R/'data/pool03-results/fold00-test-predictions.npz');labels=np.load(R/'data/training03/data/cones.npz')
sources={x['case_index']:x for x in json.loads((R.parent/'45_cone_multitask/data/labels/schema.json').read_text())['source_records']};conditions={x['case']:x for x in json.loads((R.parent/'36_tree_density/cases.json').read_text())}
chosen=np.random.default_rng(20261102).choice(schema['rotations'][0]['test'],2,replace=False).tolist();assert chosen==[1498,1598]
# Fixed mean over ALL >50C cell observations in both histories, before display subsampling.
all_hot=[]
for idx in chosen:
 c=schema['cases'][idx];src=sources[idx];cond=conditions[c['case']]
 item=dict(case=c['case'],path=src['source_path'],sha256=src['source_sha256'],source_kind='verified_temperature_slice',origin_m=[-4,-4,0] if cond.get('expanded') else [0,0,0])
 for _,temp in source_frames(item):all_hot.append(temp[temp>50])
all_hot=np.concatenate(all_hot);color_mean=float(all_hot.mean());color_low,color_high=map(float,np.quantile(all_hot,[.05,.95]))
color_policy=dict(mean_C=color_mean,lower_C=color_low,upper_C=color_high,scope='All above50C cell observations across both full histories, before display subsampling',rule='Pooled5th/95th percentiles of above50C samples; mean at colour midpoint via two-slope normalization; fixed across both cases and every frame; colour clipping only',below_fraction=float((all_hot<color_low).mean()),above_fraction=float((all_hot>color_high).mean()),fixed_palette=True,legend_pixel_identical_all_frames=True)
manifest={'seed':20261102,'selection':'Uniform random draw without replacement from all208 frozen test histories; no performance filtering','selected_epoch':134,'indices':chosen,'cases':[]}
for idx in chosen:
 c=schema['cases'][idx];name=c['case'];cond=conditions[name];src=sources[idx]
 item=dict(case=name,path=src['source_path'],sha256=src['source_sha256'],source_kind='verified_temperature_slice',origin_m=[-4,-4,0] if cond.get('expanded') else [0,0,0])
 pi=int(np.flatnonzero(pred['case_indices']==idx)[0]);frames=[]
 for j,(t,temp) in enumerate(source_frames(item)):
  assert abs(t-float(labels['time'][idx,j]))<1e-5
  hot=np.flatnonzero(temp>50);keep=hot
  if len(hot)>600:keep=np.unique(np.r_[hot[np.linspace(0,len(hot)-1,599).astype(int)],hot[np.argmax(temp[hot])]])
  cp=None if j==0 else pred['cone_parameters'][pi,j-1].astype(float).tolist();prob=None if j==0 else float(pred['cone_presence_probability'][pi,j-1])
  frames.append(dict(t=round(t,5),points=np.round(np.c_[xyz[keep],temp[keep]],3).tolist(),hot_count=len(hot),ref=labels['parameters'][idx,j].astype(float).tolist() if labels['active'][idx,j] else None,pred=cp if prob is not None and prob>=.5 else None,probability=prob))
 data=dict(case=name,index=idx,crown_height=cond['crown_height_m'],wind=cond['wind_speed'],frames=frames)
 (D/(name+'.json')).write_text(json.dumps(data,separators=(',',':'))+'\n')
 manifest['cases'].append(dict(case=name,index=idx,source_sha256=src['source_sha256'],source_path=src['source_path'],frames=len(frames),crown_height_m=cond['crown_height_m'],wind_m_s=cond['wind_speed']))
 # Fixed 3-D views, matched metre axes and actual cell-centre temperatures.
 fig=plt.figure(figsize=(11,5.6),dpi=90);axes=[fig.add_subplot(121,projection='3d'),fig.add_subplot(122,projection='3d')];cmap=plt.get_cmap('inferno');norm=TwoSlopeNorm(vmin=color_low,vcenter=color_mean,vmax=color_high)
 def cone(ax,p,color):
  if p is None:return
  h,tilt,length,radius,peak=p;a=np.deg2rad(tilt);u=np.array([np.sin(a),0,np.cos(a)]);v=np.array([np.cos(a),0,-np.sin(a)]);w=np.array([0,1,0]);apex=np.array([8,8,h]);th=np.linspace(0,2*np.pi,49);rim=apex+length*u+radius*(np.cos(th)[:,None]*v+np.sin(th)[:,None]*w)
  ax.plot(*rim.T,color=color,lw=1.1)
  for k in range(0,48,6):ax.plot(*np.stack([apex,rim[k]]).T,color=color,lw=.8,alpha=.8)
 def draw(j):
  f=frames[j]
  for ax,kind,title,color in zip(axes,['ref','pred'],['Extracted reference cone','Model-predicted cone'],['#00aabd','#dc43b7']):
   ax.clear();ax.set(xlim=(0,24),ylim=(0,16),zlim=(0,16),xlabel='Downwind x (m)',ylabel='y (m)',zlabel='Height (m)');ax.set_box_aspect((24,16,16));ax.view_init(elev=22,azim=-62)
   th=np.linspace(0,2*np.pi,33);base=np.c_[8+1.5*np.cos(th),8+1.5*np.sin(th),np.full_like(th,2)];top=np.array([8,8,2+cond['crown_height_m']]);ax.plot(*base.T,color='#238351',alpha=.65)
   for k in range(0,32,4):ax.plot(*np.stack([base[k],top]).T,color='#238351',alpha=.65)
   pts=np.array(f['points'])
   if len(pts):ax.scatter(pts[:,0],pts[:,1],pts[:,2],c=np.clip(pts[:,3],color_low,color_high),cmap=cmap,norm=norm,s=7,alpha=.58,depthshade=False)
   cone(ax,f[kind],color);ax.quiver(2,2,.5,4,0,0,color='#4775ba',arrow_length_ratio=.2)
   p=f[kind];ax.set_title(title+'\n'+('Absent / no prediction at t=0' if p is None else f'Length {p[2]:.2f}m · peak {p[4]:.0f}°C'),fontsize=10)
  fig.suptitle(f'{name} · {f["t"]:.1f}s · wind {cond["wind_speed"]:g}m/s → +x · igniter '+('ON' if f['t']<20 else 'OFF'),fontsize=12)
  return []
 fig.subplots_adjust(left=.02,right=.88,bottom=.17,top=.83,wspace=.02);cb=fig.add_axes([.91,.28,.015,.4]);fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cb,label='Gas temperature (°C) · clipped',ticks=[color_low,color_mean,color_high],format='%.1f')
 fig.text(.02,.035,'Same simulated hot cells in both views (>50°C, up to600 points/frame). Wire cones are envelopes, not flames.\nGreen wire crown: 3m wide, 8m tall above2m; no trunk. No predicted temperature field. GIF playback ≈16× real time.',fontsize=8)
 draw(10);fig.canvas.draw();fig.savefig(D/(name+'-preview.png'))
 # One fixed palette for every frame prevents GIF quantization from changing the legend.
 palette=Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy()).quantize(colors=256)
 images=[];legend=None
 for j in range(len(frames)):
  draw(j);fig.canvas.draw();rgb=np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy()
  im=Image.fromarray(rgb).quantize(palette=palette,dither=Image.Dither.NONE)
  # Colorbar plus its labels must stay pixel-identical through the full animation.
  box=(int(rgb.shape[1]*.90),int(rgb.shape[0]*.25),rgb.shape[1],int(rgb.shape[0]*.75))
  crop=im.convert('RGB').crop(box).tobytes()
  if legend is None:legend=crop
  else:assert crop==legend,'Colour legend moved or changed between frames'
  images.append(im)
 images[0].save(D/(name+'.gif'),save_all=True,append_images=images[1:],duration=125,loop=0,optimize=False,disposal=2)
 plt.close(fig)
 print('Rendered',name,flush=True)
manifest['color_scale']=color_policy
manifest['display']={'temperature':'Actual saved simulation gas temperature, not heat flux; identical field in both panels','threshold_C':50,'maximum_displayed_cells_per_frame':600,'sampling':'Evenly spaced hot-cell indices, plus hottest cell; display-only subsampling','saved_frames':91,'gif_fps':8,'cone_probability_display_threshold':.5,'geometry':'Crown diameter3m, base2m, crown height8m; no trunk; not a species model','source':'1500C imposed igniter for first20s included; no buildings or embers; 0.5m cells; observed24x16x16m crop','cone':'Ground-constrained fit may extend outside crop; broad95%-hot-cell envelope, not physical flame boundary'}
(D/'selection.json').write_text(json.dumps(manifest,indent=2)+'\n')

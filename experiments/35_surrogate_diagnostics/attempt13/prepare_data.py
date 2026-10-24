"""Frozen, configuration-grouped ten-fold inputs; no fitting or target-based splitting."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent/'attempt12'
assert json.loads((P/'results/validation.json').read_text())['passed']
items=json.loads((P/'inventory.json').read_text());names=[];scales=[];blocks=[]
def feature(name,scale,block):names.append(name);scales.append(scale);blocks.append(block)
scalar=[('gas_HRR_kW',100),('global_HRR_kW',100),('solid_oxidation_HRR_kW',100),('fuel_vapor_release_kg_s',.01),('hot_volume_m3',100),('peak_gas_temperature_C',100),('temperature_excess_integral_K_m3',10000),('mean_radiation_intensity',1),('max_radiation_intensity',100)]
for n,s in scalar:feature(n,s,'gas')
matkeys=[('remaining_total_mass_kg',1),('PARTICLE TEMPERATURE',100),('PARTICLE DIAMETER',1000),('INCIDENT HEAT FLUX',1),('PARTICLE CONVECTIVE HEAT FLUX',1)]
for k in range(4):
 for n,s in matkeys:feature(f'material{k}_{n}',s,'material')
presence=[];shape_indices=[]
for key in ['hot_plume','hrr_region']:
 presence.append(len(names));feature(key+'_present',1,'shape');ix=[]
 for axis in 'xyz':ix.append(len(names));feature(key+'_centroid_'+axis,10,'shape')
 for ij in ['xx','yy','zz','xy','xz','yz']:ix.append(len(names));feature(key+'_cov_'+ij,100,'shape')
 shape_indices.append(ix)
for axis in 'xyz':feature('hot_velocity_'+axis,5,'velocity')
S=[];M=[];T=[];G=[];cases=[];groups={};hashes={}
for it in items:
 c=it['conditions'];n=c['case'];p=P/'data/states'/(n+'.json');x=json.loads(p.read_text());hashes[n]=hashlib.sha256(p.read_bytes()).hexdigest();ys=[];ms=[]
 for r in x['snapshots']:
  y=[r[k] for k,s in scalar];m=[1]*len(y)
  for material in r['material_classes']:
   for k,s in matkeys:
    v=material[k] if k=='remaining_total_mass_kg' else material['mass_weighted'][k];y.append(v if v is not None else 0);m.append(int(v is not None))
  for key in ['hot_plume','hrr_region']:
   mo=r[key];y.append(float(mo is not None));m.append(1)
   vals=mo['centroid_m']+[mo['covariance_m2'][i][j] for i,j in [(0,0),(1,1),(2,2),(0,1),(0,2),(1,2)]] if mo else [0]*9
   y+=vals;m+=[int(mo is not None)]*9
  y+=r['hot_weighted_velocity_m_s'] or [0]*3;m+=[int(r['hot_weighted_velocity_m_s'] is not None)]*3
  ys.append(y);ms.append(m)
 assert len(ys)==91 and len(ys[0])==52
 S.append(ys);M.append(ms);T.append([r['time_s'] for r in x['snapshots']]);initial=x['snapshots'][0]['material_classes']
 G.append([c.get('crown_height_m',8)/10,c.get('loading_multiplier',1),c['moisture'],np.cos(np.deg2rad(c['angle_deg'])),np.sin(np.deg2rad(c['angle_deg'])),c['wind_speed']/5]+[v['remaining_total_mass_kg']/10 for v in initial])
 key=tuple(round(float(v),8) for v in [c.get('crown_height_m',8),c['moisture'],c.get('loading_multiplier',1),c['wind_speed'],c['angle_deg']]);groups.setdefault(key,[]).append(len(cases));cases.append(dict(case=n,source=it['source'],former_split=c['split'],physical_key=key))
assert len(groups)==480 and len(cases)==520
rng=np.random.default_rng(3513);keys=sorted(groups);rng.shuffle(keys);fold=np.zeros(520,dtype=np.int64)
for j,key in enumerate(keys):fold[groups[key]]=j%10
rotations=[]
for k in range(10):
 test=k;valid=(k+1)%10;tr=[i for i in range(520) if fold[i] not in (test,valid)];va=np.where(fold==valid)[0].tolist();te=np.where(fold==test)[0].tolist();assert set(tr).isdisjoint(va) and set(tr).isdisjoint(te) and set(va).isdisjoint(te)
 rotations.append(dict(rotation=k,train=tr,validation=va,test=te,train_configurations=384,validation_configurations=48,test_configurations=48,train_transitions=len(tr)*90))
config=np.zeros(520,dtype=np.int64)
for j,key in enumerate(sorted(groups)):config[groups[key]]=j
S=np.array(S,np.float32);M=np.array(M,np.float32);T=np.array(T,np.float32);G=np.array(G,np.float32)
assert np.isfinite(S).all() and np.all(np.diff(T,axis=1)>0)
np.savez_compressed(R/'data/sequences.npz',state=S,mask=M,time=T,geometry=G,fold=fold,configuration=config)
meta=dict(state_names=names,physical_encoding_scales=scales,blocks=blocks,presence_indices=presence,shape_indices=shape_indices,velocity_indices=[49,50,51],geometry_names=['height_div10','loading','initial_moisture','cos_ignition_angle','sin_ignition_angle','wind_x_div5','initial_mass0_div10','initial_mass1_div10','initial_mass2_div10','initial_mass3_div10'],forcing_names=['ambient_temperature_div100','igniter_on_fraction_of_step','dt_div2'],cases=cases,rotations=rotations,source_hashes=hashes)
(R/'schema.json').write_text(json.dumps(meta,indent=2));(R/'results/data-verification.json').write_text(json.dumps(dict(passed=True,histories=520,configurations=480,shape=list(S.shape),transitions=46800,fold_case_counts=np.bincount(fold).tolist(),selection='Random physical-configuration groups; no target stratification',test_policy='Former test history use explicitly authorized; not pristine historical tests'),indent=2));print('Prepared 520 histories, 480 groups, 46800 transitions, state shape',S.shape)

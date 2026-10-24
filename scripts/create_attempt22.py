"""Single authorized matched scalar versus spatial-heating comparison; no launch."""
from pathlib import Path
import json,yaml
repo=Path(__file__).resolve().parents[1];o=repo/'experiments/35_surrogate_diagnostics/attempt20';r=o.parent/'attempt22';r.mkdir(exist_ok=False);(r/'results').mkdir();(r/'data/resume').mkdir(parents=True)
for n in ['cloud.py','runtime.py','launch.py','collect.py','prepare_pilot.py','finish_run.py','finalize_archive.py','validate_transport.py','worker.py','model.py','validate.py','analyze.py']:
 s=(o/n).read_text().replace('attempt20','attempt22').replace('thermal35-20','spatial35-22').replace('gpu35-thermal20','gpu35-spatial22').replace('exp35-thermal20','exp35-spatial22')
 if n in ['worker.py','model.py','validate.py','analyze.py']:
  s=s.replace("'control'","'scalar'").replace("'thermal'","'spatial'")
 if n=='model.py':
  s=s.replace('nn.GRU(25,32','nn.GRU(37,32').replace('nn.Linear(32,4)','nn.Linear(32,7)').replace('[1,1,1,0]','[1,1,1,1,0,0,0]')
  s=s.replace('only thermal input/output','only spatial input/output')
 if n=='worker.py':
  s=s.replace('raw[:,:,3]=0','raw[:,:,4:]=0').replace('length,25)','length,37)').replace('torch.zeros(4,4,4','torch.zeros(4,4,7').replace('torch.randn(4,12,25','torch.randn(4,12,37').replace('reshape(len(ids),91-h,4)','reshape(len(ids),91-h,7)')
  s=s.replace('Matched thermal surface-heating proxy fourth-state; not stored energy J.','Matched scalar4 versus spatial7 surface-heating states; not energy/heatflux.')
 if n=='validate.py':
  s=s.replace('(520,91,4)','(520,91,7)').replace('armraw[:,:,3]=0','armraw[:,:,4:]=0')
 if n=='analyze.py':
  s=s.replace("(2,'Fuel-gas release MAE kg/s')","(2,'Fuel-gas release MAE kg/s'),(3,'Surface-heating index MAE K'),(4,'Heating moment X MAE K m'),(5,'Heating moment Y MAE K m'),(6,'Heating moment Z MAE K m')")
 (r/n).write_text(s)
(r/'prepare.py').write_text('''from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parent;a=np.load(R.parent/'attempt20/data/sequences.npz');v=np.load(R.parent/'attempt21/data/spatial_candidates.npz');assert np.array_equal(a['time'],v['time']);data={k:a[k] for k in a.files};data['state']=np.concatenate([a['state'],v['values'][:,:,2:]],-1).astype('float32');assert data['state'].shape==(520,91,7);np.savez_compressed(R/'data/sequences.npz',**data)
s=json.loads((R.parent/'attempt20/schema.json').read_text());s['state_names']+=['surface_heating_moment_x_Km','surface_heating_moment_y_Km','surface_heating_moment_z_Km'];s['physical_encoding_scales']+=[100.,100.,100.];s['model_input_shape']=[None,37];s['model_output_shape']=[None,7];s['comparison']='Same32-memory GRUs; scalar masks3spatial channels, spatial enables3surfaceheating moments relative to measuredinitialmasscentroid. No energy or heatflow claim.';(R/'schema.json').write_text(json.dumps(s,indent=2))
''')
p=json.loads((o/'coverage-plan.json').read_text());p.update(experiment='Matched four-state scalar versus seven-state spatial-heating GRU',arms=['scalar','spatial'],state_features=7,input_features=37,architecture='BothGRU37->32->7; scalar maskslast3history/readoutchannels effective25inputs4outputs, spatial37inputs7outputs. Sameinitializedparameters.',thermal_loss='Original4channel loss unchanged with1/3weight each; add each normalized spatial component squared error at1/3. Tests spatial observations plus spatial supervision, not isolated causality. Select ONLY original3state validation.',stage3_decision='Validation-only: scalar improves gasrelease but residual remains; spatial offset y modest absolute-error Spearman.202 afterwithin-time heatingdecilecentering, signedassociationweak; confoundingpossible. JustifiesONE controlledablation,notpresumptionofbenefit. No test scores used to choose this addition.')
(r/'coverage-plan.json').write_text(json.dumps(p,indent=2))
d=yaml.safe_load((o/'dvc.yaml').read_text());d['stages']['prepare_data']['deps']=['prepare.py','../attempt20/data/sequences.npz','../attempt20/schema.json','../attempt21/data/spatial_candidates.npz'];d['stages']['package']['deps']=sorted(set(d['stages']['package']['deps'])|{x.name for x in r.glob('*.py')});(r/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))

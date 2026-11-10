"""Per-case raw restore -> agreed cone datasets -> HF restore -> exact local raw cleanup.
Never launches simulations; every stage is resumable and independently receipted.
"""
from pathlib import Path
import argparse,os,fcntl,hashlib,json,shutil,subprocess,sys,time,traceback
import numpy as np
import requests,yaml
from preview_training import R,ROOT,extract,temperatures,sha,SOLVE_OVERRIDES,SOURCE_CASE_OVERRIDES
from investigate_cone_pivot import search_grid,search_continuous,evaluate
import spatial_training_variants as anchored
import cone_comparison_preview as comparison
sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf
STATE=R/'private07/continuous-training';OUT=R/'data/training-both-formats'

def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def publish(paths):
 with (ROOT/'.git/preservation-publish.lock').open('w') as publication:
  fcntl.flock(publication,fcntl.LOCK_EX)
  paths=[str(p.relative_to(ROOT)) for p in paths]
  subprocess.run(['git','commit','--only','-m','Preserve both training formats for one verified scenario','--',*paths],cwd=ROOT,check=True)
  subprocess.run(['git','push'],cwd=ROOT,check=True)
  commit=git('rev-parse','HEAD');remote=git('ls-remote','origin','refs/heads/'+git('branch','--show-current')).split()[0]
  subprocess.run(['git','merge-base','--is-ancestor',commit,remote],cwd=ROOT,check=True);return commit

def cases():
 result={}
 for folder in sorted((R/'data').glob('completed*')):
  for p in sorted(folder.rglob('proof.json')):
   if not p.parent.name.startswith('tree51_'):continue
   d=json.loads(p.read_text())
   if d.get('passed') and d.get('physical_time_s')==180:result[p.parent.name]=p
 previews={p.parent.parent.name for base in ['cone-comparison-preview','ten-case-cone-preview','conifer-cone-preview'] for p in (R/'data'/base).glob('tree*/cone/training.npz')}
 return sorted(result.items(),key=lambda x:(x[0] not in previews,x[0]))

def reused_cases():
 mapping=json.loads((R/'private07/reused-training-source-map.json').read_text());assert mapping['passed'] and mapping['count']==22
 result=[]
 for row in mapping['cases']:
  proof=ROOT/row['proof_path'];assert sha(proof)==row['proof_sha256'];result.append((row['target_case'],proof))
 return result

def raw_restore(case,proofpath,work):
 record=work/'raw-verified.json';dest=ROOT/'.artifact-staging/continuous-raw'/case
 if record.exists():
  d=json.loads(record.read_text());assert d['passed'];return d,dest
 scope=next(p for p in proofpath.parents if (p/'dvc.lock').exists());lock=yaml.safe_load((scope/'dvc.lock').read_text());name=str(proofpath.parent.relative_to(scope));owners=[o for stage in lock['stages'].values() for o in stage.get('outs',[]) if name==o['path'] or name.startswith(o['path']+'/')];owner=max(owners,key=lambda o:len(o['path']));h=owner['md5'];assert h.endswith('.dir')
 response=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:],timeout=90);response.raise_for_status();assert hashlib.md5(response.content).hexdigest()==h[:-4]
 prefix=name[len(owner['path']):].strip('/');entries=[]
 for e in response.json():
  if prefix and not e['relpath'].startswith(prefix+'/'):continue
  rel=e['relpath'][len(prefix)+1:] if prefix else e['relpath'];assert '..' not in Path(rel).parts and not Path(rel).is_absolute()
  entries.append({'path':str(proofpath.parent/rel),'md5':e['md5'],'hash':'md5'})
 assert entries and all(Path(e['path']).is_relative_to(proofpath.parent) for e in entries)
 pointer=work/'raw.dvc';pointer.write_text(yaml.safe_dump({'outs':entries}));hf.STATE=work/'raw-restore';hf.STATE.mkdir(exist_ok=True)
 # Partial restoration is retained for diagnosis; never silently discarded.
 if dest.exists() and any(dest.iterdir()):raise RuntimeError('Unverified partial restoration exists; requires inspection')
 hf.restore_records([str(pointer)],dest)
 proof=json.loads(proofpath.read_text());restored=dest/proofpath.parent.relative_to(ROOT);assert sha(restored/'proof.json')==sha(proofpath)
 expected={}
 for f in proof['files']:
  p=restored/f['path'];assert sha(p)==f['sha256'];expected[os.path.relpath(proofpath.parent/f['path'],R)]=f['sha256']
 result={'passed':True,'case':case,'owner_path':owner['path'],'owner_md5':h,'case_path':os.path.relpath(proofpath.parent,R),'source_case':proofpath.parent.name,'owner_experiment':str(scope.relative_to(ROOT)),'entries':entries,'raw_inputs_sha256':expected,'restored_files':len(entries)};save(record,result);return result,dest

def generate(case,raw,dest,work):
 target=OUT/case
 if (target/'validation.json').exists():return
 # Reuse already validated preview bytes, rather than refit completed previews.
 for base in ['cone-comparison-preview','ten-case-cone-preview','conifer-cone-preview']:
  prior=R/'data'/base/case
  if (prior/'free_cone/training.npz').exists():
   target.mkdir(parents=True,exist_ok=True)
   m=json.loads((prior/'cone/metadata.json').read_text());assert m['raw_temperature_sha256']==raw['raw_inputs_sha256'][raw['case_path']+'/solve/'+case+'_1_1.sf']
   for kind in ['cone','free_cone']:shutil.copytree(prior/kind,target/kind,dirs_exist_ok=True)
   save(target/'provenance.json',{'case':case,'reused_preview':str(prior.relative_to(R)),'original_raw_proof_sha256':sha(R/raw['case_path']/'proof.json')});validate(target);return
 scratch=work/'generated';base=scratch/'base';inter=scratch/'anchored';report=scratch/'fit-report.json';source=(R/raw['case_path']/'solve').resolve();SOLVE_OVERRIDES[case]=dest/source.relative_to(ROOT);SOURCE_CASE_OVERRIDES[case]=raw.get('source_case',case)
 if not (base/case/'metadata.json').exists():
  spec={'case':case,'restoration_receipt':str(work/'raw-verified.json'),'original_solve':os.path.relpath(source,R),'HF_restored':True}
  if SOURCE_CASE_OVERRIDES[case]!=case:
   mapping=next(v for v in json.loads((R/'private07/reused-training-source-map.json').read_text())['cases'] if v['target_case']==case);assert mapping['source_case']==SOURCE_CASE_OVERRIDES[case];spec['expected_wet_mass_kg']=mapping['source_design']['expected_wet_mass_kg']
  extract(spec,base)
 if not report.exists():
  meta=json.loads((base/case/'metadata.json').read_text());domain=meta['domain_m'];shape=np.rint(np.array(domain)/.5).astype(int);center=meta['tree_center_xy_m'];xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in shape],indexing='ij'),-1).reshape(-1,3);rows=[]
  for t,a in temperatures(SOLVE_OVERRIDES[case]/(SOURCE_CASE_OVERRIDES[case]+'_1_1.sf'),domain,.5):
   temp=a.reshape(-1);points=xyz[temp>50];row={'time_s':t,'active':bool(len(points)),'hot_cells':len(points)}
   if len(points):
    anchor=np.r_[center,0]+meta['static_inputs']['ignition_contact_relative_xyz_m'];c=search_grid(points,anchor[:2],[anchor[2]],range(-180,180,15));free,seeds=search_continuous(points,center,meta['static_inputs']['total_height_m'],domain,True,True);row['fits']={'ignition_apex':evaluate(c,xyz,temp),'plus_horizontal_apex':{**evaluate(free,xyz,temp),'seed_fits':seeds}}
   rows.append(row)
  save(report,{'cases':[{'case':case,'frames':rows}]})
 anchored.BASE=base;anchored.OUT=inter;anchored.REPORT=report;anchored.generate(case,kinds=('cone',));comparison.BASE=inter;comparison.OUT=OUT;comparison.REPORT=report;comparison.generate(case)
 shutil.copy2(report,target/'fit-report.json');shutil.copy2(base/case/'metadata.json',target/'extraction-provenance.json');validate(target)

def validate(target):
 a=np.load(target/'cone/training.npz');b=np.load(target/'free_cone/training.npz');assert np.array_equal(a['time_s'],b['time_s']) and np.array_equal(a['state'][:,:4],b['state'][:,:4]);result=[]
 for kind,n in [('cone',11),('free_cone',14)]:
  p=target/kind;d=np.load(p/'training.npz');v=d['state'];m=json.loads((p/'metadata.json').read_text());assert sha(p/'training.npz')==m['training_npz_sha256'];assert v.shape==(91,n) and np.isfinite(v).all()
  assert d['time_s'][0]==0 and d['time_s'][-1]==180 and np.all(np.diff(d['time_s'])>0)
  assert (d['right_weight']>=0).all() and (d['right_weight']<=1).all()
  for i,t in enumerate(d['source_time_s']):assert np.array_equal(v[np.flatnonzero(d['time_s']==t)[0],4:],d['source_spatial_state'][i])
  for row in v[:,4:]:
   if row[0]==0:assert (row==0).all()
   else:assert abs(np.linalg.norm(row[1:4] if kind=='cone' else row[4:7])-1)<1e-12
  s=json.loads((p/'first-transition.json').read_text());assert np.array_equal(s['initial_state']['values'],v[0]) and np.array_equal(s['next_state']['values'],v[1]);result.append({'variant':kind,'sha256':sha(p/'training.npz'),'rows':91,'channels':n,'observed':int(d['observed'].sum()),'interpolated':int(d['interpolated'].sum())})
 save(target/'validation.json',{'passed':True,'checks':result})

def preserve(case,work):
 receipt=work/'training-preserved.json'
 if receipt.exists():return json.loads(receipt.read_text())
 hf.STATE=work/'training-hf';hf.STATE.mkdir(exist_ok=True);hf.objects.clear();hf._hashes.clear();hf.review.clear()
 path=R/'dvc.yaml';doc=yaml.safe_load(path.read_text());stage='training_both_'+case;rel=str((OUT/case).relative_to(R));doc['stages'][stage]={'cmd':f'../../.venv/bin/python continuous_training.py --case {case}'+(' --reused-only' if json.loads((work/'raw-verified.json').read_text()).get('source_case',case)!=case else ''),'frozen':True,'deps':['continuous_training.py','preview_training.py','spatial_training_variants.py','cone_comparison_preview.py','investigate_cone_pivot.py'],'outs':[rel]};path.write_text(yaml.safe_dump(doc,sort_keys=False));hf.stage_commit(str(path)+':'+stage)
 lp=R/'dvc.lock';lock=yaml.safe_load(lp.read_text());lock['stages'][stage]['deps']=[{'path':x,'hash':'md5','md5':hashlib.md5((R/x).read_bytes()).hexdigest(),'size':(R/x).stat().st_size} for x in doc['stages'][stage]['deps']];lp.write_text(yaml.safe_dump(lock,sort_keys=False));hf.upload(hf.STATE/'plan.json')
 rec=lock['stages'][stage]['outs'][0].copy();rec['path']=str(R/rec['path']);pointer=work/'training.dvc';pointer.write_text(yaml.safe_dump({'outs':[rec]}));check=ROOT/'.artifact-staging/continuous-training-roundtrip'/case
 if not (hf.STATE/'restore-verification.json').exists():hf.restore_records([str(pointer)],check)
 assert json.loads((hf.STATE/'restore-verification.json').read_text())['passed'];validate(OUT/case)
 # Validation rewrites identical bytes, and must not change the locked artifact.
 for f in (OUT/case).rglob('*'):
  if f.is_file():assert sha(f)==sha(check/f.relative_to(ROOT))
 commit=publish([path,lp]);result={'passed':True,'git_commit':commit,'directory_md5':rec['md5'],'restoration_passed':True};save(receipt,result);return result

def cleanup(case,raw,dest,work,training):
 assert training['passed'] and training['restoration_passed'];assert json.loads((work/'raw-verified.json').read_text())['passed']
 # Preflight every original file: never remove unknown extras or mismatching bytes.
 original=(R/raw['case_path']).resolve();entries={Path(e['path']):e['md5'] for e in raw['entries']};planned=[]
 for p in (original/'solve').rglob('*'):
  if p.is_file():
   if p not in entries:raise RuntimeError('Untracked local raw file: '+str(p))
   assert not p.is_symlink() and hf.digest(p)[0]==entries[p];planned.append(p)
 save(work/'cleanup-plan.json',{'case':case,'paths':[str(p.relative_to(ROOT)) for p in planned],'raw_verified':True,'training_verified':True})
 removed=[]
 for p in planned:
  assert hf.digest(p)[0]==entries[p];n=p.stat().st_size;p.unlink();removed.append({'path':str(p.relative_to(ROOT)),'bytes':n,'md5':entries[p]})
 # This is this worker's isolated, already verified raw restoration, not training data.
 assert dest==ROOT/'.artifact-staging/continuous-raw'/case and dest.is_relative_to(ROOT/'.artifact-staging/continuous-raw')
 if dest.exists():shutil.rmtree(dest)
 save(work/'complete.json',{'passed':True,'case':case,'training_directory':str((OUT/case).relative_to(ROOT)),'raw_DVC_owner_md5':raw['owner_md5'],'training_preservation':training,'local_raw_files_removed':removed,'original_proof_retained':True,'training_retained':True});print('CASE COMPLETE',case,'local_raw_bytes_freed',sum(x['bytes'] for x in removed),flush=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case');ap.add_argument('--forever',action='store_true');ap.add_argument('--reused-only',action='store_true');args=ap.parse_args();STATE.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
 with (STATE/'worker.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   queue=reused_cases() if args.reused_only else cases();done=0;deferred=[]
   for case,proof in queue:
    if args.case and case!=args.case:continue
    work=STATE/case;work.mkdir(exist_ok=True)
    if (work/'complete.json').exists():done+=1;continue
    if shutil.disk_usage(ROOT).free<4*1024**3:raise RuntimeError('4GiB disk guard; no unsafe deletion')
    try:
     print('CASE START',case,flush=True);raw,dest=raw_restore(case,proof,work);generate(case,raw,dest,work);training=preserve(case,work);cleanup(case,raw,dest,work,training);done+=1
    except Exception as e:
     save(work/'deferred.json',{'case':case,'error':str(e),'traceback':traceback.format_exc(),'time':time.time(),'raw_retained':True});deferred.append(case);print('DEFERRED',case,str(e),flush=True)
    save(STATE/'status.json',{'eligible_proof_cases':len(queue),'completed':done,'deferred_this_pass':deferred,'last_case':case,'time':time.time(),'simulation_verified_count':1899,'older_reused_cases_mapping_pending':22})
   if not args.forever:break
   print('WAITING FOR UPLOADS OR RECOVERY',flush=True);time.sleep(300)
if __name__=='__main__':main()

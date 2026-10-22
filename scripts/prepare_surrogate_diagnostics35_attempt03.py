from pathlib import Path
import json,shutil,yaml
root=Path('/Users/wdavies/pi/wildfire3d');r=root/'experiments/35_surrogate_diagnostics';old=r/'attempt02';a=r/'attempt03';a.mkdir();(a/'data/resume').mkdir(parents=True);(a/'results').mkdir()
for p in old.glob('*.py'):
 s=p.read_text().replace('gpu35-diag02','gpu35-diag03').replace('diag35-02','diag35-03').replace('diagnostics35/attempt02','diagnostics35/attempt03')
 if p.name=='launch.py':s=s.replace('diagnostics35/attempt03/restored/','diagnostics35/attempt02/restored/')
 (a/p.name).write_text(s)
for n in ['cases.json','groups.json','coverage-plan.json','input-sources.json','dvc.yaml']:shutil.copy2(old/n,a/n)
(a/'restore-manifest.json').write_text('[]\n');shutil.copy2(old/'data/geometries.npz',a/'data/geometries.npz');shutil.copy2(r/'results/replica-time-audit.json',a/'replica-time-audit.json')
p=a/'worker.py';s=p.read_text();oldline="   a,t=arrays[cc[0]['case']];b,tb=arrays[cc[1]['case']];assert np.array_equal(t,tb);pairs.append(dict(configuration=cfg,cases=[c['case'] for c in cc],metrics=metrics(np.array(a),np.array(b),t)))";new="""   a,t=arrays[cc[0]['case']]
   for other in cc[1:]:
    b,tb=arrays[other['case']];ids=np.abs(tb[:,None]-t).argmin(0);delta=np.abs(tb[ids]-t);assert len(set(ids.tolist()))==len(t) and float(delta.max())<=.2
    pairs.append(dict(configuration=cfg,cases=[cc[0]['case'],other['case']],alignment='nearest existing frame, one-to-one, maximum0.2s',max_time_offset_s=float(delta.max()),metrics=metrics(np.array(a),np.array(b[ids]),t)))""";assert oldline in s;s=s.replace(oldline,new).replace('Pairwise FDS realization differences; descriptive, not a calibrated irreducible error bound.','Eight primary-versus-replica comparisons across four configurations; nearest-frame timing mismatch<=0.2s is included. Descriptive, not a calibrated irreducible error bound.');p.write_text(s)
p=a/'validate.py';s=p.read_text();s=s.replace("validate();torch.manual_seed", "audit=json.loads((R/'replica-time-audit.json').read_text());assert len(audit['rows'])==8 and audit['max_delta_s']<=.2 and all(v['distinct_mapping'] for v in audit['rows'])\nvalidate();torch.manual_seed");p.write_text(s)
p=a/'prepare_pilot.py';s=p.read_text().replace("R/'coverage-plan.json'", "R/'coverage-plan.json',R/'replica-time-audit.json'");p.write_text(s)
p=a/'dvc.yaml';d=yaml.safe_load(p.read_text());d['stages']['package']['deps'].append('replica-time-audit.json');p.write_text(yaml.safe_dump(d,sort_keys=False))
(a/'README.md').write_text((old/'README.md').read_text()+"\n\nAttempt03 separately reserves4.50 after attempt02 completed preprocessing and CUDA checks but failed exact timestamp equality BEFOREtraining. Raw slice audit:8 primary-vs-replica pairs from4 triple-seed configs; maxdifference0.155724s, each91frames, all nearestmatches sameindices. Pairdiagnostic now accepts one-to-one nearestframes<=.2s and records offset; includes temporaljitter, not pure stochasticerrorfloor. Alltraining/validationtargets and optimization unchanged. Reuse five hashverified bundles fromattempt02/restored via narrow temporaryprefixgrant. No automaticretry or recycledbudget. Cumulative83.60/100.\n")
(old/'results/failure-diagnosis.json').write_text(json.dumps(dict(cause='Exact replica timestamp equality assertion; FDS output jitter up to0.155724s across8pairs',before_training=True,cleanup_verified=True,fix='one-to-one nearest frames<=0.2s only for variability diagnostic; training unchanged',replacement='attempt03 separately reserved'),indent=2))
shutil.copy2('/tmp/prepare35r3.py',root/'scripts/prepare_surrogate_diagnostics35_attempt03.py')

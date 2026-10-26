"""Prepare a distinct recovery watchdog; never upload, deploy, or submit."""
from pathlib import Path
import hashlib,json,yaml
R=Path(__file__).resolve().parent.parent

def main():
 plan=json.loads((R/'results/partial-recovery-plan.json').read_text());groups=json.loads((R/'active-groups.json').read_text());old=plan['original_group'];new=plan['new_group'];g=next(x for x in groups if x['id']==old)
 p=R/'jobs'/old/g.get('workflow_file','workflow.yaml');source=p.read_text();assert hashlib.sha256(p.read_bytes()).hexdigest()==g['workflow_sha256']
 assert old in source and g['package_sha256'] in source
 transformed=source.replace(old,new).replace(g['package_sha256'],plan['package_sha256'])
 # Entire change is identity and hash of the already verified nine-case package.
 assert transformed.replace(new,old).replace(plan['package_sha256'],g['package_sha256'])==source
 assert yaml.safe_load(transformed)
 folder=R/'jobs'/new;folder.mkdir(exist_ok=True);dest=folder/'workflow.yaml'
 if dest.exists():assert dest.read_text()==transformed
 else:dest.write_text(transformed)
 proof={'group':new,'original_group':old,'cases':plan['cases'],'excluded_completed_cases':plan['reused_completed_cases'],'workflow_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_workflow_sha256':g['workflow_sha256'],'package_sha256':plan['package_sha256'],'image_uri':g['image_uri'],'only_identity_and_package_hash_changed':True,'submitted':False,'requirements_before_submission':['Verify all parent queue groups have immutable intents and active job/VM count below20, or parent terminal','Inspect existing replacement executions/jobs/output intent for unknown prior submission','Reserve0.40 within125cap','Verify image exists and package hash; immutable input upload','Use distinct replacement identity, never replay original032 or completedcases'],'note':'Does not modify active-groups or cloud owner; local dispatcher remains disabled.'}
 (R/'results/partial-recovery-workflow.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()

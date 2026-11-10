"""Validate completed preservation receipts and emit a bounded public audit summary."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/51_three_tree_campaign/private07'
classification=json.loads((p/'final-inventory-classification.json').read_text());assert not classification['unresolved']
training=[json.loads(f.read_text()) for f in (p/'continuous-training').glob('*/complete.json')];assert len(training)==1880 and all(x['passed'] and x['training_retained'] for x in training)
assert all((ROOT/'experiments/51_three_tree_campaign/data/training-both-formats'/x['case']).is_dir() for x in training)
deferred=[f.parent.name for f in (p/'continuous-training').glob('*/deferred.json') if not f.with_name('complete.json').exists()];assert len(deferred)==19
names=['reviewed-raw-log','historical-array','historical-support','historical-geometry','historical-boundary-text','historical-archive','historical-45-46','unmanifested-archive','historical-training-metrics','diagnostic-science']
batches={}
for name in names:
 r=json.loads((p/(name+'-preservation')/'complete.json').read_text());assert r['passed'] and r['restoration_sha256_verified']
 subprocess.run(['git','merge-base','--is-ancestor',r['git_commit'],'@{u}'],cwd=ROOT,check=True)
 batches[name]={'original_files':r['original_files'],'unique_files':r['unique_archived_files'],'git_commit':r['git_commit'],'full_restoration_verified':True}
local=[json.loads(f.read_text()) for f in (p/'local-archive-preservation').glob('*/complete.json')];assert len(local)==122 and all(x['passed'] and x['restoration_sha256_verified'] for x in local)
cloud=[json.loads(f.read_text()) for f in (p/'raw-migration-receipts').glob('*.json')]
cloud=[r for r in cloud if 'source_manifest' in r];assert len(cloud)==2825 and all(r['passed'] for r in cloud)
remote=json.loads((p/'missing-output-remote/verification.json').read_text());assert len(remote)==19 and all(x['remote_present'] and x['download_md5_verified'] for x in remote)
assert all(x['all_member_paths_present'] for x in remote if x['md5'].endswith('.dir'))
deleted=json.loads((p/'historical-boundary-text-preservation/local-original-deletion.json').read_text());assert deleted['passed'] and len(deleted['removed'])==1788
summary={'status':'audited preservation scope closed; training exceptions intentionally deferred','verified_simulations':1899,'planned_simulations':2000,'dual_format_training_preserved':1880,'training_cases_deferred':19,'training_retained_locally':True,'raw_original_bytes_removed':sum(x['bytes'] for r in training for x in r['local_raw_files_removed']),'boundary_text_originals_removed':1788,'boundary_text_bytes_removed':deleted['bytes_removed'],'cloud_archives_preserved':2825,'older_local_archives_preserved':122,'additional_batches':batches,'audit_inventory_counts':classification['counts'],'unresolved_candidate_classifications':0,'missing_local_records':{'total':166,'verified_archive_evictions':139,'corrected_paths_exact_hash':8,'fresh_remote_file_restorations':17,'remote_directory_manifest_and_member_availability':2},'limitations':['Scope is the recorded repository inventories and preservation queues, not every historical Git revision or external filesystem.','Two older export directories were checked by exact manifest hashes and remote member availability; their complete contents were not freshly restored.','Private financial, credential, operational and tool-state records remain local and are excluded from public preservation.','19 anchored-cone fitting failures remain deferred in BOTH formats by user decision, with raw retained.','No new simulations or model training were performed; sparse spatial observations and interpolated rows remain distinguished.'],'irrecoverable_loss_established_by_this_audit':False}
out=ROOT/'experiments/51_three_tree_campaign/PRESERVATION_CLOSEOUT.json';out.write_text(json.dumps(summary,indent=2)+'\n');print('PASS bounded preservation closeout;1880 training,19 deferred;0 unresolved inventory classifications')

"""Generate fixed single-worker workflow; controller runs independently of laptop."""
import argparse,json
from pathlib import Path
import yaml

P='tmrw-wildfire-20261015';REGION='us-central1';ZONE='us-central1-a';BUCKET=P+'-trial'
ROOT=Path(__file__).resolve().parent

def job(image,mode):
    return {'taskGroups':[{'taskCount':'1','parallelism':'1','taskCountPerNode':'1','taskSpec':{
        'computeResource':{'cpuMilli':4000,'memoryMib':12000},'maxRunDuration':'30s' if mode=='timeout' else '600s',
        'maxRetryCount':0,'runnables':[{'container':{'imageUri':image,'options':'--cpus=4 --memory=12g --pids-limit=256'},
            'environment':{'variables':{'TRIAL_MODE':mode,'OUTPUT_BUCKET':BUCKET,'OUTPUT_PREFIX':mode}}}]
    }}],'allocationPolicy':{'instances':[{'policy':{'machineType':'c3-standard-4','provisioningModel':'SPOT','bootDisk':{'sizeGb':'30','type':'pd-balanced'}}}],
        'location':{'allowedLocations':['zones/'+ZONE]},'serviceAccount':{'email':f'fds-worker@{P}.iam.gserviceaccount.com'},
        'labels':{'trial_id':'study15'},'network':{'networkInterfaces':[{'network':f'projects/{P}/global/networks/fds-trial','subnetwork':f'projects/{P}/regions/{REGION}/subnetworks/fds-trial'}]}},
        'labels':{'trial_id':'study15'},'logsPolicy':{'destination':'CLOUD_LOGGING'}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--image',required=True);a=ap.parse_args()
    if '@sha256:' not in a.image:raise ValueError('Immutable image digest required')
    for mode in ['science','timeout','watchdog']:
        cfg=job(a.image,mode)
        (ROOT/f'job-{mode}.json').write_text(json.dumps(cfg,indent=2)+'\n')
        # Fixed shared job ID prevents concurrent workflows from creating multiple workers.
        joburl=f'https://batch.googleapis.com/v1/projects/{P}/locations/{REGION}/jobs/fds-controlled-trial'
        base=f'https://batch.googleapis.com/v1/projects/{P}/locations/{REGION}/jobs'
        instanceurl=f'https://compute.googleapis.com/compute/v1/projects/{P}/zones/{ZONE}/instances'
        steps=[{'initialize':{'assign':[{'deadline':'${sys.now() + '+str(180 if mode=='watchdog' else 900)+'}'},{'job':cfg},{'status':{'body':{'status':{'state':'UNKNOWN'}}}}]}},
            {'create':{'call':'http.post','args':{'url':base,'query':{'jobId':'fds-controlled-trial'},'auth':{'type':'OAuth2'},'body':'${job}'},'result':'created'}},
            {'get_status':{'call':'http.get','args':{'url':joburl,'auth':{'type':'OAuth2'}},'result':'status'}},
            {'check':{'switch':[{'condition':'${status.body.status.state == "SUCCEEDED" or status.body.status.state == "FAILED"}','next':'record'},
                {'condition':'${sys.now() >= deadline}','next':'record'}]}},
            {'wait':{'call':'sys.sleep','args':{'seconds':15},'next':'get_status'}},
            {'record':{'try':{'call':'http.post','args':{'url':f'https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o',
                'query':{'uploadType':'media','name':mode+'/job-status.json'},'auth':{'type':'OAuth2'},'headers':{'Content-Type':'application/json'},'body':'${status.body}'}},
                'except':{'as':'record_error','steps':[{'record_failure':{'call':'sys.log','args':{'text':'Could not persist final status; proceeding with cleanup','severity':'ERROR'}}}]}}},
            {'delete_job':{'call':'http.delete','args':{'url':joburl,'auth':{'type':'OAuth2'}},'result':'deletion'}},
            {'cleanup_wait':{'call':'sys.sleep','args':{'seconds':30}}},
            {'list_workers':{'call':'http.get','args':{'url':instanceurl,'query':{'filter':'labels.trial_id = study15'},'auth':{'type':'OAuth2'}},'result':'workers'}},
            {'delete_stragglers':{'for':{'value':'vm','in':'${default(map.get(workers.body, "items"), [])}','steps':[
                {'delete_vm':{'call':'http.delete','args':{'url':'${"'+instanceurl+'/" + vm.name}','auth':{'type':'OAuth2'}}}}]}}},
            {'verify_wait':{'call':'sys.sleep','args':{'seconds':30}}},
            {'verify':{'call':'http.get','args':{'url':instanceurl,'query':{'filter':'labels.trial_id = study15'},'auth':{'type':'OAuth2'}},'result':'remaining'}},
            {'assert_empty':{'switch':[{'condition':'${len(default(map.get(remaining.body, "items"), [])) > 0}','raise':'Cleanup incomplete: labeled workers remain'}]}},
            {'done':{'return':{'mode':mode,'final_state':'${status.body.status.state}','workers_remaining':0,'job_uid':'${created.body.uid}'}}}]
        monitor=steps[2:5]
        steps[2:5]=[{'monitor':{'try':{'steps':monitor},'except':{'as':'monitor_error','steps':[{'monitor_failure':{'call':'sys.log','args':{'text':'Monitoring failed; proceeding to cleanup','severity':'ERROR'}}}]}}}]
        for step in steps:
            if 'delete_job' in step:
                action=step['delete_job']
                step['delete_job']={'try':action,'except':{'as':'delete_error','steps':[{'delete_failure':{'call':'sys.log','args':{'text':'Batch deletion failed; checking workers directly','severity':'ERROR'}}}]}}
        (ROOT/f'workflow-{mode}.yaml').write_text(yaml.safe_dump({'main':{'steps':steps}},sort_keys=False))

if __name__=='__main__':main()

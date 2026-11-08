"""Move pinned cloud raw archives to DVC/HF, one bounded verified archive at a time.

Reads a private JSON object inventory. Never submits jobs or deletes cloud data.
Original archives remain byte-identical; public-upload policy must accept all members.
Receipts and source object identifiers remain private. Existing output pointers are
never recomputed after staging eviction. Use --limit for a bounded validation run.
"""
import argparse, base64, fcntl, hashlib, json, os, pathlib, shutil, subprocess, sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
ROOT=pathlib.Path(__file__).resolve().parents[1]

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--inventory',required=True);ap.add_argument('--output',required=True);ap.add_argument('--receipts',required=True);ap.add_argument('--limit',type=int);a=ap.parse_args()
    output=(ROOT/a.output).resolve();receipts=(ROOT/a.receipts).resolve()
    assert output.is_relative_to(ROOT) and receipts.is_relative_to(ROOT)
    output.mkdir(parents=True,exist_ok=True);receipts.mkdir(parents=True,exist_ok=True)
    with (receipts/'migration.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        items=json.loads((ROOT/a.inventory).read_text());index={x['name']:x for x in items}
        manifests=sorted((x for x in items if x['name'].endswith('/archive-manifest.json')),key=lambda x:x.get('timeCreated',''))
        s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,status_forcelist=[429,500,502,503,504],allowed_methods=['GET'])))
        def auth():s.headers['Authorization']='Bearer '+subprocess.check_output([str(pathlib.Path.home()/'.local/google-cloud-sdk/bin/gcloud'),'auth','print-access-token'],text=True).strip()
        auth()
        def get(v):
            q=s.get(v['mediaLink'],timeout=180)
            if q.status_code==401:auth();q=s.get(v['mediaLink'],timeout=180)
            q.raise_for_status();b=q.content
            assert len(b)==int(v['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==v['md5Hash']
            return b
        state=ROOT/'experiments/43_repository_preservation/results/direct-hf';done=0
        for m in manifests:
            key=hashlib.sha256((m['name']+'@'+m['generation']).encode()).hexdigest()[:24]
            receipt=receipts/(key+'.json');planpath=receipts/(key+'-plan.json');archive=output/(key+'.tar.gz');pointer=archive.with_name(archive.name+'.dvc')
            if receipt.exists():
                old=json.loads(receipt.read_text())
                if old.get('passed'):continue
            if shutil.disk_usage(output).free<4*1024**3:raise RuntimeError('Disk guard: 4 GiB required')
            try:
                manifest=json.loads(get(m));assert manifest['complete'] and manifest['bytes']<2*1024**3
                prefix=m['name'].rsplit('/',1)[0]+'/'
                # Never trust a partial archive or silently substitute another generation.
                if not archive.exists():
                    partial=archive.with_suffix('.partial')
                    with partial.open('wb') as f:
                        for part in manifest['parts']:
                            v=index[prefix+part['name']];b=get(v)
                            assert hashlib.sha256(b).hexdigest()==part['sha256'] and len(b)==part['bytes'];f.write(b)
                    assert partial.stat().st_size==manifest['bytes'];partial.replace(archive)
                assert archive.stat().st_size==manifest['bytes']
                source_sha=sha(archive)
                if not planpath.exists():
                    if pointer.exists():raise RuntimeError('Pointer exists without dedicated plan; inspect before continuing')
                    subprocess.run([sys.executable,str(ROOT/'scripts/dvc_hf.py'),'track',str(archive)],cwd=ROOT,check=True)
                    shutil.copyfile(state/'plan.json',planpath)
                plan=json.loads(planpath.read_text());assert len(plan['objects'])==1
                obj=next(iter(plan['objects'].values()));assert obj['source']==str(archive.relative_to(ROOT)) and obj['sha256']==source_sha
                subprocess.run([sys.executable,str(ROOT/'scripts/dvc_hf.py'),'push','--plan',str(planpath)],cwd=ROOT,check=True)
                verified=json.loads((state/'upload-verification.json').read_text());assert verified['passed'] and verified['remote_size_and_xet_verified'] and verified['plan_sha256']==sha(planpath)
                # Publish only the DVC pointer; no private cloud inventory or identifiers.
                subprocess.run(['git','add','-f','--',str(pointer.relative_to(ROOT)),str((output/'.gitignore').relative_to(ROOT))],cwd=ROOT,check=True)
                if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
                    subprocess.run(['git','commit','-m','Preserve pinned raw simulation archive in DVC'],cwd=ROOT,check=True)
                subprocess.run(['git','push'],cwd=ROOT,check=True)
                head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
                remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0];assert remote==head
                save(receipt,dict(passed=True,source_manifest=m['name'],source_generation=m['generation'],archive_sha256=source_sha,bytes=archive.stat().st_size,verification=verified,git_commit=head))
                assert sha(archive)==source_sha;archive.unlink()
                done+=1;print('ARCHIVE VERIFIED',key,'newly_preserved',done,flush=True)
                if a.limit and done>=a.limit:break
            except requests.HTTPError as e:
                if e.response.status_code!=404:raise
                save(receipt,dict(passed=False,source_manifest=m['name'],reason='Pinned cloud generation no longer available'))
                print('MISSING GENERATION',key,flush=True)
        print('PASS completed this invocation',done,flush=True)
if __name__=='__main__':main()

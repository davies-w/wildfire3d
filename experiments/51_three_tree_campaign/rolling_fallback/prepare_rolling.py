"""Offline singleton packaging for a FUTURE audited continuation. Never deploys.

Selection is an explicit list of NEVER-STARTED case IDs, prepared after terminal
allocation/case reconciliation. Interrupted cases require separate reviewed
checkpoint packaging; this tool refuses to fresh-start a recovery bundle.
"""
import argparse
import ast
import base64
import hashlib
import json
import lzma
from pathlib import Path
import re
import yaml
from build import build, Dumper

def singleton(payload, case_id, namespace):
    if 'recovery.json' in payload:
        raise ValueError('Checkpoint recovery requires its own audited restore package')
    cases=json.loads(payload['groups.json'])['wave']
    chosen=[c for c in cases if c['pilot_case']==case_id]
    if len(chosen)!=1: raise ValueError('Case selection is not unique')
    c=chosen[0]; deck='decks/'+case_id+'.fds'
    if hashlib.sha256(payload[deck].encode()).hexdigest()!=c['deck_sha256']:
        raise ValueError('Deck hash mismatch')
    result={k:v for k,v in payload.items() if not k.startswith('decks/') or k==deck}
    result['groups.json']=json.dumps({'wave':[c]})
    # Operational prefixes change; scientific decks and worker implementation do not.
    for name in ('transport.py','checkpoint_control.py'):
        if name in result:
            result[name]=result[name].replace('fds-tree51-campaign04',namespace).replace('tree51/campaign04/','tree51/'+namespace+'/')
            ast.parse(result[name])
    assert result[deck]==payload[deck]
    return result

def render(namespace):
    if not re.fullmatch(r't51r[a-z0-9]{2,5}',namespace):
        raise ValueError('Use a short unique future namespace such as t51r05; never campaign04')
    result={}
    for name,doc in build().items():
        text=yaml.dump(doc,Dumper=Dumper,sort_keys=False).replace('__RUN__',namespace)
        # The bootstrap is base64 embedded; plain YAML replacement is insufficient.
        if name=='case.yaml':
            encoded=re.search("b64decode\\('([^']+)'",text).group(1)
            boot=base64.b64decode(encoded).decode().replace('__RUN__',namespace)
            ast.parse(boot)
            text=text.replace(encoded,base64.b64encode(boot.encode()).decode())
        result[name]=text
    return result

def prepare(source, selected, namespace, output):
    rendered=render(namespace)
    if not selected or len(set(selected))!=len(selected): raise ValueError('Empty/duplicate selection')
    if output.exists(): raise ValueError('Output must be a new isolated directory')
    manifest=json.loads((source/'manifest.json').read_text())
    found={}
    for wave in manifest:
        blob=(source/(wave['id']+'.xz')).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=wave['sha256']: raise ValueError('Source bundle hash mismatch')
        payload=json.loads(lzma.decompress(blob))
        for c in json.loads(payload['groups.json'])['wave']:
            if c['pilot_case'] in selected:
                if c['pilot_case'] in found: raise ValueError('Duplicate source case')
                found[c['pilot_case']]=singleton(payload,c['pilot_case'],namespace)
    if set(found)!=set(selected): raise ValueError('Missing selected cases')
    output.mkdir(parents=True)
    inputs=output/'inputs'; (inputs/'items').mkdir(parents=True)
    for name,text in rendered.items(): (output/name).write_text(text)
    for i,case in enumerate(selected):
        blob=lzma.compress(json.dumps(found[case]).encode(),preset=1); wave=f'wave-{i:06d}'
        (inputs/(wave+'.xz')).write_bytes(blob)
        (inputs/'items'/f'{i}.json').write_text(json.dumps(dict(index=i,id=wave,count=1,case=case,sha256=hashlib.sha256(blob).hexdigest()),indent=2)+'\n')
    # Deliberately fails launch admission until reconciled with the terminal ledger.
    (inputs/'index.json').write_text(json.dumps(dict(count=len(selected),reviewed=False,checkpoint_seconds=480,prior_completed=None,namespace=namespace),indent=2)+'\n')
    return len(selected)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--namespace',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    print(prepare(a.source,json.loads(a.selection.read_text()),a.namespace,a.output),'offline singleton cases; NOT authorized or submitted')

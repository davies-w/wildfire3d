"""Freeze exact rotation-0 training IDs and local temperature sources; no downloads."""
from pathlib import Path
import json,hashlib,collections
R=Path(__file__).resolve().parent;E=R.parent;repo=E.parent
s=json.loads((E/'36_tree_density/learning-schema.json').read_text());rotation=s['rotations'][0]
old={x['conditions']['case']:x for x in json.loads((E/'35_surrogate_diagnostics/attempt12/inventory.json').read_text())}
new={x['case']:x for x in json.loads((E/'36_tree_density/cases.json').read_text())}
rows=[]
for idx in rotation['train']:
    c=s['cases'][idx];n=c['case'];key=c['physical_key'];assert c['fold'] not in [rotation['test_fold'],rotation['validation_fold']]
    if c['source']=='density36':
        folder=E/'36_tree_density/data/verified-material'/n;proof=json.loads((folder/'verified.json').read_text());sf=[x for x in proof['retained_material_inputs'] if x.endswith('.sf')];assert len(sf)==1
        p=folder/sf[0];expected=proof['members'][sf[0]]['sha256'];kind='verified_temperature_slice';conditions=new[n];raw=proof['raw_sha256']
    else:
        item=old[n];p=E/item['archive'];conditions=item['conditions'];proof=json.loads((E/'35_surrogate_diagnostics/attempt12/data/states'/f'{n}.json').read_text());expected=proof['raw_sha256'];kind='verified_local_archive';raw=expected
        if item['expected_sha256']:assert item['expected_sha256']==expected
    assert p.is_file(),p
    rows.append(dict(case=n,case_index=idx,fold=c['fold'],physical_key=key,source_kind=kind,path=p.relative_to(repo).as_posix(),sha256=expected,raw_sha256=raw,bytes=p.stat().st_size,crown_height_m=float(key[0]),wind_speed=float(key[3]),origin_m=[-4,-4,0] if conditions.get('expanded') else [0,0,0]))
assert len(rows)==1662 and len({x['case'] for x in rows})==1662
out=R/'data/training-plan.json';out.parent.mkdir(exist_ok=True)
result=dict(rotation=0,training_only=True,cases=rows,schema_sha256=hashlib.sha256((E/'36_tree_density/learning-schema.json').read_bytes()).hexdigest(),sequence_sha256=hashlib.sha256((E/'36_tree_density/data/learning/sequences.npz').read_bytes()).hexdigest(),case_count=len(rows),source_bytes=sum(x['bytes'] for x in rows),sources=dict(collections.Counter(x['source_kind'] for x in rows)),network_download_required=False)
out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='cases'})

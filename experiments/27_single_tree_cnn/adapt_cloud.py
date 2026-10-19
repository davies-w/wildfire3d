from pathlib import Path
r=Path(__file__).parent
w=(r/'worker.py').read_text();start=w.index('import build');end=w.index('try:\n for c in cases:')
w=w[:start]+'''freeze=json.loads((ROOT/'input-freeze.json').read_text())
for c in cases:
 assert hashlib.sha256((ROOT/'decks'/(c['case']+'.fds')).read_bytes()).hexdigest()==freeze['cases'][c['case']]==c['deck_sha256']
'''+w[end:];(r/'worker.py').write_text(w)
p=r/'cloud.py';s=p.read_text()
a=s.index(" cases=read('cases.json');cal=");b=s.index("   runner=",a)
s=s[:a]+''' cases=read('cases.json');groups=[]
 for phase in ['pilot','domain','train','validation','test']:
  rows=[c for c in cases if c['split']==phase];count=2 if phase in ['pilot','domain'] else 3
  for i in range(0,len(rows),count):
   cs=rows[i:i+count];name=f's27-{phase}-{i//count}';g=dict(id=name,phase=phase,cases=[c['case'] for c in cs],duration_s=5400,allowance_usd=.22)
'''+s[b:]
a=s.index("   payload['build.py']");b=s.index('   encoded=',a)
s=s[:a]+'''   for c in cs:payload['decks/'+c['case']+'.fds']=(ROOT/'decks'/(c['case']+'.fds')).read_text()
   payload['input-freeze.json']=json.dumps(read('results/input-freeze.json'))
'''+s[b:]
s=s.replace('transfer26/','single27/').replace('<2.20001','<=5').replace("startswith('t26-')","startswith('s27-')").replace('default=1.','default=5.')
a=s.index(" checks=read('results/preflight.json')");b=s.index(" with (ROOT/'data/budget.lock')",a)
s=s[:a]+''' checks=read('results/preflight.json');assert len(checks)>=4 and all(x['passed'] for x in checks)
 if g['phase'] not in ['pilot','domain']:assert read('results/pilot-decision.json')['release_development']
 if g['phase']=='test':
  freeze=read('results/prediction-freeze.json')
  for filename,h in freeze['files'].items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==h
'''+s[b:]
p.write_text(s)

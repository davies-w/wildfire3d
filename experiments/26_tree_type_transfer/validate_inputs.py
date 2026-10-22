"""Audit frozen instance identity and leakage boundaries without opening test outputs."""
import json,math,hashlib
from collections import Counter
from pathlib import Path
from build import ROOT,MODELS,CLASSES,deck

def main():
 cases=json.loads((ROOT/'cases.json').read_text());templates=json.loads((ROOT/'data/tree-templates.json').read_text());freeze=json.loads((ROOT/'results/input-freeze.json').read_text())
 assert hashlib.sha256((ROOT/'data/tree-templates.json').read_bytes()).hexdigest()==freeze['template_sha256']
 ids=[c['case'] for c in cases];assert len(ids)==len(set(ids))==32
 assert {c['trees'][0]['type'] for c in cases if c['family']=='single' and c['split']=='train'}==set('ABC')
 assert {''.join(t['type'] for t in c['trees']) for c in cases if c['family']=='pair' and c['split']=='train'}=={'AA','AB','BB'}
 assert {''.join(t['type'] for t in c['trees']) for c in cases if c['split']=='transfer_test' and c['family']=='pair'}=={'AC','BC'}
 for c in cases:
  s,_=deck(c,templates);assert hashlib.sha256(s.encode()).hexdigest()==freeze['cases'][c['case']]
  assert not any(w in s for w in ["SHAPE='CONE'","SHAPE='RING'","N_PARTICLES_PER_CELL"])
  for t in c['trees']:
   assert templates[t['type']]['model']==MODELS[t['type']]
  if c['family']=='control':
   pair=next(p for p in cases if p['case']==c['matched_pair']);assert c['trees']==pair['trees'][1:]
   for field in ['split','heater_type','heater_xy','strength','duration']:assert c[field]==pair[field]
  if c['family']!='single' and c['split'] in ['train','validation']:assert all(t['type']!='C' for t in c['trees'])
 result=dict(passed=True,cases=len(cases),split_counts=dict(Counter(c['split'] for c in cases)),checks=['Explicit vegetation and heater positions only','Deck/template hashes unchanged','C isolated data allowed; C interaction training/validation forbidden','Every removal control retains identical heater and receiver','Whole configurations split'],scope='Input-only audit; no held-out FDS outputs read')
 (ROOT/'results/split-and-instance-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()

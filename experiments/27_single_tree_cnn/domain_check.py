"""Matched domain comparison; no pointwise turbulent agreement requirement."""
import json,csv
import numpy as np
from cloud import ROOT,read,save
from fields import extract

def devices(c,suffix):
 p=ROOT/'data/cloud'/c/(c+suffix)
 with p.open() as f:r=list(csv.reader(f))
 return [v.strip().strip('"') for v in r[1]],np.array(r[2:],float)
def main():
 rows=[]
 for small,large in [('s27_pilot_0','s27_domain_0'),('s27_pilot_3','s27_domain_1')]:
  cs=next(c for c in read('cases.json') if c['case']==large);extract(cs)
  a=read('data/fields/'+small+'.json');b=read('data/fields/'+large+'.json')
  comparisons={}
  for name,suffix,selector in [('total_HRR_dose','_hrr.csv',lambda k:k=='HRR'),('ground_positive_heat_dose','_devc.csv',lambda k:k.startswith('ground_') and k.endswith('_Q'))]:
   doses=[]
   for c in [small,large]:
    keys,d=devices(c,suffix);v=d[:,[i for i,k in enumerate(keys) if selector(k)]];dose=np.trapezoid(np.maximum(v,0),d[:,0],axis=0);doses.append(dose)
   comparisons[name]=dict(small_total=float(doses[0].sum()),large_total=float(doses[1].sum()),relative_L1=float(abs(doses[1]-doses[0]).sum()/max(abs(doses[1]).sum(),1)))
  rel=abs(a['post_source_fuel_kg']-b['post_source_fuel_kg'])/max(b['post_source_fuel_kg'],.1)
  # Small absolute differences for near-zero burning are explicitly treated as small.
  fuel_ok=rel<.3 or abs(a['post_source_fuel_kg']-b['post_source_fuel_kg'])<.1
  rows.append(dict(small=small,large=large,post_source_fuel_kg=[a['post_source_fuel_kg'],b['post_source_fuel_kg']],fuel_relative_difference=rel,comparisons=comparisons,screen_passed=bool(fuel_ok and comparisons['total_HRR_dose']['relative_L1']<.3 and comparisons['ground_positive_heat_dose']['relative_L1']<.3)))
 save('results/domain-comparison.json',dict(cases=rows,all_passed=all(x['screen_passed'] for x in rows),threshold='Exploratory30% on total HRR dose, ground positive-dose L1 and fuel; absolute0.1kg allowance for near-zero fuel. Not convergence or physical validation.'))
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()

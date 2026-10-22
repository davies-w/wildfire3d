"""Compare contact ignition with its source-only control and archived failed ignition."""
import json,csv,subprocess,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from contact_ignition import ROOT,read,assess

def raw_boundary(name):
 w=ROOT/'data/contact'/name;dest=ROOT/'data/contact_boundary'/name;dest.mkdir(parents=True,exist_ok=True);vals=[]
 for face in (-1,1,-2,2,-3,3):
  out=dest/f'burn_{face}.csv'
  if not out.exists():
   ans=f'{name}\n3\n1\nn\n0 90\n{face}\n1\n5\n{out}\n'
   p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=w,input=ans,text=True,capture_output=True,timeout=60,check=True);out.with_suffix('.log').write_text(p.stdout+p.stderr)
  for line in out.read_text().splitlines():
   try:v=list(map(float,line.split(',')))
   except ValueError:continue
   if len(v)==4 and math.isfinite(v[3]) and 15.99<=v[0]<=16.51 and 7.99<=v[1]<=16.01 and -.01<=v[2]<=6.01:vals.append(v[3])
 assert vals
 return dict(maximum_0_90_mean_kg_m2_s=max(vals),samples=len(vals))
def main():
 results={};fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
 for name,label in [('contact_ring20','Canopy + contact igniter'),('contact_ring20_bare','Contact igniter only (no vegetation)')]:
  r=assess(name);r['building_boundary']=raw_boundary(name);assert r['house_burning']==(r['building_boundary']['maximum_0_90_mean_kg_m2_s']>1e-12)
  h=read(name,'_hrr.csv');d=read(name,'_devc.csv');mass=sum(d[k] for k in d if k.startswith('mass '));r['first_house_burning_sample_s']=float(d['Time'][np.flatnonzero(d['house_burn_max']>1e-9)[0]]) if r['house_burning'] else None;r['peak_hrr_kw']=float(max(h['HRR']));r['energy_after_22_MJ']=float(np.trapezoid(h['HRR'][h['Time']>=22],h['Time'][h['Time']>=22])/1000);results[name]=r
  axes[0].plot(h['Time'],h['HRR']/1000,label=label);axes[1].plot(d['Time'],mass,label=label)
 for ax in axes:ax.axvline(21,color='black',ls='--',label='Igniters removed at 21 s');ax.set_xlim(0,90);ax.grid(alpha=.2);ax.legend(fontsize=9)
 axes[0].set(ylabel='Total heat release (MW)',title='Controlled ignition of the unchanged 10 m analytic canopy');axes[1].set(xlabel='Physical time (s)',ylabel='Remaining vegetation particle mass (kg)')
 fig.savefig(ROOT/'results/contact-ignition.png',dpi=150)
 results['interpretation_limits']=['Artificial hot-particle contact ignition, not a natural ground-fire exposure or ember model.','Generic fuel parameters and assigned mature-size loading remain unvalidated.','Total HRR includes building combustion. Per-class fuel-flux devices also include unfiltered wall contributions and are invalid as isolated vegetation fluxes; remaining particle mass includes water and char.','Local run90 s; original cloud scenarios180 s. Same initial90 s comparison only.']
 results['ignition_gate_passed'] = bool(results['contact_ring20']['hrr_min_40_50_kw'] >= 100 and results['contact_ring20']['wet_particle_mass_loss_40_60_kg'] > 1 and results['contact_ring20']['ignitor_count_after_22'] == 0 and results['contact_ring20']['house_burning'] and not results['contact_ring20_bare']['house_burning'] and results['contact_ring20_bare']['energy_40_60_MJ'] < .01)
 (ROOT/'results/contact-ignition.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':main()

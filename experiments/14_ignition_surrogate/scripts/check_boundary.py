"""Independent boundary-file cross-check of one positive ignition event."""
import json
import subprocess
from pathlib import Path
from benchmark import ROOT,write_json
from paths import DIST

folder=ROOT/'data/benchmark/q100_early'
output=ROOT/'data/boundary_check/boundary_check.txt'
output.parent.mkdir(parents=True,exist_ok=True)
answers='q100_early\n3\n1\nn\n1.69 2.0\n-1\n1\n1\n'+str(output)+'\n'
r=subprocess.run([str(Path(DIST)/'bin/fds2ascii')],input=answers,text=True,cwd=folder,
                 capture_output=True,timeout=60,check=True)
values=[]
for line in output.read_text().splitlines():
    try:
        row=[float(x) for x in line.split(',')]
        if len(row)==4:values.append(row[3])
    except ValueError:pass
assert values and max(values)>350,'Boundary data did not confirm ignition threshold'
write_json(ROOT/'results/boundary_check.json',{'case':'q100_early','surface':'MAIN_WALL west face x=1',
     'quantity':'WALL TEMPERATURE','time_window_s':[1.69,2.0],
     'peak_C':max(values),'threshold_C':350,'tool':'fds2ascii','confirmed':True})
print('Independent boundary check passed:',max(values),'C')

"""Independent fds2ascii evidence from the fine hot-flow case."""
import json,os,subprocess
from pathlib import Path
from study import ROOT,save

def main():
    name='fire_fine';folder=ROOT/'data/local'/f'{name}_r1'
    binary=Path(os.environ.get('FDS2ASCII',str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')))
    dest=ROOT/'data/boundary';dest.mkdir(parents=True,exist_ok=True)
    out=dest/'fire_fine_west_temperature.csv'
    answers=f'{name}\n3\n1\nn\n7.0 8.0\n-1\n1\n1\n{out}\n'
    p=subprocess.run([str(binary)],input=answers,text=True,cwd=folder,capture_output=True,timeout=60,check=True)
    (dest/'fds2ascii.log').write_text(p.stdout+p.stderr)
    values=[]
    for line in out.read_text().splitlines():
        try:
            row=list(map(float,line.split(',')))
            if len(row)==4 and abs(row[0]-4)<1e-5:values.append(row[3])
        except ValueError:pass
    if not values:raise RuntimeError('No target west-face samples')
    save(ROOT/'results/boundary_check.json',dict(case=name,surface='TARGET west face x=4 m',quantity='WALL TEMPERATURE',
        averaging_window_s=[7,8],min_C=min(values),max_C=max(values),samples=len(values),extractor=str(binary)))
    print('Boundary evidence:',min(values),max(values))

if __name__=='__main__':main()

"""Check that simplifications only change empty air, not fuel or structure geometry."""
import math,json,re
from generate import ROOT,DOMAINS,CORE,mesh_boxes,deck
from itertools import combinations
records=[]
base=deck('test','full',1000)
def scene(s):return '\n'.join(line for line in s.splitlines() if not line.startswith(('&HEAD','&MESH')))
for mode,bounds in DOMAINS.items():
    boxes=mesh_boxes(mode);v=0;n=0
    for box,dx in boxes:
        v+=math.prod(box[j+1]-box[j] for j in (0,2,4))
        for j in (0,2,4):assert (box[j+1]-box[j])/dx>=4 and abs((box[j+1]-box[j])/dx-round((box[j+1]-box[j])/dx))<1e-8
        n+=math.prod(round((box[j+1]-box[j])/dx) for j in (0,2,4))
    assert v==math.prod(bounds[j+1]-bounds[j] for j in (0,2,4))
    for (a,_),(b,_) in combinations(boxes,2):assert any(min(a[j+1],b[j+1])<=max(a[j],b[j]) for j in (0,2,4))
    assert boxes[0]==(CORE,.5)
    s=deck('test',mode,1000);assert scene(s)==scene(base)
    assert len(re.findall(r'&OBST\b',s))==1 and len(re.findall(r'&INIT\b',s))==8
    records.append(dict(mode=mode,cells=n,identical_physical_inputs=True,nonoverlapping_complete_domain=True,identical_core=True))
(ROOT/'results/design-check.json').write_text(json.dumps(records,indent=2)+'\n');print(records)

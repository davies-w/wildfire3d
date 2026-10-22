"""Parameterized reference geometry and explicit vegetation/burner controls."""
import hashlib,json,re
from pathlib import Path
import base_scene
ROOT=Path(__file__).resolve().parent

def write(case,horizon=None):
    c=dict(case);name=c['case'];duration=c.get('duration_s',30)
    source_layout=c['layout'];vegetation=c.get('vegetation',source_layout)
    s=base_scene.deck(name,source_layout,c['total_source_kw'],c.get('horizon_s',90) if horizon is None else horizon,c.get('seed',1234))
    anchors=json.loads((ROOT/'design.json').read_text())['anchors_m']
    keep={tuple(anchors[a]) for a in vegetation}
    def retain(match):
        m=re.search(r'XYZ=([^,]+),([^,]+),',match.group())
        return match.group() if m and (float(m[1]),float(m[2])) in keep else ''
    s=re.sub(r'&INIT\b.*?/',retain,s,flags=re.S)
    s=s.replace("T=30., F=1.",f'T={float(duration)}, F=1.').replace("T=31., F=0.",f'T={float(duration+1)}, F=0.')
    lines=[]
    for a in vegetation:
        x,y=anchors[a]
        for fuel in ('foliage','small roundwood','medium roundwood','large roundwood'):
            lines.append(f"&DEVC ID='crown_{a}_{fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={x-.85},{x+.85},{y-.85},{y+.85},0,3, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
    for q in ('RADIATIVE HEAT FLUX','CONVECTIVE HEAT FLUX','TOTAL HEAT FLUX'):
        lines.append(f"&BNDF QUANTITY='{q}' /")
    for plane in ('PBY=12.','PBZ=1.'):
        lines.append(f"&SLCF {plane}, QUANTITY='TEMPERATURE' /")
        lines.append(f"&SLCF {plane}, QUANTITY='VELOCITY', VECTOR=T /")
    s=s.replace('&TAIL /','\n'.join(lines)+'\n&TAIL /').replace('DT_DEVC=.5,','DT_DEVC=.5, DT_SLCF=2.,')
    (ROOT/'decks').mkdir(exist_ok=True);(ROOT/'decks'/f'{name}.fds').write_text(s)
    c.update(horizon_s=c.get('horizon_s',90) if horizon is None else horizon,seed=c.get('seed',1234),
             vegetation=vegetation,duration_s=duration,cells=55296,profile=False,variant='passive',
             deck_sha256=hashlib.sha256(s.encode()).hexdigest())
    return c

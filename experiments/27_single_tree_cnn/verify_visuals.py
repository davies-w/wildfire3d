"""Verify GIF frame coverage and extract frame24s for visual QA."""
import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).parent;o=R/'data/visual-check';o.mkdir(exist_ok=True);rows=[];thumbs=[]
for name in ['s27_test_0','s27_test_1']:
 for suffix in ['', '-3d']:
  p=R/'results/visuals'/(name+suffix+'.gif');im=Image.open(p);assert im.n_frames==46,(p,im.n_frames)
  rows.append(dict(file=str(p.relative_to(R)),frames=im.n_frames,size=list(im.size),bytes=p.stat().st_size))
  im.seek(6);frame=im.convert('RGB');frame.save(o/(name+suffix+'-24s.png'));frame.thumbnail((900,525));canvas=Image.new('RGB',(900,550),'white');canvas.paste(frame,(0,25));ImageDraw.Draw(canvas).text((10,5),name+suffix+' at24s',fill='black');thumbs.append(canvas)
sheet=Image.new('RGB',(1800,1100),'white')
for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*900,(i//2)*550))
sheet.save(o/'contact-sheet.png');(R/'results/visual-verification.json').write_text(json.dumps(rows,indent=2));print(rows)

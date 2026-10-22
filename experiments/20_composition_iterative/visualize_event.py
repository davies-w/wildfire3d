"""Render archived FDS data with Smokeview; no new simulations."""
import json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
CASE='confirm20_ACG_3200_s4321'
SRC=ROOT/'batches/confirmation20/data/cloud'/CASE
OUT=ROOT/'data/visualization';WORK=OUT/'smokeview';WORK.mkdir(parents=True,exist_ok=True)
for p in SRC.iterdir():
 if p.is_file():shutil.copy2(p,WORK/p.name)
view=(REPO/'FDS/cases/wick3/wick3.ini').read_text().replace('32.032000','24.024000').replace('-45.000000 25.000000','45.000000 25.000000')
(WORK/'view.ini').write_text(view)
frames=WORK/'frames';frames.mkdir(exist_ok=True)
times=list(range(0,41,2))+[45,50,60,75,90]
script='RENDERDIR\n frames\nUNLOADALL\nLOADINIFILE\n view.ini\n'
for suffix in ('1_1.bf','1.prt5'):script+=f'LOADFILE\n {CASE}_{suffix}\n'
script+='SETVIEWPOINT\n iso_b\n'
for i,t in enumerate(times):script+=f'SETTIMEVAL\n {t}.0\nRENDERONCE\n frame_{i:03d}\n'
script+='EXIT\n';(WORK/(CASE+'.ssf')).write_text(script)
with (OUT/'smokeview.log').open('w') as f:subprocess.run([str(REPO/'FDS/bin/smv_quiet'),'-render_overwrite','-runscript',CASE],cwd=WORK,stdout=f,stderr=subprocess.STDOUT,timeout=180)
(OUT/'times.json').write_text(json.dumps(times))
print('Rendered',len(list(frames.glob('frame_*.png'))),'frames')

from PIL import Image, ImageDraw, ImageFont
DEST=ROOT/'results/visualizations';DEST.mkdir(parents=True,exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def f(n):return ImageFont.truetype(font,n)
slides=[]
for i,t in enumerate(times):
 im=Image.new('RGB',(960,850),'#f4f7fb');d=ImageDraw.Draw(im)
 d.text((30,18),'FDS ignition event — rendered in Smokeview',font=f(30),fill='#172c43')
 d.text((30,62),'Three vegetation crowns beside the house • wind toward +x',font=f(20),fill='#415975')
 raw=Image.open(frames/f'frame_{i:03d}.png').convert('RGB')
 im.paste(raw.resize((960,720)),(0,95))
 # Cover Smokeview's bottom timestamp with an explicitly labelled panel.
 d.rectangle((0,740,960,850),fill='#f4f7fb')
 d.text((30,753),f'Simulation time: {t:02d} s',font=f(26),fill='#172c43')
 status='Before recorded house ignition' if t<9.5052105 else 'House ignition recorded at 9.51 s'
 d.text((330,755),status,font=f(23),fill='#ac3925' if t>=9.5052105 else '#415975')
 d.text((30,795),'Colours: wall temperature (°C). Dots: sampled vegetation particles.',font=f(19),fill='#415975')
 d.text((30,823),'Archived heat data; volumetric flame/smoke output was not saved.',font=f(18),fill='#415975')
 slides.append(im)
slides[8].save(DEST/'fds_ignition.png')
slides[0].save(DEST/'fds_ignition.gif',save_all=True,append_images=slides[1:],duration=[350]*25+[1800],loop=0)
print('Saved Smokeview GIF')

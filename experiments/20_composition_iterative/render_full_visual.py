"""Render smoke/HRR and synchronized three-panel comparison; no synthetic embers."""
import json,subprocess,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];CASE='confirm20_ACG_3200_s4321'
WORK=ROOT/'data/full_visual_render';WORK.mkdir(exist_ok=True);OUT=ROOT/'results/full_visual';OUT.mkdir(exist_ok=True)
for p in (ROOT/'data/full_visual').iterdir():
 if p.is_file():shutil.copy2(p,WORK/p.name)
view=(ROOT/'data/visualization/smokeview/view.ini').read_text()
(WORK/'view.ini').write_text(view)
(WORK/'frames').mkdir(exist_ok=True)
times=list(range(0,41))+list(range(42,91,2))
script='RENDERDIR\n frames\nUNLOADALL\nLOADINIFILE\n view.ini\n'
for mesh in range(1,7):
 for quantity in (1,2):script+=f'LOADFILE\n {CASE}_{mesh}_{quantity}.s3d\n'
script+=f'LOADFILE\n {CASE}_1.prt5\nSETVIEWPOINT\n iso_b\n'
for i,t in enumerate(times):script+=f'SETTIMEVAL\n {t}.0\nRENDERONCE\n smoke_{i:03d}\n'
script+='EXIT\n';(WORK/(CASE+'.ssf')).write_text(script)
with (WORK/'render.log').open('w') as log:
 subprocess.run([str(REPO/'FDS/bin/smv_quiet'),'-render_overwrite','-runscript',CASE],cwd=WORK,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def f(n):return ImageFont.truetype(font,n)
oldtimes=json.loads((ROOT/'data/visualization/times.json').read_text())
graph=Image.open(ROOT/'results/visualizations/graph_messages.png').convert('RGB')
frames=[];triples=[]
for i,t in enumerate(times):
 raw=Image.open(WORK/'frames'/f'smoke_{i:03d}.png').convert('RGB')
 im=Image.new('RGB',(960,820),'#f4f7fb');d=ImageDraw.Draw(im)
 d.text((25,14),'Smokeview: flame and smoke',font=f(30),fill='#172c43')
 d.text((25,54),f'Same A+C+G scene, local rerun • physical time {t} s',font=f(22),fill='#415975')
 im.paste(raw.resize((960,720)),(0,90));d.rectangle((0,745,960,820),fill='#f4f7fb')
 d.text((25,756),'Flames show volumetric heat release; smoke shows soot.',font=f(20),fill='#415975')
 d.text((25,788),'Vegetation particles are fixed fuel elements. This scene has no flying embers.',font=f(18),fill='#415975');frames.append(im)
 board=Image.new('RGB',(1920,740),'#f4f7fb');b=ImageDraw.Draw(board)
 b.text((20,12),f'Same scene, three views • FDS time {t} s',font=f(28),fill='#172c43')
 b.text((20,55),'Flame / smoke: local rerun',font=f(23),fill='#172c43');b.text((660,55),'Wall temperature: original cloud run',font=f(23),fill='#172c43');b.text((1300,55),'Graph: final learned state',font=f(23),fill='#172c43')
 board.paste(raw,(0,100));j=min(range(len(oldtimes)),key=lambda j:abs(oldtimes[j]-t))
 temp=Image.open(ROOT/'data/visualization/smokeview/frames'/f'frame_{j:03d}.png').convert('RGB');board.paste(temp,(640,100));board.paste(graph.resize((640,369)),(1280,125))
 b.text((20,610),'Soot + heat release, not invented flame effects.',font=f(20),fill='#415975')
 b.text((660,610),f'Closest saved frame: {oldtimes[j]} s; ignition recorded at 9.51 s.',font=f(19),fill='#415975')
 b.text((1300,610),'Static prediction — no physical clock.',font=f(20),fill='#415975')
 b.text((20,665),'No ember model in this experiment. Local and cloud solver builds may differ; the rerun is not assumed bit-for-bit identical.',font=f(23),fill='#415975')
 triples.append(board)
for name,ims in [('smoke_flame',frames),('three_views',triples)]:
 ims[16].save(OUT/(name+'.png'));ims[0].save(OUT/(name+'.gif'),save_all=True,append_images=ims[1:],duration=[160]*(len(ims)-1)+[1600],loop=0)
print('Saved',len(frames),'frames per GIF')

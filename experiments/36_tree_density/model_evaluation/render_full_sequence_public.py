"""Use the original gallery shell and controls with full-sequence rendered figures."""
from pathlib import Path
import json,html,math,re,shutil
R=Path(__file__).resolve().parents[1];D=R/'data/full-sequence';P=R/'data/full-sequence-public'
s=json.loads((D/'scores.json').read_text());meta=json.loads((R/'data/pair-sequence/rotation0/schema.json').read_text())['cases']
original=(R/'data/pair-gallery/index.html').read_text()
info=original[original.index('function info(d)'):original.index('function chart(d,f)')]
colors=['#159447','#9854bc','#1878c8'];titles=['Water · kg','Dry fuel · kg','Fuel gas · kg/s','Heating index · K']
for m in s['models']:
 records=json.loads((D/(m['slug']+'.json')).read_text())['records'];pages=[]
 for start in range(0,len(records),3):
  rows=[]
  for q in records[start:start+3]:
   case=meta[q['id']];k=case['physical_key'];n=len(q['truth'][0]);data=dict(index=q['id'],case=case['case'],fold=(0 if m['slug'].startswith('stride') else q['fold'] if m['slug']=='dense' else q['fold']//2),height=k[0],loading=k[2],wind=k[3],angle=k[4],water=q['truth'][0][0],fuel=q['truth'][0][1]);charts=[]
   for f in range(4):
    if f>=n:charts.append('<div class="chart"><h3>'+titles[f]+'</h3><p>Not predicted</p></div>');continue
    threshold=[.001,.01,.00001,.1][f]
    def T(v):return math.copysign(math.log10(1+abs(v)/threshold),v)
    arrays=[q['truth'],q['baseline'],q['prediction']];allv=[T(v[f]) for a in arrays for v in a];lo=min(allv);hi=max(allv);pad=(hi-lo or 1)*.08;lo-=pad;hi+=pad
    out='<div class="chart"><h3>'+titles[f]+'</h3><svg viewBox="0 0 280 175">'
    for j in range(5):
     z=lo+(hi-lo)*j/4;v=math.copysign(threshold*(10**abs(z)-1),z);out+=f'<text x="47" y="{142-j*30}" text-anchor="end" font-size="8" fill="#627082">{v:.3g}</text>'
    for t in [0,60,120,180]:out+=f'<text x="{51+t/180*220}" y="154" text-anchor="middle" font-size="9" fill="#627082">{t}</text>'
    out+='<text x="161" y="169" text-anchor="middle" font-size="9" fill="#627082">Target time (s)</text>'
    for series,a in enumerate(arrays):
     path=' '.join(('M' if j==0 else 'L')+f'{51+q["time"][j]/180*220:.6f},{139-(T(v[f])-lo)/(hi-lo)*120:.6f}' for j,v in enumerate(a));out+=f'<path data-series="{series}" d="{path}" fill="none" stroke="{colors[series]}" stroke-width=".9"/>'
    charts.append(out+'</svg></div>')
   rows.append(dict(info=data,charts=''.join(charts)))
  pages.append(rows)
 shell=original[:original.index('<script>')]
 shell=shell.replace('Stride-one · plain and gated',html.escape(m['name'])+' · full sequence')
 shell=re.sub(r'<p class="desc">.*?</p>','<p class="desc">Continuous full-sequence predictions initialized once at t=0; no later truth resets. No change uses the preceding actual simulation state. Symmetric-log axes retain zero and negatives. Click a legend to toggle its line; axes remain fixed.</p>',shell)
 shell=re.sub(r'<div id="legend">.*?</div>', '<div id="legend">'+''.join(f'<button data-series="{i}" aria-pressed="{str(i!=1).lower()}" style="color:{colors[i]}">{label}</button>' for i,label in enumerate(['Simulation','No change',html.escape(m['name'])]))+'</div>',shell)
 script='const total='+str(len(records))+',pages=Math.ceil(total/3),visible=[true,false,true],content='+json.dumps(pages,separators=(',',':'))+';let page=Math.max(0,Math.min(pages-1,Number(location.hash.slice(1))||0));const fmt=x=>Number(x.toPrecision(3)).toString();'+info+'''
function apply(){document.querySelectorAll('path[data-series]').forEach(p=>p.style.display=visible[+p.dataset.series]?'':'none')}
function render(){document.getElementById('count').textContent=`${page*3+1}–${Math.min(page*3+3,total)} of ${total}`;document.getElementById('back').disabled=page===0;document.getElementById('next').disabled=page===pages-1;document.getElementById('rows').innerHTML=content[page].map(d=>'<section class="row"><aside class="info">'+info(d.info)+'</aside>'+d.charts+'</section>').join('');apply()}
function load(n){page=Math.max(0,Math.min(pages-1,n));history.replaceState(null,'','#'+page);render()}
document.getElementById('back').onclick=()=>load(page-1);document.getElementById('next').onclick=()=>load(page+1);document.querySelectorAll('#legend button').forEach(b=>b.onclick=()=>{let k=+b.dataset.series;visible[k]=!visible[k];b.setAttribute('aria-pressed',String(visible[k]));apply()});load(page);
'''
 shell=shell.replace('Single split, not ten-fold aggregate.','Model-specific held-out population; see full-sequence scorecard.')
 (P/(m['slug']+'.html')).write_text(shell+'<script>'+script+'</script></body></html>')
print('Restored original gallery shell, rubric, symlog axes, legends and pagination for seven models')

for name in ["index.html","scores.json","historical-scores.json"]:shutil.copyfile(D/name,P/name)

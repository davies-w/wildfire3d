"""Add physical-space integrated error badges without changing existing plot paths."""
from pathlib import Path
import json,re,hashlib,argparse
import numpy as np
R=Path(__file__).resolve().parents[1]
D=R/'data/stride-integral';D.mkdir(exist_ok=True)
def area(t,d):
    a=np.abs(d[:-1]);b=np.abs(d[1:]);cross=d[:-1]*d[1:]<0
    avg=(a+b)/2
    np.divide(a*a+b*b,2*(a+b),out=avg,where=cross)
    return ((np.diff(t)[:,None])*avg).sum(0)
# Exact integral of absolute piecewise-linear differences, including zero crossings.
assert np.allclose(area(np.array([0.,2.]),np.array([[1.],[-1.]])),[1.])
assert np.allclose(area(np.array([0.,2.,5.]),np.array([[2.],[2.],[2.]])),[10.])
def build():
    records=json.loads((R/'data/full-sequence/stridegated.json').read_text())['records']
    seq=np.load(R/'data/learning/sequences.npz');out=[]
    for q in records:
        t=np.array(q['time']);truth=np.array(q['truth']);pred=np.array(q['prediction']);span=np.ptp(truth,axis=0);duration=t[-1]-t[0]
        assert np.all(np.diff(t)>0) and np.all(span>0) and np.isfinite(pred).all()
        integral=area(t,pred-truth);percent=100*integral/(duration*span)
        # Independent numerical integration check using a dense partition of every interval.
        dense=np.linspace(0,1,1001)
        approx=sum((t[j+1]-t[j])*np.trapezoid(abs((pred-truth)[j,None,:]*(1-dense[:,None])+(pred-truth)[j+1,None,:]*dense[:,None]),dense,axis=0) for j in range(len(t)-1))
        assert np.allclose(integral,approx,rtol=2e-5,atol=1e-8)
        out.append(dict(id=q['id'],configuration=str(seq['configuration'][q['id']]),duration_seconds=float(duration),simulation_range=span.tolist(),absolute_error_integral=integral.tolist(),percent=percent.tolist()))
    conf=np.array([q['configuration'] for q in out]);values=np.array([q['percent'] for q in out]);agg=np.array([values[conf==k].mean(0) for k in np.unique(conf)]).mean(0)
    scores=dict(model='Stride-one gated · split 0',scope='Entire saved sequence including initial point; 90 actual intervals.',formula='100 * integral(abs(prediction(t)-simulation(t))) / ((t_end-t_start)*(max(simulation)-min(simulation)))',interpolation='Exact absolute integral of piecewise-linear physical values; split at every error zero crossing. Not area in symmetric-log screen coordinates.',aggregation='Mean replicas within each configuration, then equal configuration mean.',features=['Water kg','Dry fuel kg','Gas kg/s','Heating index K'],histories=len(out),configurations=len(np.unique(conf)),aggregate_percent=agg.tolist(),records=out)
    (D/'integral-scores.json').write_text(json.dumps(scores,indent=2)+'\n')
    old=(R/'data/full-sequence-public/stridegated.html').read_text();prefix,rest=old.split(',content=',1);payload,tail=rest.split(';let page=',1);pages=json.loads(payload);byid={q['id']:q for q in out}
    for page in pages:
        for row in page:
            vals=iter(byid[row['info']['index']]['percent'])
            row['charts']=re.sub(r'<h3>(.*?)</h3>',lambda m:'<h3>'+m[1]+' <span class="integral-badge" title="Whole-sequence integral of absolute physical error / (duration × simulation range)">'+f'{next(vals):.2f}%</span></h3>',row['charts'])
    new=prefix+',content='+json.dumps(pages,separators=(',',':'))+';let page='+tail
    new=new.replace('</style>','.integral-badge{display:inline-block;font-size:10px;font-weight:600;padding:1px 4px;border:1px solid #b7c9da;border-radius:4px;background:#edf4fb;white-space:nowrap}</style>',1)
    new=new.replace('Click a legend to toggle its line; axes remain fixed.','Click a legend to toggle its line; axes remain fixed. Boxes: whole-sequence integrated absolute error ÷ (duration × simulation range), in physical units; not log-screen area.',1)
    # Every existing trajectory, rubric and all controls remain identical.
    assert re.findall(r'<path[^>]*>',old)==re.findall(r'<path[^>]*>',new)
    assert new.count('class=\\"integral-badge\\"')==208*4
    (D/'stridegated.html').write_text(new)
    card=(R/'data/full-sequence-public/index.html').read_text()
    insertions=[]
    def section(m):
        text=m[0]
        if 'Stride-one gated' not in text:return text
        text=text.replace('colspan="2" class="group g6"','colspan="3" class="group g6"',1)
        header='<th class="g6" title="Same whole-sequence metric as the gallery boxes; not restricted to this section’s phase.">Integral error ↓<br>Whole sequence</th>'
        text=text.replace('</tr></thead>',header+'</tr></thead>',1)
        i=iter(agg)
        text=re.sub(r'<tr><th>(?:Water \(kg\)|Dry fuel \(kg\)|Gas release \(kg/s\)|Heating index \(K\)).*?</tr>',lambda row:row[0][:-5]+f'<td class="integral-score">{next(i):.2f}%</td></tr>',text)
        note='<p class="note integral-note">New integral column: whole-sequence physical-space absolute error area ÷ (duration × each simulation’s max–min range). Same values as gallery boxes, averaged over replicas then equally over configurations; repeated here for reference, not phase-restricted.</p>'
        return text.replace('</section>',note+'</section>')
    updated=re.sub(r'<section>.*?</section>',section,card,flags=re.S)
    assert updated.count('class="integral-score"')==16
    restored=re.sub(r'<th class="g6" title="Same whole-sequence.*?</th>','',updated)
    restored=re.sub(r'<td class="integral-score">.*?</td>','',restored)
    restored=re.sub(r'<p class="note integral-note">.*?</p>','',restored)
    restored=restored.replace('colspan="3" class="group g6"','colspan="2" class="group g6"')
    assert restored==card,'Existing scorecard changed'
    (D/'index.html').write_text(updated)
    print(json.dumps({'aggregate_percent':agg.tolist(),'badges':832,'all_existing_paths_unchanged':True,'existing_scorecard_preserved':True}))
if __name__=='__main__':build()

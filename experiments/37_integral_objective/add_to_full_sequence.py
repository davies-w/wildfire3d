"""Append verified model columns and a gallery; never replace prior cells or curves."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parent;D=R/'data/scorecard-addition'
old=(D/'full-sequence__index.html').read_text();source=(R/'data/public/index.html').read_text()
sections=re.findall(r'<section>.*?</section>',source,re.S)
def add(m):
 s=m[0];title=re.search(r'<h2>.*?</h2>',s)[0];ref=next(x for x in sections if title in x)
 group=re.search(r'<th colspan="3" class="group g7">.*?</th>',ref)[0]
 heads=''.join(re.findall(r'<th class="g7">.*?</th>',ref))
 cells=re.findall(r'<td class="new-integral-model">.*?</td>',ref);assert len(cells)==12
 s=s.replace('</tr><tr>',group+'</tr><tr>',1).replace('</tr></thead>',heads+'</tr></thead>',1)
 rows=iter([ ''.join(cells[i:i+3]) for i in range(0,12,3)])
 return re.sub(r'<tr><th>(?:Water \(kg\)|Dry fuel \(kg\)|Gas release \(kg/s\)|Heating index \(K\)).*?</tr>',lambda x:x[0][:-5]+next(rows)+'</tr>',s)
new=re.sub(r'<section>.*?</section>',add,old,flags=re.S)
assert new.count('class="new-integral-model"')==48
assert re.findall(r'<td.*?</td>',re.sub(r'<td class="new-integral-model">.*?</td>','',new),re.S)==re.findall(r'<td.*?</td>',old,re.S)
new=new.replace('</style>','.g7{background:#e5f5e8}</style>',1)
note='<p><strong>Integral-loss gated · split 0:</strong> same 208 test histories; new range-normalized integral objective and validation selection, with equal configuration weighting. New columns show two decimals. Integral error is the same whole-sequence value in every phase table, matching graph boxes; the other two columns remain phase-specific. Previously examined split, exploratory comparison. <a href="integral-gated.html">Additional full-sequence visual comparisons</a> · <a href="../integral37/integral-comparison.json">Exact integral values</a></p>'
new=new.replace('</h1>','</h1>'+note,1);(D/'index.html').write_text(new)
gallery=(D/'integral37__gated.html').read_bytes();(D/'integral-gated.html').write_bytes(gallery)
menu=(D/'full-sequence__gallery.html').read_text();menu=menu.replace('</main>','<p><a href="integral-gated.html">Integral-loss gated · split 0</a> — 208 held-out histories; established three-row, four-chart layout with line toggles, rubric and integral boxes. This gallery uses symlog axes.</p></main>');(D/'gallery.html').write_text(menu)
reference=(R.parent/'36_tree_density/data/stride-integral/stridegated.html').read_text();g=gallery.decode()
assert re.findall(r'<style>.*?</style>',g,re.S)==re.findall(r'<style>.*?</style>',reference,re.S)
assert g[g.index('function info(d)'):]==reference[reference.index('function info(d)'):]
pages=json.loads(g.split(',content=',1)[1].split(';let page=',1)[0]);assert len(pages)==70 and sum(map(len,pages))==208
assert all(len(p)==3 for p in pages[:-1]) and all(row['charts'].count('class="chart"')==4 for p in pages for row in p)
proof=dict(passed=True,prior_cells_preserved=True,existing_gallery_pages_untouched=True,style_controls_rubric_preserved=True,histories=208,pages=70,files={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['index.html','gallery.html','integral-gated.html']})
(R/'results/scorecard-addition-build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

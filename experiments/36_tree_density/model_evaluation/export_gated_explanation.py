"""Render the exact user-requested conversation explanation; publish two allowed paths."""
from pathlib import Path
import argparse, hashlib, html, json, re
from markdown_it import MarkdownIt
R=Path(__file__).resolve().parents[1]
SOURCE=R/'documentation/gated-gru-explanation.md'
OUT=R/'data/gated-gru-explanation/index.html'
def build():
    text=SOURCE.read_text(); math=[]
    def protect(m):
        math.append(m.group()); return f'MATHPLACEHOLDER{len(math)-1}END'
    text=re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)',protect,text,flags=re.S)
    text=re.sub(r'^\*\*(\d+\. .+)\*\*$',r'## \1',text,flags=re.M)
    body=MarkdownIt('commonmark',{'html':False}).enable('table').render(text)
    for i,eq in enumerate(math):body=body.replace(f'MATHPLACEHOLDER{i}END',html.escape(eq))
    body=re.sub(r'<a href="(/Users/[^\"]+)">(.*?)</a>',lambda m:'<span class="source-ref">'+m[2]+' <small>(local audit file)</small><code>'+html.escape(html.unescape(m[1]))+'</code></span>',body)
    body=body.replace('<table>','<div class="table-wrap"><table>').replace('</table>','</table></div>')
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gated GRU: architecture, training and prediction</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#182637;font:17px/1.65 system-ui,sans-serif}main{max-width:1000px;margin:32px auto;padding:36px 42px;background:white;border:1px solid #dce3eb;border-radius:14px}h1{font-size:36px;line-height:1.2}h2{font-size:25px;line-height:1.3;margin-top:48px;padding-top:18px;border-top:1px solid #dce3eb}a{color:#205bb0}.meta,small{color:#526173}.meta{font-size:14px}table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:10px 14px;text-align:left;border:1px solid #dce3eb;vertical-align:top}th{background:#edf3fa}.table-wrap{overflow-x:auto;margin:22px 0}pre{overflow:auto;padding:18px;background:#f3f5f8;border-radius:8px}code{font-size:.87em}blockquote{border-left:4px solid #2870b8;padding-left:18px;margin-left:0}.source-ref code{display:block;overflow-wrap:anywhere;font-size:11px;color:#526173}.source-ref small{font-size:12px}mjx-container[display="true"]{overflow-x:auto;overflow-y:hidden;padding:8px 0}@media(max-width:650px){main{margin:0;padding:24px 18px;border:0;border-radius:0}h1{font-size:29px}}@media print{body{background:white}main{border:0;margin:0;max-width:none;padding:0}}
</style><script>window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]},options:{enableMenu:false}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script></head><body><main><nav><a href="../index.html">← All reports</a></nav><h1>Gated GRU: architecture, training and prediction</h1><p class="meta">Export of the detailed conversation audit, 28 October 2026. Scope: published “Stride-one gated · split 0”. Original explanation preserved; local evidence references identify files in the research workspace and are not public downloads.</p><article>'''+body+'</article></main></body></html>'
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(page)
    assert page.count('<h2>')==12
    assert 'MATHPLACEHOLDER' not in page
    assert '<a href="/Users/' not in page
    print(json.dumps({'html':str(OUT),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'sections':12,'equations':len(math)}))
def publish():
    from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
    api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
    path='gated-gru-explanation/index.html'
    assert path not in api.list_repo_files(repo,repo_type='space',revision=rev),'Already published; inspect before retry'
    old=Path(hf_hub_download(repo,'index.html',repo_type='space',revision=rev)).read_text()
    card='<a class="card" href="gated-gru-explanation/index.html" target="_blank" rel="noopener noreferrer"><span class="tag">Model explanation</span><h2>How the gated GRU works →</h2><p>The detailed audit of its four-sample input, recurrent memory, output gates, training curriculum and full-sequence predictions.</p></a>'
    marker='<div class="cards">';assert old.count(marker)==1
    new=old.replace(marker,marker+card,1);assert new.replace(card,'',1)==old
    commit=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=path,path_or_fileobj=str(OUT)),CommitOperationAdd(path_in_repo='index.html',path_or_fileobj=new.encode())],commit_message='Add detailed gated GRU explanation as first index card')
    assert Path(hf_hub_download(repo,path,repo_type='space',revision=commit.oid)).read_bytes()==OUT.read_bytes()
    assert Path(hf_hub_download(repo,'index.html',repo_type='space',revision=commit.oid)).read_text()==new
    proof={'repo':repo,'parent':rev,'commit':commit.oid,'changed_paths':[path,'index.html'],'first_card':path,'all_existing_index_bytes_preserved':True,'readback_exact':True,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'html_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}
    (R/'results/gated-gru-explanation-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args()
    publish() if a.publish else build()

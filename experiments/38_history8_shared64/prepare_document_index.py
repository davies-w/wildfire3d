"""Prepare an additive root-index card against a pinned public revision."""
from pathlib import Path
import json
from huggingface_hub import HfApi,hf_hub_download
R=Path(__file__).resolve().parent;D=R/'data/document-index';D.mkdir(exist_ok=True)
rev=HfApi().repo_info('wdavies/fire-reports',repo_type='space').sha
old=Path(hf_hub_download('wdavies/fire-reports','index.html',repo_type='space',revision=rev)).read_text()
assert 'history38/index.html' not in old
card='<a class="card" href="history38/index.html" target="_blank" rel="noopener noreferrer"><span class="tag">Experiment 38 · completed</span><h2>Longer history and a wider gated GRU →</h2><p>Eight state samples, GRU64 and shared SiLU layer: matched rotation-0 results, final learning curve, checkpoint recovery and limitations.</p></a>'
new=old.replace('<div class="cards">','<div class="cards">'+card,1);assert new.replace(card,'',1)==old
(D/'parent-index.html').write_text(old);(D/'index.html').write_text(new);(D/'parent.json').write_text(json.dumps({'revision':rev},indent=2))

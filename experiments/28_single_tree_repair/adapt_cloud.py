from pathlib import Path
R=Path(__file__).parent;P=R.parent/'27_single_tree_cnn'
s=(P/'cloud.py').read_text().replace("'s27-", "'s28-").replace('single27/', 'single28/').replace("['pilot','domain','train','validation','test']", "['test']")
s=s.replace("def read(p):return json.loads((ROOT/p).read_text())", "LEDGER=ROOT.parent/'27_single_tree_cnn'\ndef path(p):return (LEDGER if p=='budget.json' else ROOT)/p\ndef read(p):return json.loads(path(p).read_text())")
s=s.replace("def save(p,obj):(ROOT/p).write_text", "def save(p,obj):path(p).write_text").replace("(ROOT/'budget.json').exists()", "(LEDGER/'budget.json').exists()").replace("ROOT/'data/budget.lock'", "LEDGER/'data/budget.lock'")
a=s.index(" checks=read('results/preflight.json')");b=s.index(" if g['phase']=='test':",a)
s=s[:a]+" assert read('results/physical-screen.json')['pass_all']\n assert read('results/full-validation.json')['pass_all']\n assert read('results/native-preflight.json')['passed']\n"+s[b:]
(R/'cloud.py').write_text(s)
print('Cloud adapter uses parent central budget; launches require validation and native preflight')

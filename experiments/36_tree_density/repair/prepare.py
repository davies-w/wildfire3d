from pathlib import Path
import hashlib,shutil,json
R=Path(__file__).resolve().parent
source=R.parents[1]/'16_code_profiling/data/binary/fds'
expected='70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692'
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
out=R.parent/'data/restore-context';out.mkdir(exist_ok=True)
shutil.copyfile(source,out/'fds');(out/'fds').chmod(0o755)
shutil.copyfile(R/'Dockerfile',out/'Dockerfile')
(R.parent/'results/restore-preflight.json').write_text(json.dumps(dict(passed=True,exact_prior_solver_binary_sha256=expected,no_build_or_solve=True),indent=2)+'\n')

"""Verify live report bytes after removing identified hosting-only additions."""
from pathlib import Path
import hashlib,json,re,requests
R=Path(__file__).resolve().parent
url='https://wdavies-fire-reports.static.hf.space/stacked42/index.html'
r=requests.get(url,timeout=45);r.raise_for_status();text=r.content.decode('utf-8')
text=re.sub(r'<script>window\.huggingface=.*?</script>','',text)
text=re.sub(r'<meta (?:property="og:(?:title|image)"|name="twitter:(?:card|image)")[^>]*>','',text)
assert text==(R/'data/report-public/stacked42/index.html').read_text()
(R/'results03/live-report-check.json').write_text(json.dumps(dict(passed=True,url=url,http_status=r.status_code,hosting_script_and_social_metadata_removed=True,normalized_sha256=hashlib.sha256(text.encode()).hexdigest()),indent=2)+'\n')

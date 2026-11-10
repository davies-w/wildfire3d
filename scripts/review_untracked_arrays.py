"""Review numerical/raw arrays from a completed tracking audit, without deletion."""
from pathlib import Path
import csv,json,argparse,hashlib
import dvc_hf as hf
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--include-prefix',action='append',default=[]);ap.add_argument('--suffixes',nargs='+',default=['.sf','.bf','.prt5','.pt','.npz']);a=ap.parse_args();rows=[];excluded=[]
 for row in csv.DictReader(a.audit.open()):
  if a.include_prefix and not any(row['path'].startswith(x) for x in a.include_prefix):continue
  if Path(row['path']).suffix not in set(a.suffixes):continue
  p=ROOT/row['path'];reason=None
  if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(ROOT):reason='Missing, symlink or outside repository'
  elif p.stat().st_size!=int(row['bytes']):reason='Size changed since tracking audit'
  else:reason=hf.approve(p)
  if reason:excluded.append({'path':row['path'],'reason':reason});continue
  md,sha=hf.digest(p);rows.append({'path':row['path'],'bytes':p.stat().st_size,'md5':md,'sha256':sha,'public_policy_passed':True,'exclusion_reason':None})
 result={'source_audit_sha256':hashlib.sha256(a.audit.read_bytes()).hexdigest(),'files':rows,'excluded':excluded};a.report.write_text(json.dumps(result,indent=2)+'\n');print('Reviewed',len(rows),'excluded',len(excluded),flush=True)
 if excluded:raise RuntimeError('Excluded candidates require explicit reconciliation; see private report')
if __name__=='__main__':main()

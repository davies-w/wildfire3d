"""Inventory and hash-check local split raw archives without moving or deleting data.

Write the report to private storage: it contains local source paths. Missing parts
are reported explicitly and are never counted as complete archives.
"""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root):
    archives = []
    for manifest_path in sorted(root.rglob('archive-manifest.json')):
        # Migration bookkeeping and pointers are not source manifests.
        try:
            manifest = json.loads(manifest_path.read_text())
        except (ValueError, OSError) as e:
            archives.append(dict(manifest=str(manifest_path), passed=False, error=str(e)))
            continue
        if not isinstance(manifest, dict) or 'parts' not in manifest:
            continue
        row = dict(manifest=str(manifest_path), passed=False, parts=[], errors=[])
        total = 0
        for part in manifest['parts']:
            name = part['name']
            if Path(name).name != name:
                row['errors'].append('Nonlocal part name'); continue
            path = manifest_path.parent/name
            if not path.is_file() or path.is_symlink():
                row['errors'].append('Missing or symlink part: '+name); continue
            st = path.stat()
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = path.stat()
            valid = (digest == part['sha256'] and st.st_size == part['bytes'] and
                     (st.st_size, st.st_mtime_ns) == (after.st_size, after.st_mtime_ns))
            row['parts'].append(dict(path=str(path), bytes=st.st_size, sha256=digest, passed=valid))
            total += st.st_size
            if not valid: row['errors'].append('Part hash/size mismatch: '+name)
        row['bytes'] = total
        row['passed'] = bool(manifest.get('complete') and manifest['parts'] and
                             not row['errors'] and total == manifest['bytes'])
        if not row['passed'] and not row['errors']:
            row['errors'].append('Incomplete manifest or inconsistent total')
        archives.append(row)
    return dict(archives=archives, complete_archives=sum(x['passed'] for x in archives),
                complete_bytes=sum(x.get('bytes',0) for x in archives if x['passed']),
                incomplete_archives=sum(not x['passed'] for x in archives),
                remote_backup_verified=False, local_copies_removed=False)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    result=audit(a.root.resolve());a.report.parent.mkdir(parents=True,exist_ok=True)
    tmp=a.report.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(a.report)
    print(json.dumps({k:v for k,v in result.items() if k!='archives'}),flush=True)

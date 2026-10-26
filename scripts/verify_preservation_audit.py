"""Recheck the original 91-file inventory without compute, network or mutations.

Checks current bytes, claimed Git preservation, locked/mirrored archive members,
and the adopted experiment29 outputs. Pending entries remain pending. This is
storage verification, not validation of simulation completeness or physics.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import subprocess
import tarfile
import yaml


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'md5').hexdigest()


def verify(root):
    report = json.loads((root / 'docs/preservation-audit-2026-10-25.json').read_text())
    mirror = root / 'FDS/hf_dvc_mirror/files/md5'
    cache = root / '.dvc/cache/files/md5'
    outputs = {}
    names = subprocess.check_output(['git', 'ls-files', '*dvc.lock'], cwd=root, text=True).splitlines()
    for name in names:
        lock = root / name
        pipeline = yaml.safe_load(lock.with_name('dvc.yaml').read_text())
        for stage_name, stage in yaml.safe_load(lock.read_text()).get('stages', {}).items():
            definition = pipeline.get('stages', {}).get(stage_name.split('@')[0], {})
            definition = definition.get('do', definition)
            base = Path(os.path.abspath(lock.parent / definition.get('wdir', '.')))
            for output in stage.get('outs', []):
                outputs[base / output['path']] = output['md5']
    checked_objects = set()

    def mirrored(md5):
        if md5 not in checked_objects:
            obj = mirror / md5[:2] / md5[2:]
            assert obj.is_file() and digest(obj) == md5.removesuffix('.dir'), str(obj)
            checked_objects.add(md5)

    def recorded(path):
        if path in outputs:
            md5 = outputs[path]
        else:
            parents = [p for p in outputs if p in path.parents and outputs[p].endswith('.dir')]
            assert parents, f'No locked output contains {path}'
            parent = max(parents, key=lambda p: len(p.parts))
            directory = outputs[parent]
            mirrored(directory)
            obj = cache / directory[:2] / directory[2:]
            entries = json.loads(obj.read_text())
            md5 = next(e['md5'] for e in entries if e['relpath'] == str(path.relative_to(parent)))
        return md5

    counts = collections.Counter()
    for entry in report['entries']:
        path = root / entry['path']
        assert digest(path) == entry['md5'], f'Changed since audit: {path}'
        status = entry['resolution']
        counts[status] += 1
        if status == 'already_preserved_in_git_text_report':
            current = subprocess.check_output(['git', 'hash-object', str(path)], cwd=root, text=True).strip()
            committed = subprocess.check_output(['git', 'rev-parse', 'HEAD:' + entry['path']], cwd=root, text=True).strip()
            assert current == committed, entry['path']
        elif status == 'adopted_existing_evaluate_stage_and_verified_local_mirror':
            assert recorded(path) == entry['md5']
            mirrored(entry['md5'])
        elif status == 'byte_identical_member_of_locked_and_mirrored_output_tar':
            evidence = entry['archive_evidence']
            archive = root / evidence['duplicate_of']
            md5 = recorded(archive)
            assert digest(archive) == md5
            mirrored(md5)
            with tarfile.open(archive) as tar:
                with tar.extractfile(evidence['member']) as stream:
                    assert hashlib.file_digest(stream, 'md5').hexdigest() == entry['md5']
        elif status == 'all_archive_file_contents_identical_to_locked_and_mirrored_cloud_outputs':
            cloud = path.parent.parent / 'cloud'
            count = 0
            with tarfile.open(path) as tar:
                for member in tar:
                    if not member.isfile():
                        continue
                    md5 = recorded(cloud / member.name)
                    with tar.extractfile(member) as stream:
                        assert hashlib.file_digest(stream, 'md5').hexdigest() == md5
                    mirrored(md5)
                    count += 1
            assert count == entry['archive_evidence']['members']
    print(json.dumps(dict(verified_current_files=len(report['entries']), resolution_counts=counts,
                          verified_mirror_objects=len(checked_objects)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    verify(parser.parse_args().root.resolve())

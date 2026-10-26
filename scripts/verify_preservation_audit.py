"""Verify the original 91-file inventory against Git and DVC storage.

No network, compute, stage execution or mutations unless --refresh-report is
requested. Adopting old bytes proves storage integrity, not scientific validity
or a tested replay/resume of historical runs.
"""
from pathlib import Path
import argparse
import collections
import functools
import hashlib
import json
import os
import subprocess
import yaml


@functools.lru_cache(maxsize=None)
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'md5').hexdigest()


def verify(root, refresh=False):
    report_path = root / 'docs/preservation-audit-2026-10-25.json'
    report = json.loads(report_path.read_text())
    cache = root / '.dvc/cache/files/md5'
    mirror = root / 'FDS/hf_dvc_mirror/files/md5'
    # Include new pointer files even before their Git commit.
    names = set(subprocess.check_output(
        ['git', 'ls-files', '*dvc.lock', '*.dvc'], cwd=root, text=True).splitlines())
    names.update('experiments/21_local_components/' + n + '.dvc' for n in
                 ['sampling-price-source.html', 'spot-price-source.html'])
    outputs = {}
    for name in sorted(names):
        path = root / name
        document = yaml.safe_load(path.read_text())
        is_pointer = name.endswith('.dvc')
        pipeline = {} if is_pointer else yaml.safe_load(path.with_name('dvc.yaml').read_text())
        stages = [('', document)] if is_pointer else document.get('stages', {}).items()
        for stage_name, stage in stages:
            definition = pipeline.get('stages', {}).get(stage_name.split('@')[0], {})
            definition = definition.get('do', definition)
            base = Path(os.path.abspath(path.parent / definition.get('wdir', '.')))
            configs = {}
            for kind in ['outs', 'metrics', 'plots']:
                for value in definition.get(kind, []):
                    if isinstance(value, str):
                        configs[value] = {}
                    else:
                        configs.update(value)
            for output in stage.get('outs', []):
                target = base / output['path']
                outputs[target] = dict(md5=output['md5'], record=name, stage=stage_name,
                                       cached=configs.get(output['path'], {}).get('cache', True))
    checked = set()

    def stored(md5):
        if md5 not in checked:
            for base in [cache, mirror]:
                obj = base / md5[:2] / md5[2:]
                assert obj.is_file() and digest(obj) == md5.removesuffix('.dir'), str(obj)
            checked.add(md5)

    def recorded(path):
        if path in outputs:
            result = dict(outputs[path])
        else:
            parents = [p for p in outputs if p in path.parents and outputs[p]['md5'].endswith('.dir')]
            assert parents, f'No DVC output contains {path}'
            parent = max(parents, key=lambda p: len(p.parts))
            result = dict(outputs[parent])
            directory = result['md5']
            stored(directory)
            entries = json.loads((cache / directory[:2] / directory[2:]).read_text())
            result['directory_md5'] = directory
            result['member'] = str(path.relative_to(parent))
            result['md5'] = next(e['md5'] for e in entries if e['relpath'] == result['member'])
        assert result['cached'], f'Output caching disabled: {path}'
        return result

    counts = collections.Counter()
    for entry in report['entries']:
        path = root / entry['path']
        assert digest(path) == entry['md5'], f'Changed since initial audit: {path}'
        if entry['git_tracked']:
            current = subprocess.check_output(['git', 'hash-object', str(path)], cwd=root, text=True).strip()
            committed = subprocess.check_output(['git', 'rev-parse', 'HEAD:' + entry['path']], cwd=root, text=True).strip()
            assert current == committed, entry['path']
            resolution = 'preserved_in_git_text_report'
            evidence = dict(git_blob=committed)
        else:
            evidence = recorded(path)
            assert evidence['md5'] == entry['md5'], entry['path']
            stored(evidence['md5'])
            resolution = ('preserved_external_input_pointer_cache_and_mirror' if evidence['record'].endswith('.dvc')
                          else 'preserved_stage_output_cache_and_mirror')
        counts[resolution] += 1
        if refresh:
            entry['resolution'] = resolution
            entry['verified_storage'] = evidence
            for key in ['cache_present', 'mirror_present', 'lock_matches', 'declared_stage_output']:
                if key in entry:
                    entry.setdefault('initial_observation', {})[key] = entry.pop(key)
            entry.pop('limitation', None)
    summary = dict(verified_current_files=len(report['entries']), resolution_counts=dict(counts),
                   verified_cache_and_mirror_objects=len(checked), result='passed')
    assert len(report['entries']) == 91
    assert counts['preserved_in_git_text_report'] == 4
    assert counts['preserved_stage_output_cache_and_mirror'] == 85
    assert counts['preserved_external_input_pointer_cache_and_mirror'] == 2
    if refresh:
        report['resolution_counts'] = dict(counts)
        report['verification'] = dict(command='.venv/bin/python scripts/verify_preservation_audit.py', **summary)
        report['pending'] = ['Experiment36 remains under its separate supervisor; its mutable outputs and budget were not adopted or modified by this task.']
        report['completed'].append('All 91 original entries reconciled: four Git text reports and 87 files whose exact bytes match DVC records, local cache objects and local mirror objects. Downloaded archive packaging and extracted duplicates are now tracked directly as stage outputs too.')
        report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--refresh-report', action='store_true')
    args = parser.parse_args()
    verify(args.root.resolve(), args.refresh_report)

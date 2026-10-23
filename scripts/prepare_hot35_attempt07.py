"""Reproduce offline inputs/package for independent-time HOT experiment; NEVER submit.
The experiment's tracked source files are authoritative; prepare_pilot.py generates
its bounded cloud workflow. Paid submission is a separate explicit DVC stage.
"""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
for stage in ['prepare_labels','validate','package']:
 subprocess.run([str(ROOT/'.venv/bin/dvc'),'repro','--single-item','experiments/35_surrogate_diagnostics/attempt07/dvc.yaml:'+stage],cwd=ROOT,check=True)

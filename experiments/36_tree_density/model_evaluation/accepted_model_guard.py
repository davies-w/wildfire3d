"""Require completed accepted pilot evidence before any final-test target loading."""
from pathlib import Path
import hashlib,json
import torch

def require_accepted_model(root,trial='canonical-pilot01'):
    root=Path(root);load=lambda name:json.loads((root/'results'/f'{trial}-{name}.json').read_text())
    analysis=load('analysis');assert analysis['passed'] and analysis['repair_acceptance_passed'] and analysis['selection_and_winner_independently_reconstructed'] and not analysis['test_evaluated'] and analysis['optimizer_updates']==0
    collected=load('collected');assert collected['passed'] and collected['experiment_complete'] and collected['cleanup_verified']
    assert load('permission-removed')['exact_grant_removed']
    outputs=root/'data'/f'{trial}-results';freeze=json.loads((outputs/'selection-freeze.json').read_text());comparison=json.loads((outputs/'comparison.json').read_text());complete=json.loads((outputs/'complete.json').read_text())
    winner=freeze['winner'];assert winner!='raw_baseline' and winner==analysis['winner']==comparison['winner'];assert comparison['passed'] and all(comparison['checks'].values()) and not comparison['test_evaluated'];assert complete['passed'] and complete['repair_acceptance_passed'] and complete['selection_frozen_before_confirmation'] and not complete['test_evaluated'];assert not freeze['confirmation_scored'] and not freeze['test_evaluated']
    selection=next(a for a in freeze['arms'] if a['arm']==winner);assert selection['accepted_on_selection'] and selection['apply_decoder']
    path=outputs/f'{winner}-selected.pt';snapshot=torch.load(path,map_location='cpu',weights_only=True);assert snapshot['epoch']==selection['epoch'] and snapshot['apply_decoder'];digest=hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in snapshot['model'].values())).hexdigest();assert digest==selection['model_sha256']
    return dict(trial=trial,winner=winner,epoch=selection['epoch'],model_sha256=digest,checkpoint_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),snapshot=snapshot)

from pathlib import Path
import json,datetime
R=Path(__file__).parent;D=R/'data/train01'
rows={}
for n in ['previous','bound_only','bounded','strength_only','heads','interpolation']:
 d=json.loads((D/(n+'-evaluation.json')).read_text());rows[n]=d['summary']
t=json.loads((D/'heads-training.json').read_text());cleanup=json.loads((R/'results/cleanup.json').read_text());assert not any(cleanup.values())
report={'fit_seconds':t['elapsed_s'],'selected_step':t['selected_step'],'summary':rows,'cleanup':cleanup,'checkpoint_restore':json.loads((D/'resume-check.json').read_text()),'scope':'32 training and six development-validation cases; full 91-frame histories, no fresh tests. Heads fit restarted from same saved warm-start because paused laptop fit had no recoverable checkpoint. Completed bounded fit retained.','budget_ceiling_usd':1,'estimated_total_usd_range':[.15,.4],'cost_caveat':'Estimate including compute and output download, not billing invoice; retained cloud storage continues to incur a small charge.'}
(R/'results/comparison.json').write_text(json.dumps(report,indent=2))
with (R/'README.md').open('a') as f:
 f.write('\n## Completed results\n\nFull heads fit completed in %.2f seconds, excluding initial validation and cloud setup. Selected step %d. All six variants evaluated over full histories. All VMs, disks and Batch jobs deleted; temporary single-object read access removed. Checkpoint optimizer/RNG reload passed in-process, but actual Spot replacement was not tested.\n\n| Variant | Hot temperature MAE (C) | Heat-release relative L1 | Radiation-dose relative L1 | Flame IoU |\n|---|---:|---:|---:|---:|\n'%(t['elapsed_s'],t['selected_step']))
 for n,s in rows.items():
  v=s['validation']['post_source'];f.write('| %s | %.2f | %.4f | %.4f | %.4f |\n'%(n,v['hot_MAE_C'],v['HRR_curve_relative_L1'],v['radiation_dose_relative_L1'],v['flame_IoU']))
 f.write('\nThese are development-validation means over 22–180s, not independent test accuracy. The six validation cases selected checkpoints and have been reused in development. Improvements are modest. The 6C floor removes extreme negative predictions by construction; scalar normalization alone accounts for the change in total heat-release error. Separate branches improve spatial combustion overlap and radiation while temperature is slightly worse than the bounded-only fit. Same generic crown and artificial ignition; no claims of real-world validation or sequence learning. Estimated total run cost $0.15–$0.40, not an invoice; full $1 reservation retained.\n')
print(json.dumps({'fit_seconds':t['elapsed_s'],'selected_step':t['selected_step'],'cleanup_verified':True}))

"""Plot measured synthetic-test cost versus ignition-time error."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'results/comparison.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for ax,group,title in zip(axes,['coupon','transport'],['Heated-wall verification','Coupled flame / radiation screening']):
    for r,color in zip(report[group],['#bd5d26','#186c87','#727238','#6352a0']):
        err=r['max_ignition_time_error_s']
        if err is None:continue
        ax.scatter(r['total_wall_speedup'],err,s=100,color=color)
        ax.annotate(r['variant'],(r['total_wall_speedup'],err),xytext=(6,6),textcoords='offset points',fontsize=10)
    ax.axvline(1,color='gray',linewidth=0.8,linestyle='--')
    ax.set_xlabel('Observed wall-time ratio (uncontrolled load)')
    ax.set_ylabel('Maximum ignition-time difference (s)')
    ax.set_title(title);ax.grid(alpha=0.2);ax.margins(0.25)
fig.suptitle('Synthetic screening only — wall-time ratios are confounded by other workload\nIdentical reference repeat took 2.58× longer; timing errors exclude classification disagreements',fontsize=11)
fig.savefig(ROOT/'results/speed_error.png',dpi=160)

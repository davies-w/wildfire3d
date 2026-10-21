from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
R=Path(__file__).parent;cs=json.loads((R/'cases.json').read_text());fig,axs=plt.subplots(2,6,figsize=(15,5),layout='constrained')
for ax,c in zip(axs.flat,cs):
 h=c['crown_height_m'];a=np.deg2rad(c['angle_deg']);color={'train':'#278267','validation':'#ca8a24','test':'#7256a8'}[c['split']];ax.add_patch(Polygon([[6.5,2],[9.5,2],[8,2+h]],facecolor=color,alpha=.5*c['loading_multiplier'],edgecolor=color));ax.scatter([8+1.2*np.cos(a)],[2.1],color='#d22a22',s=25);ax.axhline(0,color='saddlebrown');ax.annotate('',xy=(11,7),xytext=(5,7),arrowprops={'arrowstyle':'->','color':'#2778a4'});ax.set(xlim=(4,12),ylim=(-.5,16),aspect='equal');ax.set_title(f"{c['case']} {c['split']}\n{h:g}m crown / {c['loading_multiplier']:.1f}× load\n{c['wind_speed']:.1f}m/s, {c['angle_deg']:g}°",fontsize=9);ax.set_xticks([]);ax.set_yticks([0,8,16]);ax.tick_params(labelsize=7)
fig.suptitle('Height/loading pilot — side view (X–Z), fixed 3m diameter, crown base 2m\nRed: imposed ignition arc projected into side view, active 20s. Arrow: wind +X. Purple cases remain untouched until prediction freeze.',fontsize=11);fig.savefig(R/'results/layouts.png',dpi=130);plt.close(fig)

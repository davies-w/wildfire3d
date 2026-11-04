"""Accept actual terminal completion, including a clean stop exactly at T_END.
No solver execution. Always use this invocation's captured stdout, never a stale .out.
"""
import math,re
from pathlib import Path
def terminal_success(result,device_time,logpath,target=180.0):
 if result['returncode']!=0 or result['forced_termination'] or not math.isfinite(device_time) or device_time<target-1e-6:return False
 text=Path(logpath).read_text()
 if re.search(r'\bERROR(?:\s*\(|\s*:)',text,re.I):return False
 if 'completed successfully' in text.lower():return True
 if not result['stopped']:return False
 pairs=list(re.finditer(r'Time Step:\s+(\d+), Simulation Time:\s+([\d.Ee+-]+)\s+s',text))
 if not pairs:return False
 values=[(int(m[1]),float(m[2])) for m in pairs]
 if not all(math.isfinite(t) for _,t in values):return False
 if not all(b[0]>a[0] and b[1]>a[1] for a,b in zip(values,values[1:])):return False
 return values[-1][1]>=target-1e-6 and 'STOP: FDS stopped by user' in text[pairs[-1].end():]

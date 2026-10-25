"""Reporting-only deterministic replacement regression; no fitting."""
import torch,json
from pathlib import Path
def reporting_cumsum(x,dim):
 return torch.cumsum(x.detach().cpu(),dim).to(x.device)
def main():
 torch.use_deterministic_algorithms(True);torch.manual_seed(3523);checks=[]
 for name in ['random','zero','pulse']:
  x=torch.rand(52,90)
  if name=='zero':x.zero_()
  if name=='pulse':x.zero_();x[:,9]=1
  prefix=torch.cat([torch.zeros(52,1),reporting_cumsum(x,1)],1);ends=torch.arange(1,91);begins=(ends-5).clamp_min(0)
  got=prefix[:,ends]-prefix[:,begins];expected=torch.stack([x[:,max(0,j-5):j].sum(1) for j in range(1,91)],1)
  assert torch.allclose(got,expected,atol=1e-5,rtol=1e-5)
  checks.append(dict(case=name,max_error=float((got-expected).abs().max())))
 result=dict(passed=True,checks=checks,scope='CPU reporting-only, no optimizer. Complete CUDA evaluation must be checked before any replacement fitting.')
 (Path(__file__).parent/'results/activity-metric-repair-test.json').write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':main()

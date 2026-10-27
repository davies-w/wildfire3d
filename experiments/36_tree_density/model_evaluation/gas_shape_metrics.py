"""Prospective constrained selection for the integral-preserving trial only."""
from gas_head_metrics import evaluate,acceptance as original_acceptance
def acceptance(b,c,k,scales):
 checks=original_acceptance(b,c,k,scales);checks['overprediction_tail']=c['startup_gas_p90_overprediction'] is not None and b['startup_gas_p90_overprediction'] is not None and c['startup_gas_p90_overprediction']<=b['startup_gas_p90_overprediction']*(1+k['startup_gas_p90_overprediction_relative_increase_at_most']);return checks
def eligible(b,c,k,scales):
 checks=acceptance(b,c,k,scales)
 return c['startup_gas_p90_deficit'] is not None and all(v for name,v in checks.items() if name not in ['startup_gas','peak_amplitude']) and c['peak_release_MAE_kg_s']<=b['peak_release_MAE_kg_s']
def selection_key(row):return (row['validation']['startup_gas_p90_deficit'],row['validation']['objective'],row['epoch'])

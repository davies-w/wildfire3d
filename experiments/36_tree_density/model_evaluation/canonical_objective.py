"""Combined old-regime and canonical losses; no optimizer or parameter mutation."""
from guard_matched_objective import objective as regime_objective
from canonical_data import canonical_physical_loss

def objective(model,data,ids,origins,canonical_horizons,canonical_origins,*,normalization,canonical_coefficient):
    args=data.training_batch(model,ids,origins)
    loss,parts=regime_objective(*args[:4],data.scales,data.std,*args[4:],**data.objective_metadata(ids,origins),normalization=normalization)
    # Both arms retain the balanced0.3/0.15 startup risks.
    loss=loss+.2*parts['under_tail']+.1*parts['over_tail']
    canonical=data.canonical_batch(model,ids,canonical_horizons,canonical_origins)
    canonical_loss=canonical_physical_loss(canonical,data.canonical_case_factor)
    return loss+canonical_coefficient*canonical_loss,{**parts,'canonical_physical':canonical_loss}

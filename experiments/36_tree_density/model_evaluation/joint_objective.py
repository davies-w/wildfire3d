"""Four-state loss plus replica-balanced minibatch tail risk; no optimizer."""
import torch

def weighted_cvar(values, weights, fraction=.2):
    assert values.ndim == weights.ndim == 1 and values.shape == weights.shape
    assert 0 < fraction <= 1 and bool((weights >= 0).all()) and bool(weights.sum() > 0)
    ranked, order = torch.sort(values, descending=True, stable=True)
    w = weights[order]
    mass = fraction*w.sum()
    before = w.cumsum(0)-w
    used = torch.minimum(w, (mass-before).clamp_min(0))
    return (ranked*used).sum()/mass

def objective(prediction, truth, initial, times, scales, std,
              state_weights, replica_weights, full_history_gas_peak, valid_mask=None):
    encoded = (torch.asinh(prediction/scales)-torch.asinh(truth/scales))/std
    valid = torch.ones_like(state_weights, dtype=torch.bool) if valid_mask is None else valid_mask
    assert valid.shape == state_weights.shape and bool((state_weights[~valid] == 0).all())
    lengths = valid.sum(1).clamp_min(1)
    state = ((encoded.square().mean(-1)*state_weights).sum(1)/lengths).mean()
    startup = (times[:, 1:] <= 32.2) & valid
    peak = full_history_gas_peak.abs()
    denominator = torch.where(peak > 0, peak.clamp_min(1e-6), torch.full_like(peak, .01))
    under = (((truth[:, :, 2]-prediction[:, :, 2]).clamp_min(0)*startup).amax(1)/denominator).square()
    over = (((prediction[:, :, 2]-truth[:, :, 2]).clamp_min(0)*startup).amax(1)/denominator).square()
    eligible = startup.any(1)
    if bool(eligible.any()):
        under_tail = weighted_cvar(under[eligible], replica_weights[eligible])
        over_tail = weighted_cvar(over[eligible], replica_weights[eligible])
    else:
        under_tail = over_tail = prediction.sum()*0
    predicted_peak = torch.maximum(prediction[:, :, 2].masked_fill(~valid, -float('inf')).amax(1), initial[:, 2])
    true_peak = torch.maximum(truth[:, :, 2].masked_fill(~valid, -float('inf')).amax(1), initial[:, 2])
    peak_error = ((((predicted_peak-true_peak)/denominator).square())*replica_weights).mean()
    dt = times[:, 1:]-times[:, :-1]
    def sampling_residual(curve):
        gas = torch.cat([initial[:, 2:3], curve[:, :, 2]], 1)
        integrated = torch.cumsum(.5*(gas[:, 1:]+gas[:, :-1])*dt, 1)/.75
        return integrated-(initial[:, 1:2]-curve[:, :, 1])
    residual_error = ((((sampling_residual(prediction)-sampling_residual(truth))/initial[:, 1:2].clamp_min(1e-6)).square())*valid).sum(1)/lengths
    consistency = (residual_error*replica_weights).mean()
    loss = state+.1*under_tail+.05*over_tail+.05*peak_error+.1*consistency
    return loss, dict(state=state, under_tail=under_tail, over_tail=over_tail,
                      peak_error=peak_error, sampling_residual_error=consistency)

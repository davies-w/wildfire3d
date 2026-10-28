"""Independent four-output heads over frozen GRU features.

Structured masses use interval loss hazards. Endpoint gas is a separate sample;
it is deliberately not forced to integrate to the derived dry-fuel labels.
"""
import math
import torch
from torch import nn
import torch.nn.functional as F

def deterministic_prefix_sum(value, dim):
    """Explicit ordered additions, retaining monotonicity for nonnegative inputs.

    CUDA floating cumsum is unsupported under strict deterministic algorithms.
    Fixed left-to-right additions also avoid triangular-product rounding that
    can make a nonnegative prefix decrease slightly at an unchanged endpoint.
    """
    pieces=value.unbind(dim);assert pieces
    running=pieces[0];outputs=[running]
    for piece in pieces[1:]:
        running=running+piece;outputs.append(running)
    return torch.stack(outputs,dim=dim)

def positive_with_boundary_gradient(x):
    # Explicit right-sided derivative at zero; negative interior still has zero derivative.
    return torch.where(x >= 0, x, torch.zeros_like(x))

class JointDecoder(nn.Module):
    def __init__(self, feature_mean, feature_std, state_std, physical_scales, mode):
        super().__init__()
        assert mode in ('direct', 'interval')
        self.mode = mode
        self.register_buffer('feature_mean', feature_mean.clone())
        self.register_buffer('feature_std', feature_std.clone())
        self.register_buffer('state_std', state_std.clone())
        self.register_buffer('physical_scales', physical_scales.clone())
        self.w1 = nn.Parameter(torch.empty(4, 46, 16))
        self.b1 = nn.Parameter(torch.empty(4, 16))
        self.w2 = nn.Parameter(torch.zeros(4, 16))
        self.b2 = nn.Parameter(torch.zeros(4))
        nn.init.uniform_(self.w1, -1/math.sqrt(46), 1/math.sqrt(46))
        nn.init.uniform_(self.b1, -1/math.sqrt(46), 1/math.sqrt(46))

    def forward(self, features, base_states, initial_state, times):
        assert features.shape[-1] == 46 and base_states.shape[-1] == 4
        assert times.shape == (features.shape[0], features.shape[1]+1)
        assert bool((times[:, 1:] > times[:, :-1]).all())
        assert bool(torch.isfinite(initial_state).all())
        x = (features-self.feature_mean)/self.feature_std
        hidden = torch.tanh(torch.einsum('bti,oih->btoh', x, self.w1)+self.b1)
        delta = torch.einsum('btoh,oh->bto', hidden, self.w2)+self.b2
        encoded = torch.asinh(base_states/self.physical_scales)
        # Exact baseline anchor when delta=0, including existing negative values.
        direct = base_states+self.physical_scales*(
            torch.sinh(encoded+delta*self.state_std)-torch.sinh(encoded))
        if self.mode == 'direct':
            return direct
        # Estimated observed water can be slightly negative; project the boundary too.
        initial = initial_state[:, None, :2].clamp_min(0)
        safe_initial = initial.clamp_min(1e-12)
        clipped = torch.maximum(torch.minimum(base_states[:, :, :2], safe_initial),
                                safe_initial*1e-6)
        projected = torch.cummin(clipped, dim=1).values
        previous = torch.cat([safe_initial, projected[:, :-1]], dim=1)
        increments = (torch.log(previous)-torch.log(projected)).clamp_min(0)
        # The scale permits new loss from a flat base and can suppress any base loss.
        dt = (times[:, 1:]-times[:, :-1])[:, :, None]
        reference = F.softplus(torch.zeros_like(delta[:, :, :2]))
        adjustment_scale = (increments+.1*dt/2)/reference
        hazards = positive_with_boundary_gradient(increments+adjustment_scale*(F.softplus(delta[:, :, :2])-reference))
        masses = initial*torch.exp(-deterministic_prefix_sum(hazards, dim=1))
        # Rectify the gas anchor before applying the learnable residual, so even a
        # negative/zero old prediction has a usable one-sided release derivative.
        anchor = base_states[:, :, 2:3].clamp_min(0)
        gas_encoded = torch.asinh(anchor/self.physical_scales[2])
        gas_candidate = anchor+self.physical_scales[2]*(torch.sinh(gas_encoded+delta[:, :, 2:3]*self.state_std[2])-torch.sinh(gas_encoded))
        gas = positive_with_boundary_gradient(gas_candidate)
        # The heating INDEX can be negative and is left signed.
        return torch.cat([masses, gas, direct[:, :, 3:4]], -1)

def interval_mass_loss_rates(prediction, initial_state, times, *, project_initial=False):
    reference = initial_state[:, :2].clamp_min(0) if project_initial else initial_state[:, :2]
    curve = torch.cat([reference[:, None], prediction[:, :, :2]], dim=1)
    return (curve[:, :-1]-curve[:, 1:])/(times[:, 1:]-times[:, :-1])[:, :, None]

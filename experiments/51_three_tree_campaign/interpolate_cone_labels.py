"""Explicitly synthetic cone targets between observed raw-temperature frames.

No extraction, model training or simulation is performed here. Original six-value
cone rows and timestamps remain available beside interpolated rows and provenance.
"""
import numpy as np

CONE_NAMES = ('presence', 'pivot_height_m', 'tilt_from_vertical_deg',
              'axial_length_m', 'end_radius_m', 'peak_temperature_C')


def interpolate_cones(source_time, source_cones, target_time):
    """Piecewise-linear interpolation, with no extrapolation or hidden smoothing.

Absent observed cones must use the historical zero-geometry convention. Across
an appearance/disappearance interval this produces a soft presence indicator and
geometry interpolated from/to zero; neither is an extra simulation observation.
"""
    t = np.asarray(source_time, dtype=np.float64)
    y = np.asarray(source_cones, dtype=np.float64)
    q = np.asarray(target_time, dtype=np.float64)
    if t.ndim != 1 or len(t) < 2 or y.shape != (len(t), 6):
        raise ValueError('Expected at least two source timestamps and six cone channels')
    if q.ndim != 1 or not len(q):
        raise ValueError('Target timestamps must be a nonempty vector')
    if not all(np.isfinite(x).all() for x in (t, y, q)):
        raise ValueError('Nonfinite source or target')
    if not (np.diff(t) > 0).all() or not (np.diff(q) > 0).all():
        raise ValueError('Timestamps must strictly increase')
    if q[0] < t[0] or q[-1] > t[-1]:
        raise ValueError('Extrapolation is not permitted')
    if not np.isin(y[:, 0], [0, 1]).all():
        raise ValueError('Observed presence must be binary')
    if not (y[y[:, 0] == 0, 1:] == 0).all():
        raise ValueError('Inactive source geometry must use the declared zero convention')
    hi = np.searchsorted(t, q, side='right').clip(1, len(t)-1)
    lo = hi - 1
    alpha = (q-t[lo])/(t[hi]-t[lo])
    values = y[lo] + alpha[:, None]*(y[hi]-y[lo])
    # Only exactly matching saved timestamps are marked observed. Near matches
    # remain interpolated; this prevents upgrading nominal 36 s to an observation.
    nearest = np.where(np.abs(q-t[lo]) <= np.abs(q-t[hi]), lo, hi)
    observed = q == t[nearest]
    values[observed] = y[nearest[observed]]
    assert np.isfinite(values).all()
    assert ((values >= np.minimum(y[lo], y[hi])-1e-10) &
            (values <= np.maximum(y[lo], y[hi])+1e-10)).all()
    return dict(cones=values, time_s=q.copy(), observed=observed,
                interpolated=~observed, source_time_s=t.copy(),
                source_cones=y.copy(), left_source_index=lo,
                right_source_index=hi, right_weight=alpha)

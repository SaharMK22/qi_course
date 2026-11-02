"""Statistical helpers shared across labs.

Kept deliberately simple and transparent -- these wrap very few lines of
numpy/scipy so students (and Dale) can read the source and see exactly
what's being computed, rather than treating it as a black box.
"""

import math

import numpy as np


def descriptive_stats(x):
    """Return a dict of basic descriptive statistics for a 1D sample.

    Parameters
    ----------
    x : array-like

    Returns
    -------
    dict with keys: n, mean, std, min, max, skewness

    Notes for students
    -------------------
    `skewness` here is the simple (Fisher-Pearson) third-moment measure.
    A value near 0 is consistent with a symmetric distribution (like a
    Gaussian); a clearly positive or negative value says the data leans
    to one side.
    """
    x = np.asarray(x, dtype=float)
    mean = x.mean()
    std = x.std(ddof=1)
    skew = np.mean(((x - mean) / std) ** 3) if std > 0 else 0.0
    return {
        "n": x.size,
        "mean": mean,
        "std": std,
        "min": x.min(),
        "max": x.max(),
        "skewness": skew,
    }


def fit_normal_pdf(x, n_points=200):
    """Fit a normal distribution to x (by its sample mean and std) and
    return points to plot the fitted curve.

    Parameters
    ----------
    x : array-like
        Sample data.
    n_points : int
        Number of points along the fitted curve.

    Returns
    -------
    grid : numpy.ndarray
        x-values spanning the data range.
    pdf : numpy.ndarray
        The fitted normal density at each grid point.
    params : dict
        {'mean': ..., 'std': ...} -- the fitted parameters, so students
        see exactly what was estimated from their data.
    """
    x = np.asarray(x, dtype=float)
    mean, std = x.mean(), x.std(ddof=1)
    grid = np.linspace(x.min(), x.max(), n_points)
    pdf = (1.0 / (std * np.sqrt(2 * np.pi))) * np.exp(
        -0.5 * ((grid - mean) / std) ** 2
    )
    return grid, pdf, {"mean": mean, "std": std}


# ---------------------------------------------------------------------------
# Lab 2 additions: how well does the bell curve describe the data?
# ---------------------------------------------------------------------------
def fraction_within(x, n_std):
    """Fraction of a sample lying within `n_std` standard deviations of its
    mean. A Gaussian puts about 68% within 1 std and 95% within 2 std, so
    comparing your data to those numbers is a quick test of the bell curve.
    """
    x = np.asarray(x, dtype=float)
    mean, std = x.mean(), x.std(ddof=1)
    return float(np.mean(np.abs(x - mean) <= n_std * std))


# ---------------------------------------------------------------------------
# Lab 3 additions: daily precipitation (skewed, never negative)
# ---------------------------------------------------------------------------
def wet_day_summary(prcp, wet_threshold_mm=1.0):
    """Split daily precipitation into "does it rain?" and "how much?".

    A day counts as wet if it has at least `wet_threshold_mm` of
    precipitation (1 mm is a common climatology convention; it also avoids
    trace amounts that the gauge rounds to zero).

    Returns
    -------
    dict with
        n_days             days with a recorded value
        wet_fraction       fraction of days that are wet  (occurrence)
        wet_amounts        array of precipitation on wet days (intensity)
        mean_wet_mm, std_wet_mm, skewness_wet
    """
    p = np.asarray(prcp, dtype=float)
    p = p[~np.isnan(p)]
    wet = p[p >= wet_threshold_mm]
    stats = descriptive_stats(wet)
    return {
        "n_days": int(p.size),
        "wet_fraction": float(wet.size / p.size),
        "wet_amounts": wet,
        "mean_wet_mm": float(stats["mean"]),
        "std_wet_mm": float(stats["std"]),
        "skewness_wet": float(stats["skewness"]),
    }


def fit_gamma_pdf(x, n_points=400):
    """Fit a gamma distribution to positive data by matching its mean and
    variance (the "method of moments"), and return points for plotting.

    The gamma distribution is a standard first model for the amount of
    rain on a wet day: it is zero for negative values, rises quickly, and
    has a long tail to the right. Its two parameters follow from the
    sample mean m and variance s2:

        shape = m**2 / s2        scale = s2 / m

    Returns
    -------
    grid, pdf : numpy.ndarray
        Points from 0 to the largest observation, and the fitted density.
    params : dict
        {'shape': ..., 'scale': ...}
    """
    x = np.asarray(x, dtype=float)
    mean, var = x.mean(), x.var(ddof=1)
    shape, scale = mean**2 / var, var / mean
    grid = np.linspace(x.max() / n_points, x.max(), n_points)
    return grid, gamma_pdf(grid, shape, scale), {"shape": shape, "scale": scale}


def gamma_pdf(x, shape, scale):
    """Gamma probability density at x (x > 0)."""
    x = np.asarray(x, dtype=float)
    log_pdf = ((shape - 1) * np.log(x) - x / scale
               - shape * np.log(scale) - math.lgamma(shape))
    return np.exp(log_pdf)


def gamma_exceedance(threshold, shape, scale, n_points=20000):
    """Probability that a gamma-distributed amount exceeds `threshold`.

    Computed the way the idea is defined: as the area under the density to
    the right of the threshold, using the same trapezoid rule as Lab 1.
    """
    from .numerics import trapezoid_integral
    upper = (shape + 40 * math.sqrt(shape) + 20) * scale   # far into the tail
    grid = np.linspace(threshold, upper, n_points)
    area = trapezoid_integral(grid, gamma_pdf(grid, shape, scale))[-1]
    return float(area)


def empirical_exceedance(x, threshold):
    """Fraction of a sample strictly greater than `threshold`."""
    x = np.asarray(x, dtype=float)
    return float(np.mean(x > threshold))

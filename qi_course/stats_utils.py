"""Statistical helpers shared across labs.

Kept deliberately simple and transparent -- these wrap very few lines of
numpy/scipy so students (and Dale) can read the source and see exactly
what's being computed, rather than treating it as a black box.
"""

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

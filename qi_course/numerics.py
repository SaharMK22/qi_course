"""Numerical integration and differentiation helpers.

These are intentionally simple, transparent implementations -- not calls
into scipy's black-box routines -- so students can see exactly what
"integration" and "differentiation" mean as operations on a sequence of
physical measurements. That transparency is the point of Lab 1.
"""

import numpy as np


def trapezoid_integral(x, y):
    """Approximate the running (cumulative) integral of y with respect to x.

    Parameters
    ----------
    x : array-like
        Independent variable (e.g., time in hours), strictly increasing.
    y : array-like
        Dependent variable (e.g., rainfall rate in mm/hr).

    Returns
    -------
    numpy.ndarray
        Cumulative integral, same length as x, starting at 0. The last
        value is the total accumulated amount (e.g., total rainfall).

    Notes for students
    -------------------
    This uses the trapezoid rule: on each interval, the area under the
    curve is approximated as a trapezoid rather than a rectangle. Compare
    the final value here to a running total you compute by hand from the
    raw readings -- they should be close, and the small difference is
    worth discussing in your write-up.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    dx = np.diff(x)
    avg_y = (y[:-1] + y[1:]) / 2.0
    increments = avg_y * dx
    cumulative = np.concatenate(([0.0], np.cumsum(increments)))
    return cumulative


def finite_difference(x, y):
    """Approximate dy/dx at each point using a finite difference.

    Uses a centered difference in the interior, and a one-sided
    (forward/backward) difference at the two endpoints, since a centered
    difference needs a neighbor on both sides.

    Parameters
    ----------
    x : array-like
    y : array-like

    Returns
    -------
    numpy.ndarray
        Approximate derivative, same length as x.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    dydx = np.empty_like(y)
    dydx[1:-1] = (y[2:] - y[:-2]) / (x[2:] - x[:-2])
    dydx[0] = (y[1] - y[0]) / (x[1] - x[0])
    dydx[-1] = (y[-1] - y[-2]) / (x[-1] - x[-2])
    return dydx

"""Shared plotting helpers so every lab's figures share one visual style."""

import matplotlib.pyplot as plt
import numpy as np


def quick_timeseries_plot(x, y, title="", xlabel="", ylabel="", ax=None):
    """Plot y against x with consistent, readable defaults.

    Parameters
    ----------
    x, y : array-like
    title, xlabel, ylabel : str
    ax : matplotlib.axes.Axes, optional
        Pass an existing Axes to plot into it; otherwise a new figure
        is created.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes used, so students can keep customizing the plot
        (e.g., ax.axvline(...) to mark a specific hour).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, linewidth=2)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    return ax


def histogram_with_fit(data, fit_x, fit_y, title="", xlabel="", ylabel="Density", ax=None,
                       bins=25, fit_label="Fitted normal"):
    """Plot a normalized histogram of `data` with a fitted curve overlaid.

    Meant for the "does this look Gaussian?" comparison in Lab 2: plot
    the histogram of a sample, then overlay the fitted normal curve
    from `qi_course.stats_utils.fit_normal_pdf`, so students can see
    both at once rather than the bare numbers.

    Parameters
    ----------
    data : array-like
        The raw sample (e.g., one city's July daily highs).
    fit_x, fit_y : array-like
        The fitted-curve grid and density values (from `fit_normal_pdf`).
    ax : matplotlib.axes.Axes, optional
    bins : int or array-like
        Number of bins, or the bin edges. Real thermometer data is recorded
        in whole degrees Fahrenheit, which leaves small gaps between possible
        values in degrees C; bins about 1 degree wide avoid a comb-like look.
    fit_label : str
        Legend text for the fitted curve.

    Returns
    -------
    matplotlib.axes.Axes
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(data, bins=bins, density=True, alpha=0.55, label="Observed data")
    ax.plot(fit_x, fit_y, linewidth=2, color="black", label=fit_label)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True, alpha=0.3)
    return ax


def temperature_bins(values_c, width_f=2):
    """Histogram bin edges (in degrees C) that line up with whole degrees F.

    U.S. thermometers were read in whole degrees Fahrenheit, so after
    conversion the Celsius values fall on a grid about 0.56 C apart. Bins
    whose width is a whole number of degrees F (2 F by default, about 1.1 C)
    each hold the same number of possible readings, which avoids a comb-like
    pattern that comes from the rounding, not from the weather.
    """
    f = np.asarray(values_c, dtype=float) * 9.0 / 5.0 + 32.0
    low = np.floor(f.min()) - 0.5
    high = np.ceil(f.max()) + 0.5
    edges_f = np.arange(low, high + width_f, width_f)
    return (edges_f - 32.0) * 5.0 / 9.0

"""qi_course: shared utilities for the "Developing Quantitative Intuition
in Water and Weather Science" course labs.

This file's job is to decide what a lab notebook gets automatically when
it runs:

    import qi_course as qc

Everything named in __all__ below becomes available directly as
qc.<name>, without anyone needing to know which file inside this package
it actually lives in. As new labs are built, add their new functions to
the relevant module (numerics.py, data_io.py, plotting.py, or a new
module for that lab), then import and list them here.

__version__ is a plain string, bumped by hand each time a change is
tagged as a new release on GitHub (see the README). Nothing reads this
value automatically -- it exists so a student or instructor can run
`qc.__version__` inside a notebook and confirm which version they're on
if something looks unexpected.
"""

__version__ = "0.2.0"

from .numerics import trapezoid_integral, finite_difference
from .data_io import load_demo_harvey_precip, load_demo_july_highs, list_demo_cities
from .plotting import quick_timeseries_plot, histogram_with_fit
from .stats_utils import descriptive_stats, fit_normal_pdf

__all__ = [
    "trapezoid_integral",
    "finite_difference",
    "load_demo_harvey_precip",
    "load_demo_july_highs",
    "list_demo_cities",
    "quick_timeseries_plot",
    "histogram_with_fit",
    "descriptive_stats",
    "fit_normal_pdf",
]

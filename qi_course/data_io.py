"""Data-loading helpers for the course labs.

IMPORTANT: `load_demo_harvey_precip` below returns SYNTHETIC, illustrative
data shaped like the hourly rainfall pulse from a slow-moving tropical
system. It is NOT the real observed Hurricane Harvey record. It exists so
this package and Lab 1 can be built and tested before a real dataset is
wired in. Before this lab is used with students, replace this function (or
add a new one) that loads an actual gauge record, for example from NOAA's
NCEI archives or a USGS rain-gauge/streamgage API, and update Lab 1's
notebook to call that instead.
"""

import numpy as np
import pandas as pd


def load_demo_harvey_precip():
    """Return a synthetic hourly rainfall time series for prototyping Lab 1.

    This is placeholder data only -- see the module docstring.

    Returns
    -------
    pandas.DataFrame
        Columns: 'hour' (0 to 119, five days) and 'rain_mm_per_hr'.
    """
    rng = np.random.default_rng(seed=42)
    hours = np.arange(0, 120)  # five days, hourly
    # A slow-moving-storm-like pulse: rain builds, stays heavy, tapers off.
    base = 30 * np.exp(-((hours - 60) ** 2) / (2 * 20**2))
    noise = rng.normal(0, 1.5, size=hours.shape)
    rain = np.clip(base + noise, 0, None)
    return pd.DataFrame({"hour": hours, "rain_mm_per_hr": rain})


# Demo cities for Lab 2 -- (mean, std) of daily *July high* temperatures,
# in degrees C, chosen to be roughly realistic for each city's climate.
# Real daily highs are NOT Gaussian across a full year (there's a strong
# seasonal cycle) -- restricting to one calendar month, many years, is
# what makes "approximately Gaussian" a defensible claim. This is why
# Lab 2 should pull one month at a time, not a raw annual time series.
_DEMO_CITY_JULY_STATS = {
    "Tucson": {"mean_c": 38.0, "std_c": 2.0},
    "Buffalo": {"mean_c": 27.0, "std_c": 2.3},
    "Seattle": {"mean_c": 24.0, "std_c": 2.6},
}


def load_demo_july_highs(city="Tucson", n_years=100, seed=0):
    """Return synthetic daily July high temperatures for a demo city.

    IMPORTANT: like `load_demo_harvey_precip`, this is SYNTHETIC,
    illustrative data (drawn directly from a normal distribution with a
    realistic mean/std for the city), not a real historical record. It
    exists so Lab 2's statistics and plotting can be built and tested
    before real station data is wired in. Before Lab 2 is used with
    students, replace this with a loader for an actual long-record
    station, for example from NOAA's GHCN-Daily archive, so the shape
    of the distribution is something students discover rather than
    something built into the demo by construction.

    Parameters
    ----------
    city : str
        One of the keys in `list_demo_cities()`.
    n_years : int
        Number of years of July data to simulate (31 days each).
    seed : int
        Random seed, for reproducibility.

    Returns
    -------
    pandas.DataFrame
        Columns: 'year', 'day_of_july' (1-31), 'high_temp_c'.
    """
    if city not in _DEMO_CITY_JULY_STATS:
        raise ValueError(
            f"Unknown demo city '{city}'. Try one of: "
            f"{list(_DEMO_CITY_JULY_STATS)}"
        )
    stats = _DEMO_CITY_JULY_STATS[city]
    rng = np.random.default_rng(seed=seed)
    years = np.repeat(np.arange(1, n_years + 1), 31)
    days = np.tile(np.arange(1, 32), n_years)
    temps = rng.normal(stats["mean_c"], stats["std_c"], size=years.shape)
    return pd.DataFrame({"year": years, "day_of_july": days, "high_temp_c": temps})


def list_demo_cities():
    """Return the list of city names available to `load_demo_july_highs`."""
    return list(_DEMO_CITY_JULY_STATS)

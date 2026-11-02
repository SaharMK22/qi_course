# qi_course

This info is mainly for the developers and students do not need to go through them.

Shared Python utilities and real data for the "Developing Quantitative
Intuition in Water and Weather Science" course labs. Built so every lab
notebook can reuse the same, tested data-loading, numerics, statistics, and
plotting code instead of each lab reinventing it.

## Package layout

```
qi_course_repo/
  pyproject.toml        <- package metadata + dependencies (pip reads this)
  README.md             <- this file
  smoke_test.py         <- run this before tagging any new release
  hello_qi_course.ipynb                    <- minimal "does the install work" notebook
  lab2_temperature_distributions.ipynb     <- Lab 2, real station data (draft)
  lab3_precipitation_distributions.ipynb   <- Lab 3, real station data (draft)
  lab6_gradient_divergence_curl.ipynb      <- Lab 6, real gridded winds (draft)
  tools/                <- developer tools, not used by students
    real_data_builder.py, build_real_data_colab.ipynb   <- rebuilds qi_course/data
  qi_course/
    __init__.py         <- decides what "import qi_course as qc" exposes
    numerics.py         <- trapezoid_integral, finite_difference
    stats_utils.py      <- descriptive stats, normal and gamma fits, exceedance
    stations.py         <- load_station, find_stations, month_values, annual_totals
    fields.py           <- gradient, divergence, vorticity, geostrophic wind, maps
    plotting.py         <- histogram_with_fit, temperature_bins, quick_timeseries_plot
    data_io.py          <- synthetic Lab 1 / early Lab 2 demo data (used by hello notebook)
    data/               <- real data that ships inside the package (about 1 MB)
```

## How a lab notebook uses this (Colab)

The first cell of every lab notebook is:

```python
!pip install git+https://github.com/SaharMK22/qi_course.git@v0.3.0 --quiet
import qi_course as qc
```

The `@v0.3.0` pins the install to a specific tagged release, so every
notebook gets exactly that version of the code and data, not whatever the
newest commit happens to be. Colab starts a completely fresh environment
every time a notebook is opened, so this line has to run every session
anyway; pinning it just makes sure "fresh" also means "consistent."

Typical use in a lab:

```python
df = qc.load_station("New Orleans")                 # real daily record, 1893-present
highs = qc.month_values(df, "tmax_c", 7)            # every July daily high
stats = qc.descriptive_stats(highs)
grid, pdf, params = qc.fit_normal_pdf(highs)

case = qc.load_case("1993-03-13")                   # 850 hPa winds and heights
vort = qc.vorticity(case["u"], case["v"], case["lat"], case["lon"])
```

## The included notebooks

- `hello_qi_course.ipynb`: a minimal sanity check. Install the library, print
  the version, run one function from each early lab. Meant to be the first
  thing anyone runs, to confirm the install pattern works.
- `lab2_temperature_distributions.ipynb`, `lab3_precipitation_distributions.ipynb`,
  `lab6_gradient_divergence_curl.ipynb`: first working drafts of Labs 2, 3 and 6,
  built on real data and structured as Predict, Calculate, Visualize, Explain. Each
  ends with an instructor-notes cell (delete it before sharing with students).
  These are drafts for discussion, not finished labs.

## Real data: sources, quality control, limits

All bundled data are public NOAA data, kept small enough to ship inside the package.

- Station records: NOAA NCEI GHCN-Daily, daily maximum and minimum temperature and
  precipitation. Any value that failed NOAA's own quality checks was removed, not repaired.
  Missing days are NaN, never zero. Stations were kept only if at least 90 percent of days
  were present over 1926-2025. Pulled on the date recorded in `qi_course/data/stations.csv`
  (last record dates run to late October 2026).
- Gridded winds and heights: NOAA PSL NCEP/NCAR Reanalysis 1, daily means at 850 hPa on a
  2.5 degree grid over North America, for two dates (1993-03-13 and 2017-08-27).
- Any other station can be fetched live with `qc.find_stations(lat, lon)` and
  `qc.load_station(station_id)`; this needs internet access and has not been tested at
  class scale.
- To add or refresh data, run `tools/build_real_data_colab.ipynb` in Colab, copy its output
  into `qi_course/data/`, bump the version, and release.

Limits worth remembering: the bundled station list is geographically narrow (three West Coast
stations and New Orleans) and does not yet include interior or desert stations. Lab 1's
rainfall data (`load_demo_harvey_precip`) is still synthetic.

## Turning this folder into the installable GitHub repo

1. Create a new **public** repository on GitHub (public avoids needing a
   personal access token embedded in every student's notebook just to
   install a package with no sensitive data in it).
2. Upload this folder's contents to it, keeping the folder structure.
3. On GitHub, create a Release tagged `v0.3.0` from that commit.
4. Use the install line above in every lab notebook's first cell.

## Releasing an update later

1. Make a change to a module (or add a new one, or new data).
2. Run `python smoke_test.py` and confirm it passes.
3. Bump `version` in `pyproject.toml` and `__version__` in
   `qi_course/__init__.py` together (e.g., to `0.4.0`).
4. Commit, upload, and tag a new GitHub Release, `v0.4.0`.
5. Update the `@v0.3.0` in notebook install cells to `@v0.4.0` when
   you're ready for everyone to pick up the change, not before, so a
   change never silently affects someone mid-lab.

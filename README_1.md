# qi_course

Shared Python utilities for the "Developing Quantitative Intuition in
Water and Weather Science" course labs. Built so every lab notebook can
reuse the same, tested data-loading, numerics, and plotting code instead
of each lab reinventing it.

## Package layout

```
qi_course_lib/
  pyproject.toml        <- package metadata + dependencies (pip reads this)
  README.md             <- this file
  smoke_test.py          <- run this before tagging any new release
  hello_qi_course.ipynb            <- minimal "does the install work" notebook
  lab2_temperature_distributions_demo.ipynb  <- first-pass Lab 2 notebook
  qi_course/
    __init__.py          <- decides what "import qi_course as qc" exposes
    numerics.py           <- trapezoid_integral, finite_difference
    data_io.py             <- data loaders (Lab 1 rainfall demo, Lab 2 July-temperature demo)
    plotting.py             <- quick_timeseries_plot, histogram_with_fit
    stats_utils.py           <- descriptive_stats, fit_normal_pdf
```

## How a lab notebook uses this (Colab)

Once this folder is pushed to a GitHub repository (see below), the first
cell of every lab notebook is just:

```python
!pip install git+https://github.com/SaharMK22/qi_course.git@v0.2.0 --quiet
import qi_course as qc
```

The `@v0.2.0` pins the install to a specific tagged release, so every
notebook -- a student's or Dale's -- gets exactly that version, not
whatever the newest commit happens to be. Colab starts a completely fresh
environment every time a notebook is opened, so this line has to run
every session anyway; pinning it just makes sure "fresh" also means
"consistent."

Then, anywhere in the notebook, Lab 1 style:

```python
df = qc.load_demo_harvey_precip()
cumulative_rain = qc.trapezoid_integral(df["hour"], df["rain_mm_per_hr"])
rate = qc.finite_difference(df["hour"], df["rain_mm_per_hr"])
qc.quick_timeseries_plot(df["hour"], df["rain_mm_per_hr"],
                          title="Rainfall", xlabel="Hour", ylabel="mm/hr")
```

or Lab 2 style:

```python
temps = qc.load_demo_july_highs(city="Tucson", n_years=100)
stats = qc.descriptive_stats(temps["high_temp_c"])
grid, pdf, params = qc.fit_normal_pdf(temps["high_temp_c"])
qc.histogram_with_fit(temps["high_temp_c"], grid, pdf,
                       title="Tucson July highs vs. fitted normal",
                       xlabel="High temperature (C)")
```

## The two included notebooks

- `hello_qi_course.ipynb` -- a minimal sanity check. Install the
  library, print the version, run one function from each lab. This is
  meant to be the very first thing anyone (Dale included) runs, before
  looking at real lab content, to confirm the install pattern works on
  their machine/Colab account.
- `lab2_temperature_distributions_demo.ipynb` -- a first working draft
  of Lab 2 (the temperature / Gaussian-distribution lab), built end to
  end through the course's Predict -> Calculate -> Visualize -> Explain
  structure. This is a draft for discussion, not a finished lab -- see
  the instructor notes at the bottom of the notebook.

## Turning this folder into the real, installable GitHub repo

1. Create a new **public** repository on GitHub (public avoids needing a
   personal access token embedded in every student's notebook just to
   install a package with no sensitive data in it).
2. Push this folder's contents to it as the initial commit.
3. On GitHub, create a Release tagged `v0.2.0` from that commit.
4. Use the install line above, with your actual GitHub username/org in
   the URL, in every lab notebook's first cell.

## Releasing an update later

1. Make your change to a module (or add a new one).
2. Run `python smoke_test.py` locally and confirm it passes and the
   saved plots look right.
3. Bump `version` in `pyproject.toml` and `__version__` in
   `qi_course/__init__.py` together (e.g., to `0.3.0`).
4. Commit, push, and tag a new GitHub Release, `v0.3.0`.
5. Update the `@v0.2.0` in notebook install cells to `@v0.3.0` when
   you're ready for everyone to pick up the change -- not before, so a
   change never silently affects someone mid-lab.

## Known follow-up (do this before real students touch these labs)

- `data_io.load_demo_harvey_precip()` (Lab 1) currently returns
  synthetic, illustrative rainfall data, not the real historical
  Hurricane Harvey record. Before Lab 1 goes live, replace it with a
  loader that pulls an actual gauge record, for example from NOAA's
  NCEI archives or a USGS gauge API.
- `data_io.load_demo_july_highs()` (Lab 2) currently returns synthetic
  daily highs drawn directly from a normal distribution -- so of course
  it looks Gaussian. Before Lab 2 goes live, replace it with a loader
  for a real, multi-decade station record (e.g., NOAA's GHCN-Daily
  archive), so "is this approximately Gaussian?" is a question students
  answer from real observations, not a property built into the demo.

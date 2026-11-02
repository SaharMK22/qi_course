"""Minimal sanity check: import the package and run every function once
on real and demo data. Run this after any change, before tagging a new
release. If this script errors, do not cut a new version tag yet.

Run with:  python smoke_test.py
"""

import numpy as np

import qi_course as qc


def main():
    print(f"qi_course version: {qc.__version__}")

    # ---- Lab 1 (demo data, synthetic) -------------------------------------
    df = qc.load_demo_harvey_precip()
    assert len(df) == 120
    cumulative = qc.trapezoid_integral(df["hour"], df["rain_mm_per_hr"])
    print(f"Lab 1 demo: total rainfall (trapezoid rule) {cumulative[-1]:.1f} mm")
    rate = qc.finite_difference(df["hour"], df["rain_mm_per_hr"])
    assert np.isfinite(rate).all()

    # ---- Labs 2 and 3 (real station data) ---------------------------------
    stations = qc.list_stations()
    assert len(stations) >= 4 and {"label", "first_date"} <= set(stations.columns)
    for name in stations["name"]:
        d = qc.load_station(name)
        assert d.index.is_monotonic_increasing and {"tmax_c", "tmin_c", "prcp_mm"} <= set(d.columns)
        cov = qc.station_coverage(d)
        assert cov["pct_present"]["tmax_c"] > 85, name
        july = qc.month_values(d, "tmax_c", 7)
        s = qc.descriptive_stats(july)
        assert 5 < s["mean"] < 45 and 0.5 < s["std"] < 8, (name, s)
        grid, pdf, _ = qc.fit_normal_pdf(july)
        assert abs(np.trapezoid(pdf, grid) - 1) < 0.05
        w = qc.wet_day_summary(d["prcp_mm"])
        assert 0.03 < w["wet_fraction"] < 0.7
        _, gpdf, par = qc.fit_gamma_pdf(w["wet_amounts"])
        p_model = qc.gamma_exceedance(50, par["shape"], par["scale"])
        p_data = qc.empirical_exceedance(w["wet_amounts"], 50)
        assert abs(p_model - p_data) < 0.03, (name, p_model, p_data)
        totals = qc.annual_totals(d)
        assert len(totals) > 80
        print(f"{name:<28s} July mean {s['mean']:.1f} C | wet days {w['wet_fraction']:.0%} | "
              f"{len(totals)} usable years")
    bins = qc.temperature_bins(july)
    assert np.all(np.diff(bins) > 0)

    # ---- Lab 6 (real gridded winds) ---------------------------------------
    case = qc.load_case("1993-03-13")
    lat, lon = case["lat"], case["lon"]
    vor = qc.vorticity(case["u"], case["v"], lat, lon)
    div = qc.divergence(case["u"], case["v"], lat, lon)
    inner = (slice(2, -2), slice(2, -2))
    i, j = np.unravel_index(np.argmax(vor[inner]), vor[inner].shape)
    i, j = i + 2, j + 2
    assert vor[i, j] > 5e-5, "storm should show strong counterclockwise rotation"
    assert div[i, j] < 0, "air should converge at the storm center"
    ug, vg = qc.geostrophic_wind(case["z"], lat, lon)
    rows = np.broadcast_to((lat >= 25)[:, None], ug.shape)
    assert np.corrcoef(ug[rows], case["u"][rows])[0, 1] > 0.85
    print(f"Lab 6: max vorticity {vor[i, j]*1e5:.1f}e-5 /s at {lat[i]} N, {abs(lon[j]-360)} W; "
          f"divergence there {div[i, j]*1e5:+.1f}e-5 /s")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

"""Minimal sanity check: import the package and run every function once
on the demo data. Run this after any change, before tagging a new
release -- if this script errors, don't cut a new version tag yet.

Run with:  python smoke_test.py
"""

import qi_course as qc


def main():
    print(f"qi_course version: {qc.__version__}")

    df = qc.load_demo_harvey_precip()
    assert len(df) == 120, "expected 120 hourly readings"
    print(f"Loaded demo data: {len(df)} hourly readings")

    cumulative = qc.trapezoid_integral(df["hour"], df["rain_mm_per_hr"])
    total_mm = cumulative[-1]
    print(f"Total accumulated rainfall (trapezoid rule): {total_mm:.1f} mm")

    rate_of_change = qc.finite_difference(df["hour"], df["rain_mm_per_hr"])
    print(f"Max rate of change: {rate_of_change.max():.2f} mm/hr per hour")

    ax = qc.quick_timeseries_plot(
        df["hour"],
        df["rain_mm_per_hr"],
        title="Demo rainfall (synthetic)",
        xlabel="Hour",
        ylabel="Rain (mm/hr)",
    )
    fig = ax.get_figure()
    fig.savefig("smoke_test_plot.png")
    print("Saved smoke_test_plot.png -- open it and check it looks sane.")

    print("\n--- Lab 2 checks (temperature / Gaussian distribution) ---")

    cities = qc.list_demo_cities()
    print(f"Demo cities available: {cities}")
    assert "Tucson" in cities

    temps_df = qc.load_demo_july_highs(city="Tucson", n_years=100, seed=0)
    assert len(temps_df) == 100 * 31, "expected 100 years x 31 days"
    print(f"Loaded Tucson July highs: {len(temps_df)} daily readings")

    stats = qc.descriptive_stats(temps_df["high_temp_c"])
    print(
        f"Tucson July high temp -- mean: {stats['mean']:.1f} C, "
        f"std: {stats['std']:.2f} C, skewness: {stats['skewness']:.2f}"
    )

    grid, pdf, params = qc.fit_normal_pdf(temps_df["high_temp_c"])
    print(f"Fitted normal params: mean={params['mean']:.1f}, std={params['std']:.2f}")

    ax2 = qc.histogram_with_fit(
        temps_df["high_temp_c"],
        grid,
        pdf,
        title="Tucson July daily highs (synthetic) vs. fitted normal",
        xlabel="High temperature (C)",
    )
    fig2 = ax2.get_figure()
    fig2.savefig("smoke_test_lab2_plot.png")
    print("Saved smoke_test_lab2_plot.png -- open it and check it looks sane.")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

"""One-time builder for the real-data files used by qi_course Labs 2, 3 and 6.

Run this once (in Colab is easiest). It downloads public NOAA data, applies
basic quality control, and writes small, compact files into a folder called
qi_data/ that then ship inside the qi_course package.

Sources
  GHCN-Daily (NOAA NCEI): daily station temperature and precipitation.
  NCEP/NCAR Reanalysis 1 (NOAA PSL): daily-mean gridded winds and heights.
"""

import io
import os

import numpy as np
import pandas as pd
import requests

GHCN = "https://www.ncei.noaa.gov/pub/data/ghcn/daily"

# (name fragment as it appears in GHCN station names, state). The first match
# with a 100+ year record is used for each. Not every city will qualify.
CITY_CANDIDATES = [
    ("TUCSON", "AZ"), ("PHOENIX", "AZ"), ("CNTRL PK", "NY"), ("CENTRAL PARK", "NY"),
    ("MINNEAPOLIS", "MN"), ("SEATTLE", "WA"), ("SALT LAKE CITY", "UT"),
    ("ALBUQUERQUE", "NM"), ("DENVER", "CO"), ("LOS ANGELES", "CA"),
    ("SAN DIEGO", "CA"), ("BOSTON", "MA"), ("CHICAGO", "IL"),
    ("PHILADELPHIA", "PA"), ("ST LOUIS", "MO"), ("NEW ORLEANS", "LA"),
    ("MIAMI", "FL"), ("HOUSTON", "TX"), ("ATLANTA", "GA"), ("HONOLULU", "HI"),
    ("BISMARCK", "ND"), ("FAIRBANKS", "AK"), ("PORTLAND", "OR"),
    ("SAN FRANCISCO", "CA"), ("DES MOINES", "IA"), ("LINCOLN", "NE"),
]

QC_START, QC_END = 1926, 2025   # window used to judge "100 years of data"
MIN_COMPLETENESS = 0.90         # fraction of days present in that window


# ---------------------------------------------------------------- parsing
def parse_stations(text):
    """ghcnd-stations.txt is fixed-width: id, lat, lon, elev, state, name."""
    rows = []
    for line in text.splitlines():
        if len(line) < 41:
            continue
        rows.append({
            "id": line[0:11].strip(),
            "lat": float(line[12:20]),
            "lon": float(line[21:30]),
            "state": line[38:40].strip(),
            "name": line[41:71].strip(),
        })
    return pd.DataFrame(rows)


def parse_inventory(text):
    """ghcnd-inventory.txt: one row per station and element with first/last year."""
    rows = []
    for line in text.splitlines():
        if len(line) < 45:
            continue
        rows.append({
            "id": line[0:11].strip(),
            "element": line[31:35].strip(),
            "first_year": int(line[36:40]),
            "last_year": int(line[41:45]),
        })
    return pd.DataFrame(rows)


def pick_stations(stations, inventory, candidates=CITY_CANDIDATES,
                  max_first_year=QC_START, min_last_year=2024):
    """For each candidate city, choose the station with the earliest start date
    that records both TMAX and PRCP through the present."""
    need = inventory[inventory["element"].isin(["TMAX", "PRCP"])]
    span = need.groupby(["id", "element"]).agg(
        first_year=("first_year", "min"), last_year=("last_year", "max")).reset_index()
    ok = span[(span["first_year"] <= max_first_year) & (span["last_year"] >= min_last_year)]
    counts = ok.groupby("id")["element"].nunique()
    both = set(counts[counts == 2].index)
    first = ok.groupby("id")["first_year"].max()   # later of the two starts

    chosen, missing = [], []
    for fragment, state in candidates:
        hit = stations[(stations["state"] == state)
                       & stations["name"].str.contains(fragment, regex=False)
                       & stations["id"].isin(both)].copy()
        if hit.empty:
            missing.append((fragment, state))
            continue
        hit["first_year"] = hit["id"].map(first)
        hit["is_usw"] = hit["id"].str.startswith("USW")
        hit = hit.sort_values(["is_usw", "first_year"], ascending=[False, True])
        row = hit.iloc[0]
        if row["id"] not in [c["id"] for c in chosen]:
            chosen.append(row.to_dict())
    return pd.DataFrame(chosen), missing


# --------------------------------------------------------------- station data
def parse_station_csv(raw_bytes):
    """Turn one GHCN-Daily by_station file into a tidy daily table.

    Values are stored in tenths of a degree C or tenths of a mm. Any value
    carrying a quality-control flag is discarded, not repaired.
    """
    cols = ["id", "date", "element", "value", "mflag", "qflag", "sflag", "obstime"]
    df = pd.read_csv(io.BytesIO(raw_bytes), compression="gzip", header=None,
                     names=cols, usecols=range(8),
                     dtype={"date": str, "mflag": str, "qflag": str, "sflag": str,
                            "obstime": str})
    df = df[df["element"].isin(["TMAX", "TMIN", "PRCP"])]
    df = df[df["qflag"].isna()]
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    wide = df.pivot_table(index="date", columns="element", values="value", aggfunc="first")
    wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max(), freq="D"))
    wide.index.name = "date"
    wide = wide.reindex(columns=["TMAX", "TMIN", "PRCP"])   # keep all three, even if empty
    out = pd.DataFrame({
        "tmax_c": wide["TMAX"] / 10.0,
        "tmin_c": wide["TMIN"] / 10.0,
        "prcp_mm": wide["PRCP"] / 10.0,
    })
    return out


def completeness(daily, start=QC_START, end=QC_END):
    win = daily.loc[f"{start}-01-01":f"{end}-12-31"]
    if len(win) == 0:
        return 0.0, 0.0
    return float(win["tmax_c"].notna().mean()), float(win["prcp_mm"].notna().mean())


def build_stations(out_dir, max_stations=14, session=None):
    """Download and QC candidate stations; write daily files and stations.csv."""
    get = (session or requests).get
    os.makedirs(os.path.join(out_dir, "daily"), exist_ok=True)

    stations = parse_stations(get(f"{GHCN}/ghcnd-stations.txt", timeout=180).text)
    inventory = parse_inventory(get(f"{GHCN}/ghcnd-inventory.txt", timeout=180).text)
    picks, missing = pick_stations(stations, inventory)
    print(f"{len(picks)} candidate stations; no 100-year station found for: {missing}")

    kept = []
    for _, row in picks.iterrows():
        if len(kept) >= max_stations:
            break
        url = f"{GHCN}/by_station/{row['id']}.csv.gz"
        try:
            r = get(url, timeout=300)
            r.raise_for_status()
            daily = parse_station_csv(r.content)
        except Exception as err:       # keep going; report at the end
            print(f"  skipped {row['id']} {row['name']}: {err}")
            continue
        c_t, c_p = completeness(daily)
        print(f"  {row['id']} {row['name']:<28s} {row['state']}  "
              f"TMAX {c_t:5.1%}  PRCP {c_p:5.1%}  "
              f"{daily.index.min().year}-{daily.index.max().year}")
        if c_t < MIN_COMPLETENESS or c_p < MIN_COMPLETENESS:
            print("     -> dropped: too many missing days")
            continue
        daily.round(1).to_csv(os.path.join(out_dir, "daily", f"{row['id']}.csv.gz"),
                              compression="gzip")
        kept.append({
            "id": row["id"], "name": row["name"], "state": row["state"],
            "lat": row["lat"], "lon": row["lon"],
            "first_date": str(daily.index.min().date()),
            "last_date": str(daily.index.max().date()),
            "pct_tmax": round(100 * c_t, 1), "pct_prcp": round(100 * c_p, 1),
        })
    pd.DataFrame(kept).to_csv(os.path.join(out_dir, "stations.csv"), index=False)
    print(f"\nWrote {len(kept)} stations to {out_dir}/")
    return pd.DataFrame(kept)


# ------------------------------------------------------------ reanalysis
DATE_CASES = {
    "1993-03-13": "Storm of the Century (deep winter cyclone, eastern US)",
    "2017-08-27": "Hurricane Harvey, two days after landfall",
}

URL_TEMPLATES = [
    "https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/{var}.{year}.nc",
    "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.dailyavgs/pressure/{var}.{year}.nc",
]


def _open_var(var, year, templates):
    import xarray as xr
    last_err = None
    for t in templates:
        try:
            if t.startswith("http") and "dodsC" not in t:
                path = f"{var}.{year}.nc"
                if not os.path.exists(path):
                    r = requests.get(t.format(var=var, year=year), timeout=600)
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        f.write(r.content)
                return xr.open_dataset(path)
            return xr.open_dataset(t.format(var=var, year=year))
        except Exception as err:
            last_err = err
    raise RuntimeError(f"could not open {var} {year}: {last_err}")


def extract_case(date, level=850, lat_range=(15, 65), lon_range=(-140, -50),
                 templates=URL_TEMPLATES):
    """Return u, v, height on one pressure level for one day, as numpy arrays."""
    year = int(date[:4])
    lon_lo, lon_hi = lon_range[0] % 360, lon_range[1] % 360
    out = {}
    for var, key in [("uwnd", "u"), ("vwnd", "v"), ("hgt", "z")]:
        ds = _open_var(var, year, templates)
        da = ds[var].sel(time=date, level=level)
        da = da.sel(lat=slice(lat_range[1], lat_range[0]),
                    lon=slice(lon_lo, lon_hi))
        out[key] = np.asarray(da.values, dtype="float32")
        out["lat"] = np.asarray(da["lat"].values, dtype="float32")
        out["lon"] = np.asarray(da["lon"].values, dtype="float32")
        ds.close()
    return out


def build_reanalysis(out_dir, cases=DATE_CASES, templates=URL_TEMPLATES, **kw):
    os.makedirs(out_dir, exist_ok=True)
    for date, label in cases.items():
        c = extract_case(date, templates=templates, **kw)
        np.savez_compressed(os.path.join(out_dir, f"winds_{date}.npz"),
                            lat=c["lat"], lon=c["lon"], u=c["u"], v=c["v"], z=c["z"])
        print(f"  {date}  {label}: grid {c['u'].shape}, "
              f"u range {c['u'].min():.1f}..{c['u'].max():.1f} m/s")

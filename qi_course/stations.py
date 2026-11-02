"""Real station records (NOAA GHCN-Daily) for Labs 2, 3 and 4.

Two ways to get a station:

  1. Bundled stations. A small menu of long-record stations ships inside
     this package, so the lab works with no extra downloads:
         qc.list_stations()
         df = qc.load_station("New Orleans")

  2. Any other station, downloaded live from NOAA when you run the cell:
         qc.find_stations(lat=32.2, lon=-110.9)      # search near a place
         df = qc.load_station("USW00023160")         # load by station ID

Both routes return the same table, with one row per calendar day and the
columns tmax_c, tmin_c (degrees C) and prcp_mm (millimeters). A missing
value is NaN, never zero. Values that failed NOAA's own quality checks have
already been removed (not repaired), so a gap means "no trustworthy value".
"""

import io
import os

import numpy as np
import pandas as pd

GHCN_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily"
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

_live_cache = {}   # station files and inventories downloaded this session

# NOAA station names are abbreviated ("HEADWORKS PORTLAND WTR B"). Friendlier
# labels for the bundled stations; any station not listed here falls back to
# its NOAA name in title case.
_LABELS = {
    "USW00093134": "Los Angeles (downtown)",
    "USW00012930": "New Orleans (Audubon)",
    "USC00353770": "Portland, OR (Bull Run headworks)",
    "USW00023272": "San Francisco (downtown)",
}


# ------------------------------------------------------------- bundled menu
def list_stations():
    """Return a table of the bundled stations (id, name, state, lat, lon,
    first and last date, the percent of days present, and a friendly label)."""
    table = pd.read_csv(os.path.join(_DATA_DIR, "stations.csv"))
    table["label"] = [_LABELS.get(i, n.title()) for i, n in zip(table["id"], table["name"])]
    return table


def _resolve_bundled(key):
    table = list_stations()
    key = str(key).strip()
    exact = table[table["id"] == key]
    if len(exact):
        return exact.iloc[0]
    hits = table[table["name"].str.contains(key, case=False, regex=False)
                 | table["label"].str.contains(key, case=False, regex=False)]
    if len(hits) == 1:
        return hits.iloc[0]
    if len(hits) > 1:
        raise ValueError(
            f"'{key}' matches several stations: {list(hits['label'])}. "
            "Use a longer piece of the name, or the station id."
        )
    return None


def load_station(key):
    """Load one station's daily record.

    Parameters
    ----------
    key : str
        A piece of a bundled station's name (for example "New Orleans"),
        or a GHCN station id (for example "USW00023160"). An id that is
        not in the bundled menu is downloaded from NOAA, which needs an
        internet connection and can take a few seconds.

    Returns
    -------
    pandas.DataFrame
        Indexed by date, one row per day, columns tmax_c, tmin_c, prcp_mm.
        The station's name and id are stored in `df.attrs`.
    """
    row = _resolve_bundled(key)
    if row is not None:
        path = os.path.join(_DATA_DIR, "daily", f"{row['id']}.csv.gz")
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.attrs.update({"id": row["id"], "name": row["name"], "label": row["label"],
                         "state": row["state"]})
        return df
    key = str(key).strip()
    if len(key) == 11 and key.startswith("US"):
        return _load_live(key)
    raise ValueError(
        f"'{key}' is not a bundled station. Run qc.list_stations() to see the "
        "menu, or qc.find_stations(lat, lon) to search NOAA for a station id."
    )


# ----------------------------------------------------------- live (NOAA) path
def parse_station_csv(raw_bytes):
    """Turn one raw GHCN-Daily by_station file into the tidy daily table.

    Values arrive in tenths of a degree C or tenths of a millimeter. Any
    value carrying a quality-control flag is discarded.
    """
    cols = ["id", "date", "element", "value", "mflag", "qflag", "sflag", "obstime"]
    df = pd.read_csv(io.BytesIO(raw_bytes), compression="gzip", header=None,
                     names=cols, usecols=range(8),
                     dtype={"date": str, "mflag": str, "qflag": str,
                            "sflag": str, "obstime": str})
    df = df[df["element"].isin(["TMAX", "TMIN", "PRCP"])]
    df = df[df["qflag"].isna()].copy()
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    wide = df.pivot_table(index="date", columns="element", values="value",
                          aggfunc="first")
    wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max(), freq="D"))
    wide.index.name = "date"
    wide = wide.reindex(columns=["TMAX", "TMIN", "PRCP"])
    return pd.DataFrame({
        "tmax_c": wide["TMAX"] / 10.0,
        "tmin_c": wide["TMIN"] / 10.0,
        "prcp_mm": wide["PRCP"] / 10.0,
    }).round(1)


def _http_get(url, timeout):
    import requests
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def _load_live(station_id):
    if station_id in _live_cache:
        return _live_cache[station_id].copy()
    try:
        raw = _http_get(f"{GHCN_URL}/by_station/{station_id}.csv.gz", 300).content
    except Exception as err:
        raise RuntimeError(
            f"Could not download station {station_id} from NOAA ({err}). "
            "Check the id and your internet connection, or try again in a minute. "
            "If NOAA is down, use one of the bundled stations (qc.list_stations())."
        ) from err
    df = parse_station_csv(raw)
    df.attrs.update({"id": station_id, "name": station_id, "label": station_id, "state": ""})
    _live_cache[station_id] = df
    return df.copy()


def find_stations(lat, lon, n=8, min_years=100, max_km=300):
    """Search NOAA's station list for long-record stations near a place.

    Parameters
    ----------
    lat, lon : float
        Latitude (north positive) and longitude (west negative) of your city.
    n : int
        How many stations to list.
    min_years : int
        Minimum span between a station's first and last temperature record.
        Note this is the span, not the number of days actually present;
        check coverage with qc.station_coverage after loading.
    max_km : float
        Only stations within this distance are listed.

    Returns
    -------
    pandas.DataFrame
        id, name, state, distance_km, first_year, last_year, years.

    The first call downloads NOAA's station list and inventory (tens of MB)
    and may take a minute; later calls in the same session reuse them.
    """
    if "inventory" not in _live_cache:
        stations_text = _http_get(f"{GHCN_URL}/ghcnd-stations.txt", 300).text
        inventory_text = _http_get(f"{GHCN_URL}/ghcnd-inventory.txt", 600).text
        _live_cache["stations"] = _parse_stations(stations_text)
        _live_cache["inventory"] = _parse_inventory(inventory_text)
    stations, inventory = _live_cache["stations"], _live_cache["inventory"]

    need = inventory[inventory["element"].isin(["TMAX", "PRCP"])]
    span = need.groupby(["id", "element"]).agg(
        first_year=("first_year", "min"), last_year=("last_year", "max")).reset_index()
    both = span.groupby("id").agg(
        first_year=("first_year", "max"), last_year=("last_year", "min"),
        n_elements=("element", "nunique")).reset_index()
    both = both[both["n_elements"] == 2]
    both["years"] = both["last_year"] - both["first_year"] + 1
    table = stations.merge(both, on="id")
    table["distance_km"] = _distance_km(lat, lon, table["lat"].values, table["lon"].values)
    table = table[(table["years"] >= min_years) & (table["distance_km"] <= max_km)]
    table = table.sort_values("distance_km").head(n)
    return table[["id", "name", "state", "distance_km", "first_year", "last_year",
                  "years"]].round({"distance_km": 0}).reset_index(drop=True)


def _distance_km(lat0, lon0, lats, lons):
    """Great-circle distance from one point to arrays of points."""
    r = 6371.0
    p0, p1 = np.deg2rad(lat0), np.deg2rad(lats)
    dlon = np.deg2rad(lons - lon0)
    a = np.sin((p1 - p0) / 2) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def _parse_stations(text):
    rows = []
    for line in text.splitlines():
        if len(line) < 41:
            continue
        rows.append({"id": line[0:11].strip(), "lat": float(line[12:20]),
                     "lon": float(line[21:30]), "state": line[38:40].strip(),
                     "name": line[41:71].strip()})
    return pd.DataFrame(rows)


def _parse_inventory(text):
    rows = []
    for line in text.splitlines():
        if len(line) < 45:
            continue
        rows.append({"id": line[0:11].strip(), "element": line[31:35].strip(),
                     "first_year": int(line[36:40]), "last_year": int(line[41:45])})
    return pd.DataFrame(rows)


# ----------------------------------------------------------- using a station
def station_coverage(df):
    """Report how complete a station's record is.

    Returns a dict with the first and last year, the percent of days present
    for each variable, and the list of years with more than 10 percent of
    daily maximum temperatures missing. Use it before trusting a record.
    """
    out = {
        "first_year": int(df.index.min().year),
        "last_year": int(df.index.max().year),
        "pct_present": {c: round(100 * float(df[c].notna().mean()), 1)
                        for c in ["tmax_c", "tmin_c", "prcp_mm"]},
    }
    missing = df["tmax_c"].isna().groupby(df.index.year).mean()
    out["years_with_gaps"] = [int(y) for y in missing[missing > 0.10].index]
    return out


def month_values(df, column, month, first_year=None, last_year=None):
    """All values of one column during one calendar month, missing days dropped.

    Example: July daily highs for every year on record:
        qc.month_values(df, "tmax_c", 7)
    """
    sel = df[df.index.month == month]
    if first_year is not None:
        sel = sel[sel.index.year >= first_year]
    if last_year is not None:
        sel = sel[sel.index.year <= last_year]
    return sel[column].dropna()


def annual_totals(df, column="prcp_mm", min_fraction=0.95):
    """Total of `column` for each calendar year, using only years in which at
    least `min_fraction` of the days are present (a year with missing months
    would give a falsely small total)."""
    by_year = df[column].groupby(df.index.year)
    totals = by_year.sum(min_count=1)
    present = by_year.apply(lambda s: s.notna().mean())
    return totals[present >= min_fraction]

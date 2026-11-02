"""Gridded wind and height fields for Lab 6 (gradient, divergence, curl).

The data are daily-mean 850 hPa winds and geopotential heights from NOAA's
NCEP/NCAR Reanalysis 1, on a 2.5 degree grid over North America. A
reanalysis blends observations with a weather model to give a complete,
regular map of the atmosphere, which is what lets us take derivatives.

Grid layout: every array has shape (n_lat, n_lon). `lat` runs from north to
south, `lon` from west to east (degrees east, so 250 means 110 degrees W).
"""

import os

import numpy as np

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "reanalysis")

EARTH_RADIUS_M = 6.371e6
GRAVITY = 9.80665
EARTH_ROTATION = 7.2921e-5   # radians per second

CASES = {
    "1993-03-13": "Storm of the Century: a deep winter cyclone over the southeastern US",
    "2017-08-27": "Hurricane Harvey, two days after landfall on the Texas coast",
}

# Landmarks (latitude, longitude in degrees east) so a map can be read.
PLACES = {
    "Tucson": (32.2, -110.9 + 360), "Houston": (29.8, -95.4 + 360),
    "Atlanta": (33.7, -84.4 + 360), "Chicago": (41.9, -87.6 + 360),
    "New York": (40.7, -74.0 + 360), "Denver": (39.7, -105.0 + 360),
    "Seattle": (47.6, -122.3 + 360), "Los Angeles": (34.1, -118.2 + 360),
}


def list_cases():
    """Return the available weather cases as {date: description}."""
    return dict(CASES)


def load_case(date="1993-03-13"):
    """Load one day of 850 hPa winds and heights.

    Returns
    -------
    dict with
        lat, lon : 1D arrays (degrees north, degrees east)
        u, v     : eastward and northward wind (m/s), shape (n_lat, n_lon)
        z        : geopotential height of the 850 hPa surface (m)
        date, description
    """
    path = os.path.join(_DATA_DIR, f"winds_{date}.npz")
    if not os.path.exists(path):
        raise ValueError(f"No case for '{date}'. Available: {list(CASES)}")
    f = np.load(path)
    return {"lat": f["lat"].astype(float), "lon": f["lon"].astype(float),
            "u": f["u"].astype(float), "v": f["v"].astype(float),
            "z": f["z"].astype(float), "date": date,
            "description": CASES.get(date, "")}


def grid_spacing_m(lat, lon):
    """Distance between neighboring grid points, in meters.

    Returns (dx, dy), each shaped like the grid. Going east, one degree of
    longitude covers less ground the farther you are from the equator, by
    a factor cos(latitude); going north, one degree of latitude is always
    the same distance. dy is negative because the latitudes are listed from
    north to south, so one step along a column is a step southward.
    """
    lat_rad, lon_rad = np.deg2rad(lat), np.deg2rad(lon)
    dx = EARTH_RADIUS_M * np.cos(lat_rad)[:, None] * np.gradient(lon_rad)[None, :]
    dy = EARTH_RADIUS_M * np.gradient(lat_rad)[:, None] * np.ones((1, len(lon)))
    return dx, dy


def gradient(field, lat, lon):
    """Rate of change of a field per meter, toward the east and toward the north.

    Returns (d_dx, d_dy). Each is a centered difference at interior points
    (value on the far side minus value on the near side, divided by the
    distance between them), the same idea as Lab 1's finite_difference.
    """
    dx, dy = grid_spacing_m(lat, lon)
    d_dx = np.gradient(field, axis=1) / dx
    # lat is listed north to south, so np.gradient along axis 0 gives the
    # change per step southward; dividing by the (negative) dy flips it so
    # the result is the change per meter northward.
    d_dy = np.gradient(field, axis=0) / dy
    return d_dx, d_dy


def divergence(u, v, lat, lon):
    """Horizontal divergence du/dx + dv/dy, in 1/s.

    Positive where air is spreading out, negative where it is converging.
    Uses local east-west and north-south distances; the small extra terms
    that come from the curvature of the sphere are left out (about 10
    percent effect at these latitudes), which is fine for building intuition.
    """
    du_dx, _ = gradient(u, lat, lon)
    _, dv_dy = gradient(v, lat, lon)
    return du_dx + dv_dy


def vorticity(u, v, lat, lon):
    """Vertical component of the curl, dv/dx - du/dy, in 1/s.

    Positive for counterclockwise (cyclonic, in the Northern Hemisphere)
    rotation, negative for clockwise rotation. Same curvature caveat as
    `divergence`.
    """
    dv_dx, _ = gradient(v, lat, lon)
    _, du_dy = gradient(u, lat, lon)
    return dv_dx - du_dy


def geostrophic_wind(z, lat, lon):
    """Wind implied by the height gradient alone, if pressure force and
    Coriolis force balanced exactly.

        u_g = -(g/f) dz/dy        v_g = (g/f) dz/dx

    where f = 2 * (Earth's rotation rate) * sin(latitude). It blows
    parallel to the height contours with low heights on its left (Northern
    Hemisphere). Not meaningful near the equator, where f approaches zero.
    """
    f = 2 * EARTH_ROTATION * np.sin(np.deg2rad(lat))[:, None]
    dz_dx, dz_dy = gradient(z, lat, lon)
    return -(GRAVITY / f) * dz_dy, (GRAVITY / f) * dz_dx


def plot_field_map(lat, lon, field, u=None, v=None, contours=None,
                   title="", label="", symmetric=True, ax=None,
                   places=("Houston", "Atlanta", "Chicago", "Denver"), skip=2):
    """Draw a shaded map of `field`, optionally with wind arrows and contours.

    symmetric=True centers the color scale on zero (blue negative, red
    positive), which is what you want for divergence and vorticity.
    `contours` is a second field (for example height) drawn as thin lines.
    Arrow length is proportional to wind speed. `places` marks landmarks.
    """
    import matplotlib.pyplot as plt
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5.2))
    inner = np.abs(field[2:-2, 2:-2])
    if symmetric:
        limit = np.nanmax(inner)
        levels = np.linspace(-limit, limit, 21)
        cmap = "RdBu_r"
    else:
        levels = 21
        cmap = "viridis"
    shade = ax.contourf(lon - 360, lat, field, levels=levels, cmap=cmap, extend="both")
    cbar = plt.colorbar(shade, ax=ax, shrink=0.85)
    cbar.set_label(label)
    if contours is not None:
        ax.contour(lon - 360, lat, contours, colors="black", linewidths=0.6, levels=12)
    if u is not None and v is not None:
        ax.quiver((lon - 360)[::skip], lat[::skip], u[::skip, ::skip], v[::skip, ::skip],
                  scale=300, width=0.003, color="black")
    for name in places or []:
        plat, plon = PLACES[name]
        ax.plot(plon - 360, plat, marker="o", color="gold", markeredgecolor="black",
                markersize=6)
        ax.annotate(name, (plon - 360, plat), xytext=(4, 4), textcoords="offset points",
                    fontsize=8)
    ax.set_xlabel("Longitude (negative = west)")
    ax.set_ylabel("Latitude (degrees north)")
    ax.set_title(title)
    return ax

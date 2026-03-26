# Copyright 2024-, European Centre for Medium Range Weather Forecasts.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cartopy.crs as ccrs
import numpy as np


def nnshow(lons, lats, data, ax, nx=1000, ny=1000, style=None, **kwargs):
    """
    Plot an ORCA curvilinear grid by nearest-neighbour pixel sampling.

    ORCA grids (eORCA025, ORCA1, …) use a tripolar curvilinear coordinate
    system: longitude and latitude are 2-D arrays with no simple analytic row/
    column lookup.  This function builds a KD-tree over the source grid points
    and, for each pixel in an nx×ny output image, finds the nearest grid cell
    and assigns its value.

    Parameters
    ----------
    lons : array-like
        2-D (or 1-D flattened) array of grid-point longitudes (degrees).
    lats : array-like
        2-D (or 1-D flattened) array of grid-point latitudes (degrees).
    data : array-like
        Array of values, one per grid point (same shape as lons/lats, or 1-D).
    ax : cartopy.mpl.geoaxes.GeoAxes
        Axes to plot on.
    nx : int, optional
        Horizontal pixel resolution of the output image (default 1000).
    ny : int, optional
        Vertical pixel resolution of the output image (default 1000).
    style : Style, optional
        earthkit-plots Style object; if provided its pcolormesh kwargs are applied.
    **kwargs
        Additional keyword arguments forwarded to :func:`matplotlib.axes.Axes.imshow`.
    """
    from scipy.spatial import KDTree

    kwargs.pop("transform_first", None)
    kwargs.pop("transform", None)

    lons = np.asarray(lons, dtype=float).ravel()
    lats = np.asarray(lats, dtype=float).ravel()
    data = np.asarray(data, dtype=float).ravel()

    # Build a KD-tree in 3-D Cartesian space to avoid longitude-wrap issues.
    src_xyz = _lonlat_to_xyz(lons, lats)
    tree = KDTree(src_xyz)

    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    if xlims == (0.0, 1.0) and ylims == (0.0, 1.0):
        ax.set_global()
        xlims = ax.get_xlim()
        ylims = ax.get_ylim()

    dx = (xlims[1] - xlims[0]) / nx
    dy = (ylims[1] - ylims[0]) / ny
    xvals = np.linspace(xlims[0] + dx / 2, xlims[1] - dx / 2, nx)
    yvals = np.linspace(ylims[0] + dy / 2, ylims[1] - dy / 2, ny)
    xvals2, yvals2 = np.meshgrid(xvals, yvals)

    # Back-transform pixel centres from the map projection to lon/lat.
    latlon = ccrs.PlateCarree().transform_points(
        ax.projection, xvals2, yvals2, np.zeros_like(xvals2)
    )
    valid = np.all(np.isfinite(latlon), axis=-1)

    pixel_lons = latlon[valid, 0]
    pixel_lats = latlon[valid, 1]

    # Query the KD-tree for each valid pixel.
    pix_xyz = _lonlat_to_xyz(pixel_lons, pixel_lats)
    _, idx = tree.query(pix_xyz, workers=-1)

    res = np.full(latlon.shape[:-1], np.nan, dtype=float)
    res[valid] = data[idx]

    if style is not None:
        kwargs = {**kwargs, **style.to_pcolormesh_kwargs(res)}

    return ax.imshow(res, extent=xlims + ylims, origin="lower", **kwargs)


def _lonlat_to_xyz(lons, lats):
    """Convert longitude/latitude (degrees) to unit-sphere Cartesian coordinates."""
    lon_r = np.deg2rad(lons)
    lat_r = np.deg2rad(lats)
    cos_lat = np.cos(lat_r)
    return np.column_stack([cos_lat * np.cos(lon_r), cos_lat * np.sin(lon_r), np.sin(lat_r)])

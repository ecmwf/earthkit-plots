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
    Plot an octahedral reduced Gaussian grid by pixel sampling.

    For each pixel in an nx-by-ny image covering the current axes extent, the
    containing grid cell is found analytically: the latitude row is determined
    from the Gaussian latitude boundaries (midpoints between adjacent rows) and
    the longitude column from the regular spacing within that row.  The pixel is
    then coloured with the corresponding data value.

    This exactly replicates the rectangular cells produced by the old
    PolyCollection approach, but at a cost proportional to the output resolution
    (nx × ny) rather than the number of grid points, making it far cheaper for
    high-resolution grids.

    Parameters
    ----------
    lons : array-like
        1D array of grid-point longitudes (degrees, any convention).
    lats : array-like
        1D array of grid-point latitudes (degrees).
    data : array-like
        1D array of values, one per grid point.
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
    kwargs.pop("transform_first", None)
    kwargs.pop("transform", None)

    lons = np.asarray(lons, dtype=float)
    lats = np.asarray(lats, dtype=float)
    data = np.asarray(data, dtype=float)

    # ---------------------------------------------------------------
    # Build the row lookup structure from the 1D point arrays.
    #
    # The octahedral reduced Gaussian grid has a fixed set of Gaussian
    # latitudes.  Points are ordered by row (pole-to-pole or equator-
    # to-pole depending on the GRIB scan mode).  We reconstruct the
    # row structure: for each unique latitude value, record the start
    # index in the flat array, the number of points, and the longitude
    # spacing for that row.
    # ---------------------------------------------------------------
    unique_lats, row_starts, row_counts = _build_row_index(lats)

    lat_bounds = _lat_boundaries(unique_lats)
    
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

    latlon = ccrs.PlateCarree().transform_points(
        ax.projection, xvals2, yvals2, np.zeros_like(xvals2)
    )
    valid = np.all(np.isfinite(latlon), axis=-1)

    pixel_lons = latlon[valid, 0]  # [-180, 180]
    pixel_lats = latlon[valid, 1]  # [-90, 90]

    # ---------------------------------------------------------------
    # For each valid pixel, find the row index via searchsorted on
    # the latitude boundaries, then compute the column index from the
    # longitude spacing of that row.
    # ---------------------------------------------------------------
    # lat_bounds is sorted ascending; rows go from south to north (or
    # north to south — we handle both via sorting below).
    if lat_bounds[0] > lat_bounds[-1]:
        # Descending: flip for searchsorted, then invert result
        row_idx = len(unique_lats) - np.searchsorted(
            lat_bounds[::-1], pixel_lats, side="right"
        )
    else:
        # Ascending
        row_idx = np.searchsorted(lat_bounds, pixel_lats, side="right") - 1

    # Clamp to valid row range
    row_idx = np.clip(row_idx, 0, len(unique_lats) - 1)

    # Within each row, points are evenly spaced and are cell *centres*.
    # The Gaussian grid standard places the first point of every row at
    # lon=0, so cell edges are at -d_lon/2, d_lon/2, 3*d_lon/2, ...
    # We reconstruct the column index by expressing the pixel longitude
    # relative to lon=0 in [0,360) space and rounding to the nearest point.
    #
    # Use the actual spacing between the first two stored lons of each row
    # rather than 360/npts: the stored count may be a regional subset, but
    # the spacing always reflects the true full-row resolution.
    # Compute per-row d_lon from the actual lon spacing of each row's first pair.
    row_d_lons = np.array(
        [
            abs(lons[start + 1] - lons[start]) if count > 1 else 360.0 / count
            for start, count in zip(row_starts, row_counts)
        ]
    )
    d_lon = row_d_lons[row_idx]  # cell width for each pixel's row

    first_lons = lons[row_starts[row_idx]]  # first stored lon of each pixel's row
    npts_full = np.round(360.0 / d_lon).astype(int)

    # Difference in the same periodic space, wrapped to (-180, 180]
    delta = pixel_lons - first_lons
    delta = (delta + 180.0) % 360.0 - 180.0

    # floor(delta/d_lon + 0.5) = round-half-up to nearest column
    col_idx = np.floor(delta / d_lon + 0.5).astype(int) % npts_full

    flat_idx = row_starts[row_idx] + col_idx

    res = np.full(latlon.shape[:-1], np.nan, dtype=float)
    res[valid] = data[flat_idx]

    if style is not None:
        kwargs = {**kwargs, **style.to_pcolormesh_kwargs(res)}

    return ax.imshow(res, extent=xlims + ylims, origin="lower", **kwargs)


def _build_row_index(lats):
    """
    Given a 1-D array of point latitudes (one entry per grid point, grouped by
    row), return the unique latitude values, the start index of each row in the
    flat array, and the number of points in each row.
    """
    # Detect row boundaries: a new row starts whenever the latitude changes.
    changes = np.concatenate(([True], lats[1:] != lats[:-1]))
    row_starts = np.where(changes)[0]
    unique_lats = lats[row_starts]
    row_counts = np.diff(np.append(row_starts, len(lats)))
    return unique_lats, row_starts, row_counts


def _lat_boundaries(unique_lats):
    """
    Compute latitude cell boundaries as midpoints between adjacent row
    latitudes, extrapolated symmetrically at both poles.
    """
    mid = (unique_lats[:-1] + unique_lats[1:]) / 2.0
    first = 2.0 * unique_lats[0] - mid[0]
    last = 2.0 * unique_lats[-1] - mid[-1]
    return np.concatenate(([first], mid, [last]))

# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

from typing import Any

import numpy as np

from earthkit.plots.schemas import schema
from earthkit.plots.sources.context import PlotContext


def apply_regrid(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    gridspec: Any,
    context: PlotContext,
    target_resolution: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply regridding to data with special grid structure.

    This centralized regridding function works for any source type that
    provides a gridspec (HEALPix, Reduced Gaussian Grid, etc.).

    Parameters
    ----------
    x : np.ndarray
        Current x coordinates (longitude).
    y : np.ndarray
        Current y coordinates (latitude).
    z : np.ndarray
        Field values to regrid.
    gridspec : GridSpec or dict
        Grid specification from source.
    context : PlotContext
        Plot context (only regrid for geographic plots).
    target_resolution : float, optional
        Target grid resolution in degrees. If None, uses schema default.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Regridded (x, y, z) coordinates.

    Raises
    ------
    ImportError
        If earthkit-regrid is not available.
    """
    # Only regrid geographic plots
    if not context.is_geographic:
        return x, y, z

    # Check if regridding is available
    from earthkit.plots.geo.regrid import can_regrid

    if not can_regrid():
        raise ImportError(
            f"earthkit-regrid is required for plotting data on a "
            f"'{gridspec.__class__.__name__}' grid. "
            "Please install: pip install earthkit-regrid"
        )

    # Get target resolution
    if target_resolution is None:
        target_resolution = schema.interpolate_target_resolution

    # Generate target regular lat/lon grid
    x_new, y_new = _generate_latlon_grid(target_resolution)

    # Import regridding function
    from earthkit.plots.geo.regrid import regrid

    # Prepare output grid spec
    out_grid = {"grid": [target_resolution, target_resolution]}

    z_new = regrid(z, in_grid=gridspec, out_grid=out_grid)

    return x_new, y_new, z_new


def _generate_latlon_grid(
    resolution: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate regular latitude/longitude grid.

    Parameters
    ----------
    resolution : float
        Grid resolution in degrees.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (longitude, latitude) 2D mesh grids.
    """
    # Generate lat/lon vectors
    lat_v = np.linspace(90, -90, int(180 / resolution) + 1)
    lon_v = np.linspace(0, 360 - resolution, int(360 / resolution))

    # Create mesh grids
    lon, lat = np.meshgrid(lon_v, lat_v)

    return lon, lat

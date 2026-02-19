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

from earthkit.plots.sources.context import PlotContext


def apply_regrid(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    gridspec: Any,
    context: PlotContext,
    target_resolution: float | None = None,
    method: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply regridding to data with a structured grid specification.

    Delegates to :class:`~earthkit.plots.resample.Regrid` so that all
    regridding logic lives in one place.

    Parameters
    ----------
    x, y : np.ndarray
        Source coordinate arrays (passed through; regridder uses gridspec).
    z : np.ndarray
        Field values to regrid.
    gridspec : dict or GridSpec
        Grid specification from the source (HEALPix, reduced Gaussian, …).
    context : PlotContext
        Only geographic plots are regridded.
    target_resolution : float, optional
        Output grid spacing in degrees.  Defaults to the schema value.
    method : str, optional
        Interpolation method (``'linear'`` or ``'nearest-neighbour'``).

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        ``(lon_2d, lat_2d, z_2d)`` on the regular lat/lon output grid.
    """
    from earthkit.plots.resample import Regrid
    from earthkit.plots.schemas import schema

    if target_resolution is None:
        target_resolution = schema.interpolate_target_resolution

    resampler = Regrid(
        resolution=target_resolution,
        method=method or "linear",
        source_grid=gridspec,
    )
    return resampler.apply(x, y, z, gridspec=gridspec, context=context)

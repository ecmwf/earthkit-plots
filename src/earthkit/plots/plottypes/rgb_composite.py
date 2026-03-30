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

"""
RGB composite rendering.

Provides the pure data-preparation logic for three-channel RGB plots.
The function is free of Subplot state — it only requires three Source objects
and returns the prepared DataArray and coordinate arrays ready for plotting.

The Subplot wrapper (``Subplot.rgb_composite``) owns Source construction,
the ``pcolormesh`` call, and Layer bookkeeping.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np


class RGBCompositeResult(NamedTuple):
    """
    Data returned by :func:`prepare_rgb_composite`.

    Attributes
    ----------
    rgb_array : xarray.DataArray
        A DataArray with dims ``['y', 'x', 'rgb']`` and normalised [0, 1]
        values, ready to pass directly to ``pcolormesh`` with ``no_style=True``.
    x_values : numpy.ndarray
        1-D x coordinate array extracted from the red channel source.
    y_values : numpy.ndarray
        1-D y coordinate array extracted from the red channel source.
    """

    rgb_array: object  # xarray.DataArray — avoid hard import at module level
    x_values: np.ndarray
    y_values: np.ndarray


def _normalise_channel(values: np.ndarray) -> np.ndarray:
    """Linearly scale *values* to the [0, 1] range."""
    vmin, vmax = values.min(), values.max()
    if vmax == vmin:
        # Constant channel — return zeros rather than NaN from 0/0.
        return np.zeros_like(values, dtype=float)
    return (values - vmin) / (vmax - vmin)


def prepare_rgb_composite(red_source, green_source, blue_source) -> RGBCompositeResult:
    """
    Normalise three channel Sources and assemble them into an RGB DataArray.

    Each channel is independently min-max normalised to [0, 1].  The x/y
    coordinates are taken from the red channel (all three are assumed to share
    the same grid).

    Parameters
    ----------
    red_source, green_source, blue_source : Source
        Unified Source objects for the R, G, and B channels.  Each must have
        a non-None ``z`` coordinate (the scalar field values).

    Returns
    -------
    RGBCompositeResult
        Named tuple containing the ready-to-plot ``rgb_array``, and the
        extracted ``x_values`` / ``y_values`` coordinate arrays.

    Raises
    ------
    ValueError
        If any channel source has no ``z`` values.
    """
    import xarray as xr

    for name, src in (
        ("red", red_source),
        ("green", green_source),
        ("blue", blue_source),
    ):
        if src.z is None:
            raise ValueError(
                f"RGB composite requires z values for all three channels; "
                f"the {name!r} channel source has no z data."
            )

    red = _normalise_channel(red_source.z.values)
    green = _normalise_channel(green_source.z.values)
    blue = _normalise_channel(blue_source.z.values)

    x_values = red_source.x.values
    y_values = red_source.y.values

    # pcolormesh expects 1-D coordinate arrays; squeeze out the redundant
    # dimension when the source provides a full 2-D coordinate grid.
    if x_values.ndim == 2:
        x_values = x_values[0, :]
    if y_values.ndim == 2:
        y_values = y_values[:, 0]

    rgb_array = xr.DataArray(
        np.stack((red, green, blue), axis=-1),
        coords={"y": y_values, "x": x_values, "rgb": ["red", "green", "blue"]},
        dims=["y", "x", "rgb"],
    )

    return RGBCompositeResult(
        rgb_array=rgb_array,
        x_values=x_values,
        y_values=y_values,
    )

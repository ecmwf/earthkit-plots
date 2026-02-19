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
earthkit-plots resampling pipeline.

Public API
----------
Resample         -- base class for all resamplers
Subsample        -- stride/fixed subsampling of coordinate arrays
Regrid           -- regrid HEALPix / reduced Gaussian data to regular lat/lon
Chain            -- apply two or more resamplers in sequence
Bilinear         -- pixel-space bilinear interpolation (smooth contours)
NearestNeighbour -- pixel-space nearest-neighbour lookup (sharp cell edges)
Interpolate      -- unstructured → structured grid interpolation

Internal helpers
----------------
_AUTO            -- sentinel for resample="auto"
_PixelSampler    -- base class for pixel-sampling resamplers
_is_structured_grid -- True when gridspec indicates HEALPix or reduced Gaussian
_convert_spec    -- normalise a gridspec to a plain dict
_call_regrid_compat -- legacy shim for geo.regrid module
"""

from earthkit.plots.resample._base import _AUTO, Resample, Subsample
from earthkit.plots.resample._chain import Chain
from earthkit.plots.resample._interpolate import Interpolate
from earthkit.plots.resample._pixel_sampler import (
    Bilinear,
    GridSample,
    NearestNeighbour,
    _PixelSampler,
)
from earthkit.plots.resample._regrid import (
    Regrid,
    _call_regrid_compat,
    _convert_spec,
    _generate_latlon_grid,
    _is_structured_grid,
)

__all__ = [
    # Public resamplers
    "Resample",
    "Subsample",
    "Regrid",
    "Chain",
    "Bilinear",
    "NearestNeighbour",
    "Interpolate",
    # Backwards-compatible alias
    "GridSample",
    # Sentinels / helpers used internally (exposed for testing / advanced use)
    "_AUTO",
    "_PixelSampler",
    "_is_structured_grid",
    "_convert_spec",
    "_generate_latlon_grid",
    "_call_regrid_compat",
]

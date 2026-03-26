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
Backward-compatible re-export facade for the plotting pipeline.

The implementation has been split into focused private modules:

    components/_pipeline.py       — extract_plottables_* orchestration
    components/_style_utils.py    — configure_style, apply_*, _prepare_style_and_units
    components/_pixel_sampling.py — Bilinear/NN reprojection, data-space resampling
    components/_grid_handlers.py  — HEALPix/octahedral dispatch, cyclic points

All names that were previously public in this module are re-exported here so
that existing ``from earthkit.plots.components.extractors import ...`` calls
continue to work without modification.
"""

# --- grid handlers -----------------------------------------------------------
from earthkit.plots.components._grid_handlers import (
    _handle_cyclic_points,
    _handle_regular_grid_nn,
    _handle_specialized_grids,
    _handle_transform_settings,
    _plot_healpix,
    _plot_octahedral,
)

# --- pipeline entry points ---------------------------------------------------
from earthkit.plots.components._pipeline import (
    _infer_plot_context,
    extract_plottables_1D,
    extract_plottables_2D,
    extract_plottables_envelope,
    extract_plottables_vector_2D,
)

# --- pixel-sampling subsystem ------------------------------------------------
from earthkit.plots.components._pixel_sampling import (
    PixelSamplingResult,
    _apply_data_resampling,
    _apply_pixel_sampling,
    _auto_resample_policy,
    _get_subplot_bbox,
    _reproject_bilinear,
    _try_nearest_neighbour_imshow,
)

# --- style utilities ---------------------------------------------------------
from earthkit.plots.components._style_utils import (
    _prepare_style_and_units,
    apply_sampling,
    apply_scale_factor,
    configure_style,
)

__all__ = [
    # Pipeline
    "extract_plottables_1D",
    "extract_plottables_2D",
    "extract_plottables_vector_2D",
    "extract_plottables_envelope",
    "_infer_plot_context",
    # Style utilities
    "configure_style",
    "apply_scale_factor",
    "apply_sampling",
    "_prepare_style_and_units",
    # Pixel sampling
    "PixelSamplingResult",
    "_auto_resample_policy",
    "_apply_data_resampling",
    "_apply_pixel_sampling",
    "_get_subplot_bbox",
    "_reproject_bilinear",
    "_try_nearest_neighbour_imshow",
    # Grid handlers
    "_handle_specialized_grids",
    "_handle_regular_grid_nn",
    "_handle_cyclic_points",
    "_handle_transform_settings",
    "_plot_healpix",
    "_plot_octahedral",
]

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
Geospatial operations module.

This module provides comprehensive geospatial functionality including:
- Bounds and coordinate reference systems
- Grid definitions and operations
- Mapping and visualization tools
- Globe and tile handling
"""

# Import from bounds submodule (now at top level)
from ..bounds import (
    CANNOT_TRANSFORM_FIRST,
    DEFAULT_CRS,
    AlbersEqualArea,
    BoundingBox,
    CRSOptimiser,
    Domain,
    Equatorial,
    Global,
    LambertAzimuthalEqualArea,
    Landscape,
    LargeEqatorial,
    NaturalEarthDomain,
    NorthPolar,
    NorthPolarStereo,
    OptimisedCRS,
    PlateCarree,
    Portrait,
    PresetDomain,
    SouthPolar,
    SouthPolarStereo,
    Square,
    TransverseMercator,
    dict_to_crs,
    force_0_to_360,
    force_minus_180_to_180,
    format_name,
    get_resolution,
    is_cylindrical,
    is_latlon,
    parse_crs,
    roll_from_0_360_to_minus_180_180,
    roll_from_minus_180_180_to_0_360,
    string_to_crs,
    union,
)

# Import from grids submodule (now at top level)
from ..grids import (
    GRIDSPECS,
    GridSpec,
    HEALPix,
    ReducedGG,
    _guess_resolution_and_shape,
    calculate_row_heights,
    interpolate_unstructured,
    is_global,
    is_structured,
    needs_cyclic_point,
    nnshow,
    plot_octahedral_grid,
)
from .globes import globe

# Import from geospatial modules (formerly in geospatial package)
from .maps import Map
from .tiles import Tile

__all__ = [
    # Bounds and coordinate systems
    "BoundingBox",
    "DEFAULT_CRS",
    "CANNOT_TRANSFORM_FIRST",
    "dict_to_crs",
    "string_to_crs",
    "parse_crs",
    "is_cylindrical",
    "Domain",
    "PresetDomain",
    "force_minus_180_to_180",
    "roll_from_0_360_to_minus_180_180",
    "roll_from_minus_180_180_to_0_360",
    "force_0_to_360",
    "is_latlon",
    "format_name",
    "union",
    "NaturalEarthDomain",
    "get_resolution",
    "OptimisedCRS",
    "PlateCarree",
    "LambertAzimuthalEqualArea",
    "TransverseMercator",
    "AlbersEqualArea",
    "NorthPolarStereo",
    "SouthPolarStereo",
    "CRSOptimiser",
    "Global",
    "Equatorial",
    "NorthPolar",
    "SouthPolar",
    "LargeEqatorial",
    "Square",
    "Landscape",
    "Portrait",
    # Grids
    "is_structured",
    "is_global",
    "_guess_resolution_and_shape",
    "interpolate_unstructured",
    "needs_cyclic_point",
    "nnshow",
    "plot_octahedral_grid",
    "calculate_row_heights",
    "GridSpec",
    "ReducedGG",
    "HEALPix",
    "GRIDSPECS",
    # Mapping and visualization
    "Map",
    "Tile",
    "globe",
]

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
Bounds submodule for geospatial operations.

This submodule contains classes and functions for handling:
- Geographic bounds and boundaries
- Coordinate reference systems
- Domain definitions and operations
- Natural Earth data integration
"""

from .bounds import BoundingBox
from .coordinate_reference_systems import (
    DEFAULT_CRS,
    CANNOT_TRANSFORM_FIRST,
    dict_to_crs,
    string_to_crs,
    parse_crs,
    is_cylindrical,
)
from .domains import Domain, PresetDomain, force_minus_180_to_180, roll_from_0_360_to_minus_180_180, roll_from_minus_180_180_to_0_360, force_0_to_360, is_latlon, format_name, union
from .natural_earth import NaturalEarthDomain, get_resolution
from .optimisers import (
    OptimisedCRS,
    PlateCarree,
    LambertAzimuthalEqualArea,
    TransverseMercator,
    AlbersEqualArea,
    NorthPolarStereo,
    SouthPolarStereo,
    CRSOptimiser,
    Global,
    Equatorial,
    NorthPolar,
    SouthPolar,
    LargeEqatorial,
    Square,
    Landscape,
    Portrait,
)

__all__ = [
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
]

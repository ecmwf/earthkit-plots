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
Grids submodule for geospatial operations.

This submodule contains classes and functions for handling:
- Grid definitions and operations
- HEALPix grid handling
- Octahedral grid operations
- Grid optimization algorithms
"""

from .grids import (
    is_structured,
    is_global,
    _guess_resolution_and_shape,
    interpolate_unstructured,
    needs_cyclic_point,
)
from .healpix import nnshow
from .octahedral import plot_octahedral_grid, calculate_row_heights
from .utils import (
    GridSpec,
    ReducedGG,
    HEALPix,
    GRIDSPECS,
)

__all__ = [
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
]

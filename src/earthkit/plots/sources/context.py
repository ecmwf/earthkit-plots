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

from enum import Enum


class PlotContext(Enum):
    """
    Plot type context to guide coordinate inference.

    The plot context helps resolve ambiguities in coordinate assignment
    by providing information about the intended plot type. For example,
    a "CARTESIAN_1D" context indicates a line plot or bar chart,
    while a "GEOGRAPHIC_2D" context indicates a geographic map of a field,
    which affects how many dimensions are expected and how coordinates
    should be interpreted.
    """

    CARTESIAN_1D = "cartesian_1d"  # Line plots, bar charts, (some) scatter plots
    CARTESIAN_2D = "cartesian_2d"  # Heatmaps, contours
    GEOGRAPHIC_1D = "geographic_1d"  # Hovmoellers, cross-sections
    GEOGRAPHIC_2D = "geographic_2d"  # Maps
    GEOGRAPHIC_VECTOR_2D = "geographic_vector_2d"  # Vector fields on maps
    CARTESIAN_VECTOR_2D = "cartesian_vector_2d"  # Vector fields in cartesian plots

    @property
    def is_geographic(self) -> bool:
        """Return True if this is a geographic plot context."""
        return "geographic" in self.value

    @property
    def is_vector(self) -> bool:
        """Return True if this is a vector plot context."""
        return "vector" in self.value

    @property
    def is_cartesian(self) -> bool:
        """Return True if this is a cartesian plot context."""
        return "cartesian" in self.value

    @property
    def is_1d(self) -> bool:
        """Return True if this is a 1D plot context."""
        return "1d" in self.value

    @property
    def is_2d(self) -> bool:
        """Return True if this is a 2D plot context."""
        return "2d" in self.value

    @property
    def requires_z(self) -> bool:
        """Return True if this plot type requires z values."""
        return self.is_2d

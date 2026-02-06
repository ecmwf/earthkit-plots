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

from dataclasses import dataclass

import numpy as np


@dataclass
class CoordinateInfo:
    """
    Information about an extracted coordinate dimension.

    Returned by extractors to provide both coordinate values and metadata.
    """

    values: np.ndarray
    """Coordinate values as numpy array."""

    name: str = ""
    """
    Name of the coordinate/variable used to extract this dimension.
    Empty string for auto-generated coordinates (e.g., indices).
    """

    source_units: str | None = None
    """Original units from the data source (e.g., from attrs['units'])."""

    metadata: dict = None
    """
    Dimension-specific metadata from coordinate/variable attributes.
    Empty dict for auto-generated coordinates.
    """

    def __post_init__(self):
        """Ensure metadata is a dict."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExtractedCoordinates:
    """
    Complete coordinate extraction result with metadata.

    Returned by extractor.extract_coordinates() to provide both coordinate
    arrays and their associated metadata.
    """

    x: CoordinateInfo
    """X coordinate information."""

    y: CoordinateInfo
    """Y coordinate information."""

    z: CoordinateInfo | None = None
    """Z coordinate information (None for 1D plots)."""

    u: CoordinateInfo | None = None
    """U component information (None for non-vector plots)."""

    v: CoordinateInfo | None = None
    """V component information (None for non-vector plots)."""

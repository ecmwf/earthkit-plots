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
from earthkit.plots.sources.coordinates import ExtractedCoordinates


class BaseExtractor:
    """
    Base extractor with common utilities and default implementations.

    Subclasses should override extract_coordinates() and optionally
    override get_metadata(), get_crs(), and get_gridspec() methods.
    """

    def __init__(self, data: Any):
        self.data = data

    def extract_coordinates(
        self,
        x: str | np.ndarray | None,
        y: str | np.ndarray | None,
        z: str | np.ndarray | None,
        u: str | np.ndarray | None,
        v: str | np.ndarray | None,
        context: PlotContext,
    ) -> ExtractedCoordinates:
        """
        Extract x, y, z, u, v coordinates from data with metadata.

        Must be implemented by subclasses.

        Parameters
        ----------
        x : str, np.ndarray, or None
            X coordinate specification.
        y : str, np.ndarray, or None
            Y coordinate specification.
        z : str, np.ndarray, or None
            Z values specification.
        u : str, np.ndarray, or None
            U component specification (for vector plots).
        v : str, np.ndarray, or None
            V component specification (for vector plots).
        context : PlotContext
            Plot context to guide coordinate inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        raise NotImplementedError("Subclasses must implement extract_coordinates()")

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Extract metadata value.

        Default implementation returns default value.
        Subclasses should override to extract from their data type.

        Parameters
        ----------
        key : str
            Metadata key to retrieve.
        default : Any, optional
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value or default.
        """
        return default

    def get_crs(self) -> Any | None:
        """
        Extract coordinate reference system.

        Default implementation returns None.
        Subclasses should override if their data type supports CRS.

        Returns
        -------
        CRS or None
            Coordinate reference system if available.
        """
        return None

    def get_gridspec(self) -> Any | None:
        """
        Extract grid specification for regridding.

        Default implementation returns None.
        Subclasses should override if their data type has gridspec metadata.

        Returns
        -------
        GridSpec or None
            Grid specification if data has special grid structure.
        """
        return None

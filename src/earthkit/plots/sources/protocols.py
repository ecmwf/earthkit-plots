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

from typing import Any, Protocol

import numpy as np

from earthkit.plots.sources.context import PlotContext


class DataExtractor(Protocol):
    """
    Protocol that all data extractors must satisfy.

    Extractors wrap different data types (numpy, xarray, earthkit, etc.)
    and provide a consistent interface for coordinate extraction and
    metadata access.
    """

    def extract_coordinates(
        self,
        x: str | np.ndarray | None,
        y: str | np.ndarray | None,
        z: str | np.ndarray | None,
        u: str | np.ndarray | None,
        v: str | np.ndarray | None,
        context: PlotContext,
    ):
        """
        Extract x, y, z, u, v coordinates from some arbitrary data.

        Parameters
        ----------
        x : str, np.ndarray, or None
            X coordinate specification. Can be a coordinate name (str),
            explicit array, or None for automatic inference.
        y : str, np.ndarray, or None
            Y coordinate specification. Can be a coordinate name (str),
            explicit array, or None for automatic inference.
        z : str, np.ndarray, or None
            Z values specification. Can be a variable name (str),
            explicit array, or None for automatic inference.
        u : str, np.ndarray, or None
            U component specification (for vector plots). Can be a variable
            name (str), explicit array, or None for automatic inference.
        v : str, np.ndarray, or None
            V component specification (for vector plots). Can be a variable
            name (str), explicit array, or None for automatic inference.
        context : PlotContext
            Plot context to guide coordinate inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata.
        """
        ...

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Extract metadata value.

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
        ...

    def get_crs(self) -> Any | None:
        """
        Extract coordinate reference system.

        Returns
        -------
        cartopy.crs.CRS or None
            Coordinate reference system if available.
        """
        ...

    def get_gridspec(self) -> Any | None:
        """
        Extract grid specification for regridding.

        Returns
        -------
        GridSpec or None
            Grid specification if data has special grid structure.
        """
        ...

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

from typing import Any, Optional, Protocol, Union

import numpy as np

from earthkit.plots.sources.context import PlotContext


class DataAdaptor(Protocol):
    """
    Protocol that all data adaptors must satisfy.

    Adaptors wrap different data types (numpy, xarray, earthkit, etc.)
    and provide a consistent interface for coordinate extraction and
    metadata access.
    """

    def extract_coordinates(
        self,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        context: PlotContext,
    ) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Extract x, y, z coordinates from some arbitrary data.

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
        context : PlotContext
            Plot context to guide coordinate inference.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]
            Extracted (x, y, z) coordinates.
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

    def get_crs(self) -> Optional[Any]:
        """
        Extract coordinate reference system.

        Returns
        -------
        cartopy.crs.CRS or None
            Coordinate reference system if available.
        """
        ...

    def get_gridspec(self) -> Optional[Any]:
        """
        Extract grid specification for regridding.

        Returns
        -------
        GridSpec or None
            Grid specification if data has special grid structure.
        """
        ...

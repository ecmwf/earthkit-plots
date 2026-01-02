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

from typing import Any, Optional, Union

import numpy as np

from earthkit.plots.sources.adaptors import SELECTED_DATA
from earthkit.plots.sources.adaptors.base import BaseAdaptor
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.extractor import CoordinateExtractor
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates


class NumpyAdaptor(BaseAdaptor):
    """
    Adaptor for numpy arrays and array-like objects.

    Handles simple arrays with minimal metadata. Coordinates are inferred
    from array shapes and plot context.
    """

    def __init__(self, data: Any, metadata: Optional[dict] = None):
        """
        Initialize numpy adaptor.

        Parameters
        ----------
        data : array-like
            Numpy array or array-like object.
        metadata : dict, optional
            Optional metadata dict for the data.
        """
        super().__init__(data)
        self._metadata = metadata or {}

    def extract_coordinates(
        self,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        context: PlotContext,
    ) -> ExtractedCoordinates:
        """
        Extract coordinates from numpy arrays with auto-generation.

        Matplotlib-style interface: explicit x, y, z arrays with auto-generation
        of missing coordinates based on provided arrays and plot context.

        Auto-generation rules:
        - CARTESIAN_1D: if only y provided, generate x as index
        - CARTESIAN_2D/GEOGRAPHIC_2D: if only z provided, generate x, y as indices from z.shape
        - If no arrays provided at all, use self.data as fallback (for backward compat)

        Parameters
        ----------
        x : np.ndarray or None
            X coordinate array.
        y : np.ndarray or None
            Y coordinate array.
        z : np.ndarray or None
            Z values array.
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        # Reject string coordinates
        for coord_name, coord_value in [("x", x), ("y", y), ("z", z)]:
            if isinstance(coord_value, str):
                raise ValueError(
                    f"String coordinate names not supported for numpy arrays. "
                    f"Please provide explicit coordinate arrays for '{coord_name}'."
                )

        # Convert to numpy arrays if provided
        x_arr = np.atleast_1d(x) if x is not None else None
        y_arr = np.atleast_1d(y) if y is not None else None
        z_arr = np.atleast_1d(z) if z is not None else None

        # Build arrays dict for coordinate extractor
        arrays = {}

        # Determine which array is the "main" data array (marked with SELECTED_DATA)
        # and add user-provided arrays
        if context.is_2d:
            # 2D plots: z is the main data
            if z_arr is not None:
                arrays[SELECTED_DATA] = z_arr
                arrays["z_spec"] = z_arr
            elif self.data is not None:
                # Fallback: use self.data as z (for backward compat with legacy "data" param)
                data_array = np.atleast_1d(self.data)
                arrays[SELECTED_DATA] = data_array

            # Add x and y if provided
            if x_arr is not None:
                arrays["x_spec"] = x_arr
            if y_arr is not None:
                arrays["y_spec"] = y_arr
        else:
            # 1D plots: y is the main data
            if y_arr is not None:
                arrays[SELECTED_DATA] = y_arr
                arrays["y_spec"] = y_arr
            elif self.data is not None:
                # Fallback: use self.data as y (for backward compat with legacy "data" param)
                data_array = np.atleast_1d(self.data)
                arrays[SELECTED_DATA] = data_array

            # Add x if provided
            if x_arr is not None:
                arrays["x_spec"] = x_arr

        # Use coordinate extractor to infer
        coords = CoordinateExtractor.infer_from_shapes_and_context(arrays, context)

        # For numpy arrays, no metadata available - all empty
        # Get units from top-level metadata if available
        source_units = self._metadata.get("units")

        x_info = CoordinateInfo(
            values=coords["x"],
            name="",
            source_units=None,
            metadata={},
        )
        y_info = CoordinateInfo(
            values=coords["y"],
            name="",
            source_units=source_units if context == PlotContext.CARTESIAN_1D else None,
            metadata={},
        )
        z_info = None
        if coords.get("z") is not None:
            z_info = CoordinateInfo(
                values=coords["z"],
                name="",
                source_units=source_units if context.is_2d else None,
                metadata={},
            )

        return ExtractedCoordinates(x=x_info, y=y_info, z=z_info)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.

        Parameters
        ----------
        key : str
            Metadata key.
        default : Any
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value or default.
        """
        return self._metadata.get(key, default)

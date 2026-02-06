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
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates
from earthkit.plots.sources.extractors.base import BaseExtractor


class NumpyExtractor(BaseExtractor):
    """
    Strategy for extracting coordinates from numpy arrays and array-like objects.

    Handles simple arrays with minimal metadata. Coordinates are inferred
    from array shapes and plot context.

    Parameters
    ----------
    data : array-like
        Numpy array or array-like object.
    metadata : dict, optional
        Optional metadata dict for the data.
    """

    def __init__(self, data: Any, metadata: dict | None = None):
        super().__init__(data)
        self._metadata = metadata or {}

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
        Extract coordinates from numpy arrays.

        Matplotlib-style interface: explicit x, y, z arrays with auto-generation
        of missing coordinates based on provided arrays and plot context.

        Auto-generation rules:
        - CARTESIAN_1D: if only y provided, generate x as index
        - CARTESIAN_2D/GEOGRAPHIC_2D: if only z provided, generate x, y as indices from z.shape

        Parameters
        ----------
        x : np.ndarray or None
            X coordinate array.
        y : np.ndarray or None
            Y coordinate array.
        z : np.ndarray or None
            Z values array.
        u : np.ndarray or None
            U component array (for vector plots).
        v : np.ndarray or None
            V component array (for vector plots).
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        for coord_name, coord_value in [
            ("x", x),
            ("y", y),
            ("z", z),
            ("u", u),
            ("v", v),
        ]:
            if isinstance(coord_value, str):
                raise ValueError(
                    f"String coordinate names not supported for numpy arrays. "
                    f"Please provide explicit coordinate arrays for '{coord_name}'."
                )

        # Convert to numpy arrays if lists/tuples provided
        x_arr = np.atleast_1d(x) if x is not None else None
        y_arr = np.atleast_1d(y) if y is not None else None
        z_arr = np.atleast_1d(z) if z is not None else None
        u_arr = np.atleast_1d(u) if u is not None else None
        v_arr = np.atleast_1d(v) if v is not None else None

        # Validate u and v: both or neither
        if (u_arr is None) != (v_arr is None):
            raise ValueError(
                "Both u and v components must be specified for vector plots. "
                f"Got u={'array' if u_arr is not None else 'None'}, "
                f"v={'array' if v_arr is not None else 'None'}"
            )

        if context.is_2d:
            coords = self._extract_2d_coordinates(x_arr, y_arr, z_arr, u_arr, v_arr)
        else:
            coords = self._extract_1d_coordinates(x_arr, y_arr)

        return ExtractedCoordinates(
            x=coords["x"],
            y=coords["y"],
            z=coords.get("z"),
            u=coords.get("u"),
            v=coords.get("v"),
        )

    def _extract_1d_coordinates(
        self,
        x_arr: np.ndarray | None,
        y_arr: np.ndarray | None,
    ) -> dict[str, CoordinateInfo]:
        """
        Extract coordinates for 1D plots (lines, bars etc).

        Default: y is the data, x is the independent variable (auto-generated
        if not provided).

        Parameters
        ----------
        x_arr : np.ndarray or None
            X coordinate array.
        y_arr : np.ndarray or None
            Y coordinate array (data values).

        Returns
        -------
        dict
            Dictionary with keys 'x', 'y', 'z' (z is always None for 1D).
        """
        if y_arr is not None:
            y_values = y_arr
        elif self.data is not None:
            y_values = np.atleast_1d(self.data)
        else:
            raise ValueError("No data provided for 1D plot (y is required)")

        if x_arr is not None:
            x_values = x_arr
        else:
            x_values = np.arange(len(y_values))

        # Get units from metadata if available (only applies to y for 1D)
        source_units = self._metadata.get("units")

        x_info = CoordinateInfo(
            values=x_values,
            name="",
            source_units=None,
            metadata={},
        )
        y_info = CoordinateInfo(
            values=y_values,
            name="",
            source_units=source_units,
            metadata={},
        )

        return {"x": x_info, "y": y_info, "z": None}

    def _extract_2d_coordinates(
        self,
        x_arr: np.ndarray | None,
        y_arr: np.ndarray | None,
        z_arr: np.ndarray | None,
        u_arr: np.ndarray | None,
        v_arr: np.ndarray | None,
    ) -> dict[str, CoordinateInfo]:
        """
        Extract coordinates for 2D plots including optional vector components.

        Handles two cases:
        1. Structured grids: z is 2D, x/y are 1D (or auto-generated), meshgrid applied
        2. Scattered points: x, y, z are all 1D with matching lengths, no meshgrid

        Parameters
        ----------
        x_arr : np.ndarray or None
            X coordinate array.
        y_arr : np.ndarray or None
            Y coordinate array.
        z_arr : np.ndarray or None
            Z values array (can be 1D for scattered points or 2D for grids).
        u_arr : np.ndarray or None
            U component array (for vector plots).
        v_arr : np.ndarray or None
            V component array (for vector plots).

        Returns
        -------
        dict
            Dictionary with keys 'x', 'y', 'z', 'u', 'v'.
        """
        if z_arr is not None:
            z_values = z_arr
        elif self.data is not None:
            z_values = np.atleast_1d(self.data)
        else:
            raise ValueError("No data provided for 2D plot (z is required)")

        if z_values.ndim > 2:
            raise ValueError(
                f"Expected 1D or 2D data for 2D plot, got {z_values.ndim}D array"
            )

        # Case 1: z is 1D - scattered point data (x, y, z all 1D with same length)
        if z_values.ndim == 1:
            n_points = len(z_values)

            if x_arr is not None:
                x_values = x_arr
            else:
                # Auto-generate x as indices
                x_values = np.arange(n_points)

            if y_arr is not None:
                y_values = y_arr
            else:
                # Auto-generate y as indices
                y_values = np.arange(n_points)

            # Verify all arrays have matching lengths for scattered data
            if len(x_values) != n_points or len(y_values) != n_points:
                raise ValueError(
                    f"For scattered point data (1D z), x, y, and z must have the same length. "
                    f"Got x: {len(x_values)}, y: {len(y_values)}, z: {n_points}"
                )

            # Keep as 1D - no meshgrid for scattered points

        # Case 2: z is 2D - structured grid data
        else:
            ny, nx = z_values.shape

            if x_arr is not None:
                x_values = x_arr
            else:
                # Auto-generate x from z shape
                x_values = np.arange(nx)

            if y_arr is not None:
                y_values = y_arr
            else:
                # Auto-generate y from z shape
                y_values = np.arange(ny)

            # Apply meshgrid if coordinates are 1D
            if x_values.ndim == 1 and y_values.ndim == 1:
                if len(x_values) != nx or len(y_values) != ny:
                    raise ValueError(
                        f"Coordinate shapes don't match data: "
                        f"x has {len(x_values)} points (expected {nx}), "
                        f"y has {len(y_values)} points (expected {ny})"
                    )
                x_values, y_values = np.meshgrid(x_values, y_values)

        # Get units from metadata if available (only applies to z for 2D)
        source_units = self._metadata.get("units")

        x_info = CoordinateInfo(
            values=x_values,
            name="",
            source_units=None,
            metadata={},
        )
        y_info = CoordinateInfo(
            values=y_values,
            name="",
            source_units=None,
            metadata={},
        )
        z_info = CoordinateInfo(
            values=z_values,
            name="",
            source_units=source_units,
            metadata={},
        )

        # Extract u and v if provided
        u_info = None
        v_info = None

        if u_arr is not None and v_arr is not None:
            # Validate shapes match z
            if u_arr.shape != z_values.shape or v_arr.shape != z_values.shape:
                raise ValueError(
                    f"Vector component shapes must match data shape. "
                    f"Got z: {z_values.shape}, u: {u_arr.shape}, v: {v_arr.shape}"
                )

            u_info = CoordinateInfo(
                values=u_arr,
                name="",
                source_units=None,
                metadata={},
            )
            v_info = CoordinateInfo(
                values=v_arr,
                name="",
                source_units=None,
                metadata={},
            )

        return {"x": x_info, "y": y_info, "z": z_info, "u": u_info, "v": v_info}

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

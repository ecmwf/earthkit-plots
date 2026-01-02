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

from typing import Optional

import numpy as np

from earthkit.plots import identifiers
from earthkit.plots.sources.adaptors import SELECTED_DATA
from earthkit.plots.sources.context import PlotContext


class CoordinateExtractor:
    """
    Central coordinate extraction logic shared across most adaptors.

    This class encapsulates the inference rules for determining which
    arrays correspond to x, y, and z coordinates based on the plot context.
    """

    @staticmethod
    def infer_from_shapes_and_context(
        arrays: dict[str, np.ndarray],
        context: PlotContext,
    ) -> dict[str, Optional[np.ndarray]]:
        """
        Infer coordinate roles (x/y/z) from array shapes and plot context.

        Parameters
        ----------
        arrays : dict[str, np.ndarray]
            Available arrays with descriptive keys. Special keys:
            - 'x_spec', 'y_spec', 'z_spec': User-specified coordinates
            - SELECTED_DATA constant: The selected data variable's values
            - Dimension/coordinate names as keys
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        dict
            Dictionary with keys 'x', 'y', 'z' containing inferred arrays.
            z may be None for 1D plots.
        """
        if "x_spec" in arrays and "y_spec" in arrays:
            if context.is_2d:
                # Determine z: either from z_spec or SELECTED_DATA
                z = arrays.get("z_spec", arrays.get(SELECTED_DATA))
                x = arrays["x_spec"]
                y = arrays["y_spec"]

                # Apply meshgrid if needed (1D coords with 2D data)
                if z is not None and z.ndim == 2 and x.ndim == 1 and y.ndim == 1:
                    ny, nx = z.shape
                    if len(x) == nx and len(y) == ny:
                        x, y = np.meshgrid(x, y)

                return {"x": x, "y": y, "z": z}
            else:
                return {
                    "x": arrays["x_spec"],
                    "y": arrays["y_spec"],
                    "z": arrays.get("z_spec"),
                }

        # Dispatch to context-specific coordinate inference
        if context == PlotContext.CARTESIAN_1D:
            return CoordinateExtractor._infer_1d_cartesian(arrays)
        elif context == PlotContext.CARTESIAN_2D:
            return CoordinateExtractor._infer_2d_cartesian(arrays)
        elif context == PlotContext.GEOGRAPHIC_1D:
            return CoordinateExtractor._infer_1d_geographic(arrays)
        else:
            return CoordinateExtractor._infer_2d_geographic(arrays)

    @staticmethod
    def _infer_1d_cartesian(arrays: dict) -> dict:
        """
        Infer coordinates for 1D cartesian plots (line plots, scatter, bar).

        Default assumption:
            x = independent variable
            y = dependent variable

        Strategy: Attempt to auto-detect x and y first. Then if the user
        has specified only one of x or y, check if it matches the auto-detected
        *other* coordinate to determine if a swap is needed.
        
        Parameters
        ----------
        arrays : dict
            Available arrays with descriptive keys.
        """
        auto_x = None
        auto_y = None

        # Look for a 1D variable - this becomes y
        if SELECTED_DATA in arrays and arrays[SELECTED_DATA].ndim == 1:
            auto_y = arrays[SELECTED_DATA]
            # Check if there's a matching dimension coordinate
            # (any 1D array that's not the variable itself and has same length)
            for dim_key in arrays:
                # Skip the variable itself and user-specified coords
                if dim_key in [SELECTED_DATA, "values", "x_spec", "y_spec", "z_spec"]:
                    continue
                # Look for 1D array with matching length (dimension coordinate)
                if arrays[dim_key].ndim == 1 and len(arrays[dim_key]) == len(auto_y):
                    auto_x = arrays[dim_key]
                    break
            # No matching dimension, generate index
            if auto_x is None:
                auto_x = np.arange(len(auto_y))

        # Fallback: use first two 1D arrays if no selected data
        if auto_x is None or auto_y is None:
            one_d_arrays = [(k, v) for k, v in arrays.items()
                           if v.ndim == 1 and k not in ["x_spec", "y_spec", "z_spec"]]
            if len(one_d_arrays) >= 2:
                auto_x = one_d_arrays[0][1]
                auto_y = one_d_arrays[1][1]
            elif len(one_d_arrays) == 1:
                auto_y = one_d_arrays[0][1]
                auto_x = np.arange(len(auto_y))
            else:
                raise ValueError("Could not infer 1D cartesian coordinates from provided arrays")

        # Step 2: Handle user specifications with potential swapping
        x_spec = arrays.get("x_spec")
        y_spec = arrays.get("y_spec")

        if x_spec is not None and y_spec is None:
            # User specified x only - check if it matches auto_y
            if np.array_equal(x_spec, auto_y):
                # Swap: what we thought was y becomes x
                return {"x": auto_y, "y": auto_x, "z": None}
            else:
                # Use user's x, keep auto y
                return {"x": x_spec, "y": auto_y, "z": None}

        elif y_spec is not None and x_spec is None:
            # User specified y only - check if it matches auto_x
            if np.array_equal(y_spec, auto_x):
                # Swap: what we thought was x becomes y
                return {"x": auto_y, "y": auto_x, "z": None}
            else:
                # Use user's y, keep auto x
                return {"x": auto_x, "y": y_spec, "z": None}

        # No user specs, use auto-detected
        return {"x": auto_x, "y": auto_y, "z": None}

    @staticmethod
    def _infer_2d_cartesian(arrays: dict) -> dict:
        """
        Infer coordinates for 2D cartesian plots (heatmaps, contours).

        Convention: z = 2D data field, x/y = coordinates along axes.

        Strategy: Auto-detect first, then check if user-specified
        coordinates should swap roles.
        """
        # Step 1: Auto-detect z, x, y (ignoring user specs for now)
        auto_z = None
        auto_x = None
        auto_y = None

        # Look for 2D variable as z
        for key in [SELECTED_DATA, "values"]:
            if key in arrays and arrays[key].ndim == 2:
                auto_z = arrays[key]
                ny, nx = auto_z.shape

                # Look for matching 1D dimensions
                for dim_key, arr in arrays.items():
                    if arr.ndim == 1 and dim_key not in ["x_spec", "y_spec", "z_spec", SELECTED_DATA, "values"]:
                        if len(arr) == nx and auto_x is None:
                            auto_x = arr
                        elif len(arr) == ny and auto_y is None:
                            auto_y = arr

                # Generate if not found
                if auto_x is None:
                    auto_x = np.arange(nx)
                if auto_y is None:
                    auto_y = np.arange(ny)

                break

        if auto_z is None:
            raise ValueError("Could not find 2D data for cartesian 2D plot")

        # Step 2: Handle user specifications
        x_spec = arrays.get("x_spec")
        y_spec = arrays.get("y_spec")
        z_spec = arrays.get("z_spec")

        # If user specified z, use their z and auto-detected x/y
        if z_spec is not None:
            z = z_spec
            x = auto_x
            y = auto_y
        else:
            z = auto_z

            # Check for x/y swapping
            if x_spec is not None and y_spec is None:
                # User specified x only - check if it matches auto_y
                if np.array_equal(x_spec, auto_y):
                    # Swap
                    x = auto_y
                    y = auto_x
                else:
                    x = x_spec
                    y = auto_y
            elif y_spec is not None and x_spec is None:
                # User specified y only - check if it matches auto_x
                if np.array_equal(y_spec, auto_x):
                    # Swap
                    x = auto_y
                    y = auto_x
                else:
                    x = auto_x
                    y = y_spec
            else:
                # No user specs, use auto-detected
                x = auto_x
                y = auto_y

        # Meshgrid if 1D coordinates with 2D data
        if z.ndim == 2 and x.ndim == 1 and y.ndim == 1:
            ny, nx = z.shape
            # Verify shapes match
            if len(x) != nx or len(y) != ny:
                raise ValueError(
                    f"Coordinate shapes don't match data: "
                    f"x has {len(x)} points (expected {nx}), "
                    f"y has {len(y)} points (expected {ny})"
                )
            x, y = np.meshgrid(x, y)

        return {"x": x, "y": y, "z": z}

    @staticmethod
    def _infer_1d_geographic(arrays: dict) -> dict:
        """
        Infer coordinates for 1D geographic plots (point maps, trajectories).

        Convention: x = longitude, y = latitude, z = values (optional).
        """
        # Try to find lat/lon by name matching
        lat_key = CoordinateExtractor._match_by_name(
            list(arrays.keys()), identifiers.LATITUDE
        )
        lon_key = CoordinateExtractor._match_by_name(
            list(arrays.keys()), identifiers.LONGITUDE
        )

        if lat_key and lon_key:
            lat = arrays[lat_key]
            lon = arrays[lon_key]

            # Find a value variable if available
            z = None
            for key in [SELECTED_DATA, "values", "z_spec"]:
                if key in arrays and key not in (lat_key, lon_key):
                    z = arrays[key]
                    break

            return {"x": lon, "y": lat, "z": z}

        # Fallback: if user specified x and y, assume they are lon/lat
        if "x_spec" in arrays and "y_spec" in arrays:
            return {
                "x": arrays["x_spec"],
                "y": arrays["y_spec"],
                "z": arrays.get("z_spec"),
            }

        raise ValueError(
            "Could not infer geographic coordinates. "
            "Please specify x (longitude) and y (latitude) explicitly."
        )

    @staticmethod
    def _infer_2d_geographic(arrays: dict) -> dict:
        """
        Infer coordinates for 2D geographic plots (field maps).

        IMPORTANT: Extracts coordinates in the data's native CRS, whether that's:
        - Projected coordinates (x/y in meters for Lambert, UTM, etc.)
        - Geographic coordinates (latitude/longitude in degrees)

        The plotting code will handle any necessary transformations based on the
        data's CRS and the target projection.
        """
        # Strategy: Look for dimension coordinates first (the actual coordinate arrays),
        # ignoring scalar coordinates which are just metadata.

        # First, try to find x/y dimension coordinates (projected data)
        x_key = CoordinateExtractor._match_by_name(
            list(arrays.keys()), identifiers.X
        )
        y_key = CoordinateExtractor._match_by_name(
            list(arrays.keys()), identifiers.Y
        )

        if x_key and y_key:
            x = arrays[x_key]
            y = arrays[y_key]

            # Only use if they're actual dimension coordinates (not scalars)
            if x.ndim >= 1 and y.ndim >= 1:
                # Find 2D field
                z = None
                for key in [SELECTED_DATA, "values", "z_spec"]:
                    if key in arrays and arrays[key].ndim in (1, 2):
                        z = arrays[key]
                        break

                # Meshgrid if 1D coordinates with 2D data
                if z is not None and z.ndim == 2 and x.ndim == 1 and y.ndim == 1:
                    ny, nx = z.shape
                    if len(x) == nx and len(y) == ny:
                        x, y = np.meshgrid(x, y)

                return {"x": x, "y": y, "z": z}

        # If no x/y, try lat/lon (geographic data)
        lat_key = CoordinateExtractor._match_by_name(
            list(arrays.keys()), identifiers.LATITUDE
        )
        lon_key = CoordinateExtractor._match_by_name(
            list(arrays.keys()), identifiers.LONGITUDE
        )

        if lat_key and lon_key:
            lat = arrays[lat_key]
            lon = arrays[lon_key]

            # Only use if they're actual dimension coordinates (not scalars)
            if lat.ndim >= 1 and lon.ndim >= 1:
                # Find 2D field
                z = None
                for key in [SELECTED_DATA, "values", "z_spec"]:
                    if key in arrays and arrays[key].ndim in (1, 2):
                        z = arrays[key]
                        break

                # Meshgrid if 1D coordinates with 2D data
                if z is not None and z.ndim == 2 and lon.ndim == 1 and lat.ndim == 1:
                    ny, nx = z.shape
                    if len(lon) == nx and len(lat) == ny:
                        lon, lat = np.meshgrid(lon, lat)

                return {"x": lon, "y": lat, "z": z}

        # Fallback: look for 2D arrays that could be lat/lon
        # and another 2D array for the field
        two_d_arrays = {k: v for k, v in arrays.items() if v.ndim == 2}
        if len(two_d_arrays) >= 2:
            # Assume first is field, need to find lat/lon
            # This is ambiguous - better to require explicit specification
            pass

        raise ValueError(
            "Could not infer geographic coordinates for 2D plot. "
            "Please specify coordinates explicitly or ensure data has "
            "identifiable latitude/longitude dimensions."
        )

    @staticmethod
    def _match_by_name(
        candidates: list[str], identifiers: list[str]
    ) -> Optional[str]:
        """
        Find first candidate matching identifier list.

        Parameters
        ----------
        candidates : list of str
            Candidate names to check.
        identifiers : list of str
            Identifier patterns to match against.

        Returns
        -------
        str or None
            First matching candidate, or None if no match.
        """
        for candidate in candidates:
            if candidate in identifiers:
                return candidate
        return None

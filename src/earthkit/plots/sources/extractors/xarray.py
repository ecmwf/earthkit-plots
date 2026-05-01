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
import xarray as xr

from earthkit.plots import identifiers
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates
from earthkit.plots.sources.extractors.base import BaseExtractor


def _coord_item(coord):
    """Return a scalar coordinate value, converting datetime64 to pd.Timestamp."""
    if np.issubdtype(coord.dtype, np.datetime64):
        import pandas as pd

        return pd.Timestamp(coord.values)
    return coord.item()


class XarrayExtractor(BaseExtractor):
    """
    Strategy for extracting coordinates from xarray DataArrays and Datasets.

    Handles rich metadata, coordinate systems, and multi-dimensional data.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Xarray data structure.
    """

    def __init__(self, data: xr.DataArray | xr.Dataset, metadata: dict | None = None):
        super().__init__(data)

        # Remove singleton dimensions for easier handling
        self.data = data.squeeze()

        # User-supplied metadata (e.g. grid spec overrides)
        self._user_metadata: dict = metadata or {}

        # Set up cache for selected DataArray (when data is Dataset)
        self._selected_dataarray: xr.DataArray | None = None

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
        Extract coordinates from xarray data with metadata.

        Parameters
        ----------
        x : str, np.ndarray, or None
            X coordinate name or array.
        y : str, np.ndarray, or None
            Y coordinate name or array.
        z : str, np.ndarray, or None
            Z variable name or array.
        u : str, np.ndarray, or None
            U component name or array (for vector plots).
        v : str, np.ndarray, or None
            V component name or array (for vector plots).
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        da = self._get_dataarray(z, x, y)

        if context.is_2d:
            coords = self._extract_2d_coordinates(da, x, y, z, u, v, context)
        else:
            coords = self._extract_1d_coordinates(da, x, y, context)

        return ExtractedCoordinates(
            x=coords["x"],
            y=coords["y"],
            z=coords.get("z"),
            u=coords.get("u"),
            v=coords.get("v"),
        )

    def _extract_1d_coordinates(
        self,
        da: xr.DataArray,
        x: str | np.ndarray | None,
        y: str | np.ndarray | None,
        context: PlotContext,
    ) -> dict[str, CoordinateInfo]:
        """
        Extract coordinates for 1D plots (line, bar, geographic points).

        For GEOGRAPHIC_1D: x=longitude, y=latitude, z=data values
        For CARTESIAN_1D: x=independent variable, y=data values, z=None

        Parameters
        ----------
        da : xr.DataArray
            DataArray to extract from.
        x : str, np.ndarray, or None
            User-specified x coordinate/dimension/variable/array.
        y : str, np.ndarray, or None
            User-specified y coordinate/dimension/variable/array.
        context : PlotContext
            Plot context (CARTESIAN_1D or GEOGRAPHIC_1D).

        Returns
        -------
        dict
            Dictionary with keys 'x', 'y', and optionally 'z'.
        """
        # Step 1: Auto-detect x and y based on context
        if context == PlotContext.GEOGRAPHIC_1D:
            # Geographic: x=lon, y=lat from coordinates, z=data
            auto_x_values = None
            auto_x_name = ""
            auto_x_metadata = {}
            auto_x_units = None

            auto_y_values = None
            auto_y_name = ""
            auto_y_metadata = {}
            auto_y_units = None

            # Try to find lat/lon coordinates
            for coord_name in da.coords:
                coord = da.coords[coord_name]
                if coord_name in identifiers.LONGITUDE:
                    auto_x_values = coord.values
                    auto_x_name = coord_name
                    auto_x_metadata = dict(coord.attrs) if hasattr(coord, "attrs") else {}
                    auto_x_units = auto_x_metadata.get("units")
                elif coord_name in identifiers.LATITUDE:
                    auto_y_values = coord.values
                    auto_y_name = coord_name
                    auto_y_metadata = dict(coord.attrs) if hasattr(coord, "attrs") else {}
                    auto_y_units = auto_y_metadata.get("units")
        else:
            # Cartesian: x=independent, y=data (default roles)
            # A 0-d DataArray (e.g. from .isel(time=-1)) has no dims; wrap as
            # 1-element arrays so downstream code can treat it uniformly.
            if da.ndim == 0:
                auto_y_values = np.atleast_1d(da.values)
                auto_y_name = da.name if da.name else ""
                auto_y_metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
                auto_y_units = auto_y_metadata.get("units")

                # Use the first scalar coordinate that looks like an x-axis
                # (e.g. the time coordinate retained after .isel()).
                auto_x_values = None
                auto_x_name = ""
                auto_x_metadata = {}
                auto_x_units = None
                for coord_name, coord in da.coords.items():
                    if coord.ndim == 0:
                        auto_x_values = np.atleast_1d(coord.values)
                        auto_x_name = coord_name
                        auto_x_metadata = dict(coord.attrs) if hasattr(coord, "attrs") else {}
                        auto_x_units = auto_x_metadata.get("units")
                        break
                if auto_x_values is None:
                    auto_x_values = np.array([0])
            else:
                auto_y_values = da.values
                auto_y_name = da.name if da.name else ""
                auto_y_metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
                auto_y_units = auto_y_metadata.get("units")

                # Find dimension/coordinate for x
                auto_x_values = None
                auto_x_name = ""
                auto_x_metadata = {}
                auto_x_units = None

                if len(da.dims) == 1:
                    dim_name = da.dims[0]
                    if dim_name in da.coords:
                        coord = da.coords[dim_name]
                        auto_x_values = coord.values
                        auto_x_name = dim_name
                        auto_x_metadata = dict(coord.attrs) if hasattr(coord, "attrs") else {}
                        auto_x_units = auto_x_metadata.get("units")
                    else:
                        auto_x_values = np.arange(da.sizes[dim_name])

                if auto_x_values is None:
                    # Fallback: generate index based on y length
                    auto_x_values = np.arange(len(auto_y_values))

        # Step 2: Handle user specifications
        if context == PlotContext.GEOGRAPHIC_1D:
            # Geographic: override auto-detected if user specified
            if x is not None:
                x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(da, x)
            elif auto_x_values is not None:
                x_values = auto_x_values
                x_name = auto_x_name
                x_metadata = auto_x_metadata
                x_units = auto_x_units
            else:
                raise ValueError("Could not infer longitude coordinate. Please specify x (longitude) explicitly.")

            if y is not None:
                y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(da, y)
            elif auto_y_values is not None:
                y_values = auto_y_values
                y_name = auto_y_name
                y_metadata = auto_y_metadata
                y_units = auto_y_units
            else:
                raise ValueError("Could not infer latitude coordinate. Please specify y (latitude) explicitly.")

            # Z is the data values
            z_values = da.values
            z_name = da.name if da.name else ""
            z_metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
            z_units = z_metadata.get("units")

            z_info = CoordinateInfo(
                values=z_values,
                name=z_name,
                source_units=z_units,
                metadata=z_metadata,
            )
        else:
            # Cartesian: apply swapping logic
            # If user specifies only y and it matches a coordinate (not the data),
            # then swap: y becomes the coordinate, x becomes the data

            if x is not None and y is not None:
                x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(da, x)
                y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(da, y)
            elif y is not None and x is None:
                # Only y specified - check if it matches the auto-detected x coordinate
                y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(da, y)

                # Check if user's y matches what would be the default x (coordinate)
                if isinstance(y, str) and y in da.coords and y != da.name:
                    # User wants to use the coordinate as y, so swap: x becomes the data
                    x_values = auto_y_values
                    x_name = auto_y_name
                    x_metadata = auto_y_metadata
                    x_units = auto_y_units
                else:
                    # User's y is the data or an array, use auto x
                    x_values = auto_x_values
                    x_name = auto_x_name
                    x_metadata = auto_x_metadata
                    x_units = auto_x_units
            elif x is not None and y is None:
                # Only x specified - check if it matches the auto-detected y (data)
                x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(da, x)

                # Check if user's x matches what would be the default y (data)
                if isinstance(x, str) and x == da.name:
                    # User wants to use the data as x, so swap: y becomes the coordinate
                    y_values = auto_x_values
                    y_name = auto_x_name
                    y_metadata = auto_x_metadata
                    y_units = auto_x_units
                else:
                    # User's x is a coordinate or array, use auto y
                    y_values = auto_y_values
                    y_name = auto_y_name
                    y_metadata = auto_y_metadata
                    y_units = auto_y_units
            else:
                # Neither specified - use auto-detected
                x_values = auto_x_values
                x_name = auto_x_name
                x_metadata = auto_x_metadata
                x_units = auto_x_units

                y_values = auto_y_values
                y_name = auto_y_name
                y_metadata = auto_y_metadata
                y_units = auto_y_units

            z_info = None

        x_info = CoordinateInfo(
            values=x_values,
            name=x_name,
            source_units=x_units,
            metadata=x_metadata,
        )
        y_info = CoordinateInfo(
            values=y_values,
            name=y_name,
            source_units=y_units,
            metadata=y_metadata,
        )

        return {"x": x_info, "y": y_info, "z": z_info}

    def _extract_2d_coordinates(
        self,
        da: xr.DataArray,
        x: str | np.ndarray | None,
        y: str | np.ndarray | None,
        z: str | np.ndarray | None,
        u: str | np.ndarray | None,
        v: str | np.ndarray | None,
        context: PlotContext,
    ) -> dict[str, CoordinateInfo]:
        """
        Extract coordinates for 2D plots (heatmaps, contours, field maps) including vector components.

        Parameters
        ----------
        da : xr.DataArray
            DataArray to extract from.
        x, y, z : str, np.ndarray, or None
            User-specified coordinates.
        u, v : str, np.ndarray, or None
            User-specified vector components.
        context : PlotContext
            Plot context (CARTESIAN_2D or GEOGRAPHIC_2D).

        Returns
        -------
        dict
            Dictionary with keys 'x', 'y', 'z', 'u', 'v'.
        """
        if context == PlotContext.GEOGRAPHIC_2D:
            # Try geographic coordinate extraction first
            result = self._try_extract_geographic_2d(da, x, y, z)
            if result is not None:
                # Add empty u/v to result from geographic extraction
                result["u"] = None
                result["v"] = None
                # Now try to extract u/v
                u_info, v_info = self._extract_uv_components(u, v)
                if u_info is not None:
                    result["u"] = u_info
                    result["v"] = v_info
                return result

            # Geographic extraction found no lat/lon coordinates.  This is
            # normal for structured unstructured grids (HEALPix, reduced
            # Gaussian) where the cell dimension is 1D and lat/lon are derived
            # from the gridspec at regrid time.  Return the raw values with
            # placeholder x/y — the Regrid step will replace them.

            # Check the gridspec *before* touching da.values — for dask-backed
            # arrays, calling .values triggers a compute that can take seconds
            # even if we are about to raise an error anyway.
            if da.ndim == 1:
                from earthkit.plots.resample._regrid import _is_structured_grid

                gridspec = self.get_gridspec()
                if not _is_structured_grid(gridspec):
                    raise ValueError(
                        f"Got 1D data (shape {da.shape}) in a geographic 2D plot context "
                        "but no recognised grid specification was found. "
                        "Pass a grid spec via the data's 'ek_grid_spec' attribute or via the "
                        "metadata argument."
                    )

            if z is not None:
                z_values, z_name, z_metadata, z_units = self._resolve_coordinate_spec(da, z)
            else:
                z_values = da.values
                z_name = da.name if da.name else ""
                z_metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
                z_units = z_metadata.get("units")

            if z_values.ndim == 1:
                placeholder = np.zeros(len(z_values))
                x_info = CoordinateInfo(values=placeholder, name="", source_units=None, metadata={})
                y_info = CoordinateInfo(values=placeholder, name="", source_units=None, metadata={})
                z_info = CoordinateInfo(values=z_values, name=z_name, source_units=z_units, metadata=z_metadata)
                return {"x": x_info, "y": y_info, "z": z_info, "u": None, "v": None}

        # Cartesian 2D or fallback for geographic
        # Convention: z is 2D data field, x/y are coordinates along axes

        # Step 1: Determine z values
        if z is not None:
            z_values, z_name, z_metadata, z_units = self._resolve_coordinate_spec(da, z)
        else:
            z_values = da.values
            z_name = da.name if da.name else ""
            z_metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
            z_units = z_metadata.get("units")

        if z_values.ndim != 2:
            raise ValueError(f"Expected 2D data for 2D plot, got {z_values.ndim}D")

        ny, nx = z_values.shape

        # Step 2: Determine x and y coordinates
        # For 2D data, we expect dimension coordinates or explicit arrays

        auto_x_values = None
        auto_x_name = ""
        auto_x_metadata = {}
        auto_x_units = None

        auto_y_values = None
        auto_y_name = ""
        auto_y_metadata = {}
        auto_y_units = None

        # Try to extract dimension coordinates from the DataArray
        if len(da.dims) >= 2:
            # By convention: dims[0] is y (rows), dims[1] is x (columns)
            x_dim = da.dims[1] if len(da.dims) >= 2 else da.dims[0]
            y_dim = da.dims[0]

            if x_dim in da.coords:
                x_coord = da.coords[x_dim]
                auto_x_values = x_coord.values
                auto_x_name = x_dim
                auto_x_metadata = dict(x_coord.attrs) if hasattr(x_coord, "attrs") else {}
                auto_x_units = auto_x_metadata.get("units")
            else:
                auto_x_values = np.arange(nx)

            if y_dim in da.coords:
                y_coord = da.coords[y_dim]
                auto_y_values = y_coord.values
                auto_y_name = y_dim
                auto_y_metadata = dict(y_coord.attrs) if hasattr(y_coord, "attrs") else {}
                auto_y_units = auto_y_metadata.get("units")
            else:
                auto_y_values = np.arange(ny)

        # Generate fallbacks if not found
        if auto_x_values is None:
            auto_x_values = np.arange(nx)
        if auto_y_values is None:
            auto_y_values = np.arange(ny)

        # Handle user specifications
        if x is not None:
            x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(da, x)
        else:
            x_values = auto_x_values
            x_name = auto_x_name
            x_metadata = auto_x_metadata
            x_units = auto_x_units

        if y is not None:
            y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(da, y)
        else:
            y_values = auto_y_values
            y_name = auto_y_name
            y_metadata = auto_y_metadata
            y_units = auto_y_units

        # Apply meshgrid if needed (1D coordinates with 2D data)
        if x_values.ndim == 1 and y_values.ndim == 1:
            if len(x_values) != nx or len(y_values) != ny:
                raise ValueError(
                    f"Coordinate shapes don't match data: "
                    f"x has {len(x_values)} points (expected {nx}), "
                    f"y has {len(y_values)} points (expected {ny})"
                )
            x_values, y_values = np.meshgrid(x_values, y_values)

        # Build CoordinateInfo objects
        x_info = CoordinateInfo(
            values=x_values,
            name=x_name,
            source_units=x_units,
            metadata=x_metadata,
        )
        y_info = CoordinateInfo(
            values=y_values,
            name=y_name,
            source_units=y_units,
            metadata=y_metadata,
        )
        z_info = CoordinateInfo(
            values=z_values,
            name=z_name,
            source_units=z_units,
            metadata=z_metadata,
        )

        # Extract u and v components
        u_info, v_info = self._extract_uv_components(u, v)

        return {"x": x_info, "y": y_info, "z": z_info, "u": u_info, "v": v_info}

    def _try_extract_geographic_2d(
        self,
        da: xr.DataArray,
        x: str | np.ndarray | None,
        y: str | np.ndarray | None,
        z: str | np.ndarray | None,
    ) -> dict[str, CoordinateInfo] | None:
        """
        Try to extract geographic coordinates for 2D plots.

        Returns None if geographic coordinates cannot be identified.

        CRS-aware coordinate selection:
        - For projected CRS: Use dimension coordinates (x, y)
        - For geographic CRS or None: Use lat/lon coordinates if available

        Parameters
        ----------
        da : xr.DataArray
            DataArray to extract from.
        x, y, z : str, np.ndarray, or None
            User-specified coordinates.

        Returns
        -------
        dict or None
            Dictionary with keys 'x' (lon), 'y' (lat), 'z' if successful, else None.
        """
        # Get CRS to decide which coordinates to use
        crs = self.get_crs()

        # Check if CRS is projected (not geographic)
        is_projected = False
        if crs is not None:
            # Check if it's a projected CRS by seeing if it's NOT PlateCarree/geodetic
            try:
                # PlateCarree and other geographic CRS don't have .proj4_params with +proj=longlat
                # Projected CRS will have different projections
                if hasattr(crs, "__class__"):
                    crs_class_name = crs.__class__.__name__
                    # Common geographic CRS in cartopy
                    geographic_crs = ["PlateCarree", "Geodetic", "RotatedPole"]
                    is_projected = crs_class_name not in geographic_crs
            except (ImportError, AttributeError):
                pass

        # Look for different coordinate types
        lat_coord = None
        lon_coord = None
        x_dim_coord = None
        y_dim_coord = None

        for coord_name in da.coords:
            coord = da.coords[coord_name]
            # Only consider non-scalar coordinates
            if coord.ndim >= 1:
                # Check for pure dimension coordinates first (x, y but NOT lat/lon)
                if coord_name in ["x", "X", "xc", "projection_x_coordinate"]:
                    x_dim_coord = coord
                elif coord_name in ["y", "Y", "yc", "projection_y_coordinate"]:
                    y_dim_coord = coord
                # Then check for lat/lon coordinates
                elif coord_name in identifiers.LATITUDE:
                    lat_coord = coord
                elif coord_name in identifiers.LONGITUDE:
                    lon_coord = coord

        # Decide which coordinates to use based on CRS
        if is_projected:
            # For projected CRS: prefer dimension coordinates (x, y in projection space)
            if x_dim_coord is not None and y_dim_coord is not None:
                # Use dimension coordinates for projected data
                lon_coord = x_dim_coord
                lat_coord = y_dim_coord
            else:
                # No dimension coords found, can't extract
                return None
        else:
            # For geographic CRS or None: prefer lat/lon if they match data shape
            if lat_coord is not None and lon_coord is not None:
                # Check if lat/lon are 2D and match the data shape
                if lat_coord.ndim == 2 and lon_coord.ndim == 2:
                    if lat_coord.shape == da.shape and lon_coord.shape == da.shape:
                        # Use 2D lat/lon coordinates
                        pass  # Keep lat_coord and lon_coord as is
                    else:
                        # Shape mismatch, fall back to dimension coords
                        if x_dim_coord is not None and y_dim_coord is not None:
                            lon_coord = x_dim_coord
                            lat_coord = y_dim_coord
                        else:
                            return None
                elif lat_coord.ndim == 1 and lon_coord.ndim == 1:
                    # 1D lat/lon - these are dimension coordinates, use them
                    pass  # Keep lat_coord and lon_coord as is
                else:
                    # Dimension mismatch between lat and lon
                    return None
            elif x_dim_coord is not None and y_dim_coord is not None:
                # No lat/lon found, use dimension coordinates
                lon_coord = x_dim_coord
                lat_coord = y_dim_coord
            else:
                # Can't extract geographic coordinates
                return None

        # Extract z values
        if z is not None:
            z_values, z_name, z_metadata, z_units = self._resolve_coordinate_spec(da, z)
        else:
            z_values = da.values
            z_name = da.name if da.name else ""
            z_metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
            z_units = z_metadata.get("units")

        # Handle user-specified coordinates
        if x is not None:
            (
                lon_values,
                lon_name,
                lon_metadata,
                lon_units,
            ) = self._resolve_coordinate_spec(da, x)
        else:
            lon_values = lon_coord.values
            lon_name = lon_coord.name
            lon_metadata = dict(lon_coord.attrs) if hasattr(lon_coord, "attrs") else {}
            lon_units = lon_metadata.get("units")

        if y is not None:
            (
                lat_values,
                lat_name,
                lat_metadata,
                lat_units,
            ) = self._resolve_coordinate_spec(da, y)
        else:
            lat_values = lat_coord.values
            lat_name = lat_coord.name
            lat_metadata = dict(lat_coord.attrs) if hasattr(lat_coord, "attrs") else {}
            lat_units = lat_metadata.get("units")

        # Apply meshgrid if needed
        if z_values.ndim == 2 and lon_values.ndim == 1 and lat_values.ndim == 1:
            ny, nx = z_values.shape
            if len(lon_values) == nx and len(lat_values) == ny:
                lon_values, lat_values = np.meshgrid(lon_values, lat_values)

        # Build CoordinateInfo objects
        x_info = CoordinateInfo(
            values=lon_values,
            name=lon_name,
            source_units=lon_units,
            metadata=lon_metadata,
        )
        y_info = CoordinateInfo(
            values=lat_values,
            name=lat_name,
            source_units=lat_units,
            metadata=lat_metadata,
        )
        z_info = CoordinateInfo(
            values=z_values,
            name=z_name,
            source_units=z_units,
            metadata=z_metadata,
        )

        return {"x": x_info, "y": y_info, "z": z_info}

    def _resolve_coordinate_spec(
        self,
        da: xr.DataArray,
        spec: str | np.ndarray,
    ) -> tuple[np.ndarray, str, dict, str | None]:
        """
        Resolve a coordinate specification to (values, name, metadata, units).

        Parameters
        ----------
        da : xr.DataArray
            DataArray to extract from.
        spec : str or np.ndarray
            Coordinate specification (name or explicit array).

        Returns
        -------
        tuple
            (values, name, metadata, units)
        """
        if not isinstance(spec, str):
            # Explicit array provided (np.ndarray, pd.DatetimeIndex, list, etc.)
            return (np.atleast_1d(spec), "", {}, None)

        # spec is a string - resolve to coordinate or data variable
        if spec in da.coords:
            # It's a coordinate
            coord = da.coords[spec]
            metadata = dict(coord.attrs) if hasattr(coord, "attrs") else {}
            units = metadata.get("units")
            return (coord.values, spec, metadata, units)

        # Check if it's a data variable in the original Dataset
        if isinstance(self.data, xr.Dataset) and spec in self.data.data_vars:
            var = self.data[spec]
            metadata = dict(var.attrs) if hasattr(var, "attrs") else {}
            units = metadata.get("units")
            return (var.values, spec, metadata, units)

        # Check if it's the DataArray's own name (use its values)
        if da.name and spec == da.name:
            metadata = dict(da.attrs) if hasattr(da, "attrs") else {}
            units = metadata.get("units")
            return (da.values, spec, metadata, units)

        # Not found
        available_coords = list(da.coords.keys())
        available_vars = []
        if isinstance(self.data, xr.Dataset):
            available_vars = list(self.data.data_vars.keys())

        raise ValueError(
            f"Coordinate or variable '{spec}' not found. "
            f"Available coordinates: {available_coords}. "
            f"Available data variables: {available_vars}"
        )

    def _get_dataarray(
        self,
        z: str | np.ndarray | None,
        x: str | np.ndarray | None = None,
        y: str | np.ndarray | None = None,
    ) -> xr.DataArray:
        """
        Get DataArray from Dataset if needed.

        Parameters
        ----------
        z : str, np.ndarray, or None
            Variable name to extract if data is a Dataset.
        x, y : str, np.ndarray, or None
            May refer to variable names in 1D contexts.

        Returns
        -------
        xr.DataArray
            Extracted or existing DataArray.
        """
        if not isinstance(self.data, xr.Dataset):
            self._selected_dataarray = self.data
            return self.data

        # Data is a Dataset - need to select variable
        dataset = self.data

        # Check if x, y, or z refers to a data variable
        # Priority: z > y > x (for backward compatibility)
        var_name = None
        if isinstance(z, str) and z in dataset.data_vars:
            var_name = z
        elif isinstance(y, str) and y in dataset.data_vars:
            var_name = y
        elif isinstance(x, str) and x in dataset.data_vars:
            var_name = x

        if var_name:
            self._selected_dataarray = dataset[var_name]
            return self._selected_dataarray

        # Auto-select variable
        if len(dataset.data_vars) == 1:
            var_name = list(dataset.data_vars.keys())[0]
            self._selected_dataarray = dataset[var_name]
            return self._selected_dataarray

        # Try to find the main data variable (has coordinate dimensions)
        var_name = identifiers.identify_primary(dataset)
        if var_name and var_name in dataset.data_vars:
            self._selected_dataarray = dataset[var_name]
            return self._selected_dataarray

        raise ValueError(
            f"Multiple variables in Dataset: {list(dataset.data_vars.keys())}. "
            "Please specify which variable to plot using 'x', 'y', or 'z' parameter."
        )

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from xarray attrs.

        Lookup order:
        1. Primary variable attrs (selected DataArray or identified primary var)
        2. Scalar coordinate value (0-d coord matching key name)
        3. Variable name as fallback for the "name" key
        4. Dataset-level attrs

        Parameters
        ----------
        key : str
            Metadata attribute name (e.g. "long_name", "units", "name").
        default : Any
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value or default.
        """
        # Step 1: Primary variable attrs
        primary_da = self._get_primary_da()
        if primary_da is not None:
            value = primary_da.attrs.get(key)
            if value is not None:
                return value

        # Step 2: Scalar coordinate value (0-d coord whose name matches key)
        da_for_coords = (
            primary_da if primary_da is not None else (self.data if isinstance(self.data, xr.DataArray) else None)
        )
        if da_for_coords is not None and key in da_for_coords.coords:
            coord = da_for_coords.coords[key]
            if coord.ndim == 0:
                return _coord_item(coord)
            elif coord.ndim == 1 and coord.size == 1:
                return _coord_item(coord[0])
        if isinstance(self.data, xr.Dataset) and key in self.data.coords:
            coord = self.data.coords[key]
            if coord.ndim == 0:
                return _coord_item(coord)
            elif coord.ndim == 1 and coord.size == 1:
                return _coord_item(coord[0])

        # Step 3: Variable name as "name" fallback
        if key == "name":
            if primary_da is not None and primary_da.name:
                return primary_da.name
            if isinstance(self.data, xr.DataArray) and self.data.name:
                return self.data.name

        # Step 4: Dataset-level attrs
        if isinstance(self.data, xr.Dataset):
            value = self.data.attrs.get(key)
            if value is not None:
                return value

        return default

    def _get_primary_da(self) -> "xr.DataArray | None":
        """
        Return the primary DataArray for metadata extraction.

        Uses the already-selected DataArray if available, otherwise tries to
        identify the primary variable from a Dataset.
        """
        if self._selected_dataarray is not None:
            return self._selected_dataarray

        if isinstance(self.data, xr.DataArray):
            return self.data

        if isinstance(self.data, xr.Dataset):
            if len(self.data.data_vars) == 1:
                var_name = list(self.data.data_vars.keys())[0]
                return self.data[var_name]
            try:
                var_name = identifiers.identify_primary(self.data)
                if var_name and var_name in self.data.data_vars:
                    return self.data[var_name]
            except Exception:
                pass

        return None

    def get_datetime(self) -> dict | None:
        """
        Extract datetime information from xarray scalar time coordinates.

        Handles three cases:
        - ``valid_time``/``time`` (+ optional ``forecast_reference_time``/``initial_time``
          as base): returns ``base_time`` and ``valid_time``.
        - ``forecast_reference_time`` + ``step``: returns ``base_time``, ``lead_time``
          (as a timedelta), and the derived ``valid_time``.
        - ``step`` only: returns ``lead_time`` (as a timedelta) with no absolute times.

        Returns
        -------
        dict or None
            Dict with a subset of ``base_time``, ``valid_time``, ``lead_time`` keys,
            or None if no recognised time coordinate is found.
        """
        da = self._get_primary_da()
        if da is None:
            if isinstance(self.data, xr.Dataset):
                da = next(iter(self.data.data_vars.values()), None)
                if da is None:
                    return None
            else:
                da = self.data

        def _scalar_val(coord):
            return coord.values if coord.ndim == 0 else (coord.values[0] if coord.size == 1 else None)

        # --- absolute datetime coords ---
        datetime_coord_names = ["valid_time", "time", "forecast_reference_time", "initial_time"]
        found = {}
        for name in datetime_coord_names:
            if name in da.coords:
                val = _scalar_val(da.coords[name])
                if val is not None:
                    dt = self._parse_time_value(val)
                    if dt is not None:
                        found[name] = dt

        # --- step / lead_time coord (timedelta64) ---
        lead_time = None
        for step_name in ("step", "lead_time"):
            if step_name in da.coords:
                val = _scalar_val(da.coords[step_name])
                if val is not None:
                    lead_time = self._parse_timedelta_value(val)
                    if lead_time is not None:
                        break

        # Nothing at all found.
        if not found and lead_time is None:
            return None

        result = {}

        base = found.get("forecast_reference_time") or found.get("initial_time")
        valid = found.get("valid_time") or found.get("time")

        if base is not None:
            result["base_time"] = base
        if valid is not None:
            result["valid_time"] = valid
        elif base is not None and lead_time is not None:
            # Derive valid_time from base + step.
            result["valid_time"] = base + lead_time
        if lead_time is not None:
            result["lead_time"] = lead_time
        elif base is not None and valid is not None:
            # Derive lead_time from the two absolute times.
            result["lead_time"] = valid - base

        # Ensure base_time falls back to valid when no reference time is present.
        if "base_time" not in result and "valid_time" in result:
            result["base_time"] = result["valid_time"]

        return result if result else None

    @staticmethod
    def _parse_time_value(value):
        """Parse a numpy datetime64, Python datetime, or string into a datetime."""
        import datetime

        import numpy as np

        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, np.datetime64):
            try:
                import pandas as pd

                return pd.Timestamp(value).to_pydatetime()
            except ImportError:
                return value.astype("datetime64[ms]").astype(datetime.datetime)
        try:
            import dateutil.parser

            return dateutil.parser.parse(str(value))
        except (ValueError, TypeError, OverflowError):
            return None

    @staticmethod
    def _parse_timedelta_value(value):
        """Parse a numpy timedelta64 or Python timedelta into a datetime.timedelta."""
        import datetime

        import numpy as np

        if isinstance(value, datetime.timedelta):
            return value
        if isinstance(value, np.timedelta64):
            # Convert via integer nanoseconds to avoid overflow on large steps.
            ns = int(value.astype("timedelta64[ns]").astype(np.int64))
            return datetime.timedelta(microseconds=ns // 1000)
        return None

    def get_crs(self) -> Any | None:
        """
        Extract CRS from xarray data.

        Uses earthkit-data to convert xarray and extract projection information,
        which handles CF-convention grid_mapping and other metadata.

        Returns
        -------
        CRS or None
            Coordinate reference system (cartopy CRS) if found.
        """
        # Quick check: if 'crs' is directly in attrs, return it
        if hasattr(self.data, "attrs") and "crs" in self.data.attrs:
            return self.data.attrs["crs"]

        # Try to use earthkit-data to extract projection from CF conventions.
        # self.data is a single-variable Dataset (yielded by iter_plot_groups)
        # that includes the grid_mapping variable, so from_object sees the full
        # CF grid_mapping info without needing the original multi-var Dataset.
        try:
            import earthkit.data as ek_data

            earthkit_data = ek_data.from_object(self.data).to_fieldlist()

            # Extract projection and convert to cartopy CRS
            if hasattr(earthkit_data, "geography"):
                projection = earthkit_data.geography.projection()
                if projection is not None and hasattr(projection, "to_cartopy_crs"):
                    return projection.to_cartopy_crs()

        except (ImportError, AttributeError, Exception):
            pass

        return None

    def get_gridspec(self) -> Any | None:
        """
        Extract gridspec from xarray attrs.

        Checks the following attribute keys in order of preference:
        - ``ek_grid_spec`` (new earthkit/xarray standard, e.g. ``{"grid": "O320"}``)
        - ``gridSpec`` / ``grid_spec`` (legacy keys)

        For xarray DataArrays, also falls back to the parent Dataset's global
        attributes when the variable-level attrs do not carry the gridspec.

        Returns
        -------
        GridSpec or None
            Grid specification if found in metadata.
        """
        from earthkit.plots.sources.gridspec import GridSpec

        _KEYS = ("ek_grid_spec", "gridSpec", "grid_spec")

        def _extract(attrs):
            for key in _KEYS:
                if key in attrs:
                    raw = attrs[key]
                    if isinstance(raw, GridSpec):
                        return raw
                    spec = GridSpec._to_dict(raw)
                    if spec:
                        return GridSpec(spec)
            return None

        # User-supplied metadata takes priority.  Also accept a plain "grid"
        # key (e.g. metadata={"grid": "H512"}) as a shorthand for ek_grid_spec.
        if self._user_metadata:
            result = _extract(self._user_metadata)
            if result is not None:
                return result
            # Shorthand: {"grid": "H512", ...} passed directly
            if "grid" in self._user_metadata:
                spec = GridSpec._to_dict(self._user_metadata)
                if spec:
                    return GridSpec(spec)

        # Check attrs on self.data — covers both DataArrays (variable attrs) and
        # Datasets (global attrs). xarray DataArrays don't carry a back-reference
        # to their parent Dataset, so there is no further fallback.
        if hasattr(self.data, "attrs"):
            result = _extract(self.data.attrs)
            if result is not None:
                return result

    def _extract_uv_components(
        self,
        u: str | np.ndarray | None,
        v: str | np.ndarray | None,
    ) -> tuple[CoordinateInfo | None, CoordinateInfo | None]:
        """
        Extract U and V vector components with auto-detection.

        Parameters
        ----------
        u : str, np.ndarray, or None
            U component specification (variable name or array).
        v : str, np.ndarray, or None
            V component specification (variable name or array).

        Returns
        -------
        tuple[Optional[CoordinateInfo], Optional[CoordinateInfo]]
            (u_info, v_info) - returns (None, None) if no vector data.
        """
        # Case 1: Both u and v explicitly specified
        if u is not None and v is not None:
            # Use current DataArray or Dataset
            da = self._selected_dataarray if self._selected_dataarray is not None else self.data

            u_values, u_name, u_metadata, u_units = self._resolve_coordinate_spec(da, u)
            v_values, v_name, v_metadata, v_units = self._resolve_coordinate_spec(da, v)

            u_info = CoordinateInfo(
                values=u_values,
                name=u_name,
                source_units=u_units,
                metadata=u_metadata,
            )
            v_info = CoordinateInfo(
                values=v_values,
                name=v_name,
                source_units=v_units,
                metadata=v_metadata,
            )
            return u_info, v_info

        # Case 2: Only one specified - error
        elif u is not None or v is not None:
            raise ValueError(
                "Both u and v components must be specified for vector plots. "
                f"Got u={'specified' if u is not None else 'None'}, "
                f"v={'specified' if v is not None else 'None'}"
            )

        # Case 3: Neither specified - try auto-detection from Dataset
        elif isinstance(self.data, xr.Dataset):
            return self._try_auto_detect_uv_from_dataset()

        # No vector data
        return None, None

    def _try_auto_detect_uv_from_dataset(
        self,
    ) -> tuple[CoordinateInfo | None, CoordinateInfo | None]:
        """
        Try to auto-detect U/V component pairs from Dataset variables.

        Returns
        -------
        tuple[Optional[CoordinateInfo], Optional[CoordinateInfo]]
            (u_info, v_info) if detected, else (None, None).
        """
        if not isinstance(self.data, xr.Dataset):
            return None, None

        # Get list of variable names
        var_names = list(self.data.data_vars.keys())

        # Use identifier module to find UV pairs
        uv_pair = identifiers.find_uv_pair(var_names)

        if uv_pair is None:
            return None, None

        u_name, v_name = uv_pair

        # Extract U component
        u_var = self.data[u_name]
        u_values = u_var.values
        u_metadata = dict(u_var.attrs) if hasattr(u_var, "attrs") else {}
        u_units = u_metadata.get("units")
        u_info = CoordinateInfo(
            values=u_values,
            name=u_name,
            source_units=u_units,
            metadata=u_metadata,
        )

        # Extract V component
        v_var = self.data[v_name]
        v_values = v_var.values
        v_metadata = dict(v_var.attrs) if hasattr(v_var, "attrs") else {}
        v_units = v_metadata.get("units")
        v_info = CoordinateInfo(
            values=v_values,
            name=v_name,
            source_units=v_units,
            metadata=v_metadata,
        )

        return u_info, v_info


def _unique_coord_vals(coord):
    """Return unique values from an xarray coordinate, preserving dtype and order."""
    seen = {}
    for val in coord.values.flat:
        if val not in seen:
            seen[val] = val
    return list(seen.values())


def _get_extra_dims(da):
    """Return non-spatial, non-singleton dimension names from a DataArray."""
    from earthkit.plots import identifiers

    spatial_dims = set(identifiers.LATITUDE + identifiers.LONGITUDE)
    has_latlon = any(d in spatial_dims for d in da.dims)

    if not has_latlon:
        # Unstructured/HEALPix: the spatial dimension isn't a named lat/lon
        # dimension, so we can't safely identify "extra" dims. Yield the whole
        # field as a single panel and let the specialized-grid handlers deal
        # with it.
        return []

    return [d for d in da.dims if d not in spatial_dims and da.sizes[d] > 1]


def _iter_cartesian(da, dims):
    """
    Yield ``(key_dict, DataArray)`` for every combination of values across *dims*.

    ``key_dict`` maps each dim name to its selected value.
    """
    import itertools

    all_vals = [_unique_coord_vals(da[d]) for d in dims]
    for combo in itertools.product(*all_vals):
        sel = {d: v for d, v in zip(dims, combo)}
        yield sel, da.sel(sel)


def _grid_mapping_vars(ds: xr.Dataset) -> set:
    """Return the set of variable names that are grid_mapping references."""
    refs = set()
    for name in ds.data_vars:
        gm = ds[name].attrs.get("grid_mapping")
        if isinstance(gm, str):
            refs.update(gm.split())
    return refs


def _plottable_vars(ds: xr.Dataset) -> list:
    """Return data_vars names that are not grid_mapping coordinate variables."""
    skip = _grid_mapping_vars(ds)
    return [v for v in ds.data_vars if v not in skip]


def _single_var_dataset(ds: xr.Dataset, var: str) -> xr.Dataset:
    """Return a single-variable Dataset that retains grid_mapping variables.

    This preserves the grid_mapping variable (e.g. lambert_azimuthal_equal_area)
    alongside the requested variable so that earthkit-data can find it when
    extracting the CRS via from_object(ds).to_fieldlist().geography.projection().
    """
    gm_name = ds[var].attrs.get("grid_mapping")
    keep = [var]
    if isinstance(gm_name, str) and gm_name in ds.data_vars:
        keep.append(gm_name)
    return ds[keep]


def iter_plot_groups(data, groupby, mode, combine_vectors=False):
    """
    Yield ``(key, [DataArray, ...])`` tuples for xarray DataArray/Dataset.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Input xarray object.
    groupby : str or None
        Coordinate name to split on (one panel per unique value).
    mode : str
        ``"auto"``, ``"overlay"``, or ``"split"``.
    combine_vectors : bool, optional
        When ``True`` and *data* is a :class:`xr.Dataset`, matching U/V
        component pairs are identified and yielded as a two-variable
        sub-Dataset (so the caller can dispatch to a vector/quiver plot)
        rather than as two separate scalar panels.  Non-vector variables
        are still yielded individually.  Default is ``False``.

    Yields
    ------
    key : hashable
        Group identifier (used as panel label / title key).
    targets : list
        One or more DataArrays (or a two-variable Dataset for vector pairs
        when *combine_vectors* is ``True``) to overlay on the same subplot.
    """
    if mode == "overlay":
        if isinstance(data, xr.Dataset):
            yield None, [data[v] for v in _plottable_vars(data)]
        else:
            yield None, [data]
        return

    if mode == "split":
        if isinstance(data, xr.Dataset):
            for var in _plottable_vars(data):
                yield var, [_single_var_dataset(data, var)]
        elif groupby is not None:
            coord_vals = _unique_coord_vals(data[groupby])
            for val in coord_vals:
                yield val, [data.sel({groupby: val})]
        else:
            yield None, [data]
        return

    # mode == "auto"
    squeezed = data.squeeze() if isinstance(data, xr.DataArray) else data

    if isinstance(data, xr.Dataset):
        var_names = _plottable_vars(data)
        if len(var_names) > 1:
            # Multi-var Dataset: determine all non-spatial extra dims across variables,
            # then yield the full Cartesian product of (variable × extra_dims).
            # If groupby is set it takes priority as the sole extra split dim.
            first_da = data.squeeze()[var_names[0]]
            if groupby is not None:
                extra_dims = [groupby]
            else:
                extra_dims = _get_extra_dims(first_da)

            # When combine_vectors is requested, find and remove UV pairs first.
            vector_pair = None
            remaining_vars = var_names
            if combine_vectors:
                from earthkit.plots import identifiers

                pair = identifiers.find_uv_pair(var_names)
                if pair is not None:
                    u_name, v_name = pair
                    vector_pair = (u_name, v_name)
                    remaining_vars = [v for v in var_names if v not in pair]

            if extra_dims:
                if vector_pair is not None:
                    u_name, v_name = vector_pair
                    uv_ds = data[[u_name, v_name]]
                    first_vec_da = uv_ds.squeeze()[u_name]
                    for sel, _ in _iter_cartesian(first_vec_da, extra_dims):
                        key = ("__vector__", u_name, v_name) + tuple(sel.values())
                        yield key, [uv_ds.sel(sel)]
                for var in remaining_vars:
                    da = data.squeeze()[var]
                    for sel, slice_da in _iter_cartesian(da, extra_dims):
                        key = (var,) + tuple(sel.values())
                        yield key, [_single_var_dataset(data, var).sel(sel)]
            else:
                squeezed_ds = data.squeeze()
                if vector_pair is not None:
                    u_name, v_name = vector_pair
                    yield (
                        ("__vector__", u_name, v_name),
                        [squeezed_ds[[u_name, v_name]]],
                    )
                for var in remaining_vars:
                    yield (var,), [_single_var_dataset(squeezed_ds, var)]
            return
        # Single-var Dataset: keep as Dataset to preserve grid_mapping variables
        squeezed = _single_var_dataset(data.squeeze(), var_names[0])

    # DataArray path
    if groupby is not None:
        coord_vals = _unique_coord_vals(squeezed[groupby])
        for val in coord_vals:
            yield val, [squeezed.sel({groupby: val})]
    else:
        # Auto-detect all extra non-spatial dimensions and iterate their full
        # Cartesian product so every panel gets a 2-D (lat × lon) slice.
        extra_dims = _get_extra_dims(squeezed)
        if extra_dims:
            for sel, slice_da in _iter_cartesian(squeezed, extra_dims):
                key = tuple(sel.values()) if len(sel) > 1 else next(iter(sel.values()))
                yield key, [slice_da]
        else:
            yield None, [data]


def iter_plot_groups_2d(data, row_dim, col_dim, groupby, mode):
    """
    Yield ``(row_key, col_key, [DataArray, ...])`` tuples for structured 2-D layout.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Input xarray object.
    row_dim : str or None
        Dimension name (or ``"variable"`` for Dataset variables) to lay out
        along rows.
    col_dim : str or None
        Dimension name (or ``"variable"`` for Dataset variables) to lay out
        along columns.
    groupby : str or None
        Additional dimension to split on (ignored if covered by row/col dims).
    mode : str
        ``"auto"``, ``"overlay"``, or ``"split"``.

    Yields
    ------
    row_key : hashable
        Value identifying the row (None if row_dim not specified).
    col_key : hashable
        Value identifying the column (None if col_dim not specified).
    targets : list of xr.DataArray
        DataArrays to plot on the corresponding panel.
    """
    squeezed = data.squeeze() if isinstance(data, xr.DataArray) else data

    # Resolve variable dimension
    VARIABLE_DIM = "variable"

    def _var_vals(ds):
        return list(ds.data_vars)

    def _resolve_dim_vals(da_or_ds, dim):
        """Return list of unique values for *dim* (handles 'variable' pseudo-dim)."""
        if dim == VARIABLE_DIM:
            if isinstance(da_or_ds, xr.Dataset):
                return _var_vals(da_or_ds)
            return [da_or_ds.name]
        if isinstance(da_or_ds, xr.Dataset):
            return _unique_coord_vals(da_or_ds[_var_vals(da_or_ds)[0]][dim])
        return _unique_coord_vals(da_or_ds[dim])

    def _select(da_or_ds, dim, val):
        """Select a single value along *dim* from a DataArray or Dataset."""
        if dim == VARIABLE_DIM:
            return da_or_ds[val] if isinstance(da_or_ds, xr.Dataset) else da_or_ds
        if isinstance(da_or_ds, xr.Dataset):
            return da_or_ds.sel({dim: val})
        return da_or_ds.sel({dim: val})

    row_vals = _resolve_dim_vals(squeezed, row_dim) if row_dim else [None]
    col_vals = _resolve_dim_vals(squeezed, col_dim) if col_dim else [None]

    # Dims already consumed by the row/col axes — don't expand again
    consumed_dims = set()
    if row_dim and row_dim != "variable":
        consumed_dims.add(row_dim)
    if col_dim and col_dim != "variable":
        consumed_dims.add(col_dim)

    def _expand_slice(slice_data, row_val, col_val):
        """
        Yield ``(compound_row_key, col_val, [DataArray])`` tuples, expanding
        any remaining extra non-spatial dims into separate rows.
        """
        if isinstance(slice_data, xr.Dataset):
            # Variable-major: for each variable, expand its extra dims
            var_names = list(slice_data.data_vars)
            for var in var_names:
                da = slice_data[var]
                extra = [d for d in _get_extra_dims(da) if d not in consumed_dims]
                if extra:
                    for sel, sliced in _iter_cartesian(da, extra):
                        extra_key = tuple(sel.values())
                        compound_row = (row_val, var) + extra_key
                        yield compound_row, col_val, [sliced]
                else:
                    yield (row_val, var), col_val, [da]
        else:
            extra = [d for d in _get_extra_dims(slice_data) if d not in consumed_dims]
            if extra:
                for sel, sliced in _iter_cartesian(slice_data, extra):
                    extra_key = tuple(sel.values())
                    compound_row = (row_val,) + extra_key if row_val is not None else extra_key
                    yield compound_row, col_val, [sliced]
            else:
                yield row_val, col_val, [slice_data]

    # Collect all (row_key, col_key, targets) in row-major order so that the
    # figure grid is laid out correctly (all columns for a given row together).
    all_groups = []
    for col_val in col_vals:
        for row_val in row_vals:
            slice_data = squeezed
            if row_dim and row_val is not None:
                slice_data = _select(slice_data, row_dim, row_val)
            if col_dim and col_val is not None:
                slice_data = _select(slice_data, col_dim, col_val)
            for entry in _expand_slice(slice_data, row_val, col_val):
                all_groups.append(entry)

    # Re-order so that we iterate row-major (all cols for row 0, then row 1, …)
    row_keys_seen = list(dict.fromkeys(rk for rk, _, _ in all_groups))
    col_keys_seen = list(dict.fromkeys(ck for _, ck, _ in all_groups))
    group_map = {(rk, ck): tgts for rk, ck, tgts in all_groups}
    for rk in row_keys_seen:
        for ck in col_keys_seen:
            if (rk, ck) in group_map:
                yield rk, ck, group_map[(rk, ck)]

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


class XarrayExtractor(BaseExtractor):
    """
    Strategy for extracting coordinates from xarray DataArrays and Datasets.

    Handles rich metadata, coordinate systems, and multi-dimensional data.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Xarray data structure.
    """

    def __init__(self, data: xr.DataArray | xr.Dataset):
        super().__init__(data)

        # Remove singleton dimensions for easier handling
        self.data = data.squeeze()

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
                    auto_x_metadata = (
                        dict(coord.attrs) if hasattr(coord, "attrs") else {}
                    )
                    auto_x_units = auto_x_metadata.get("units")
                elif coord_name in identifiers.LATITUDE:
                    auto_y_values = coord.values
                    auto_y_name = coord_name
                    auto_y_metadata = (
                        dict(coord.attrs) if hasattr(coord, "attrs") else {}
                    )
                    auto_y_units = auto_y_metadata.get("units")
        else:
            # Cartesian: x=independent, y=data (default roles)
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
                    auto_x_metadata = (
                        dict(coord.attrs) if hasattr(coord, "attrs") else {}
                    )
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
                x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(
                    da, x
                )
            elif auto_x_values is not None:
                x_values = auto_x_values
                x_name = auto_x_name
                x_metadata = auto_x_metadata
                x_units = auto_x_units
            else:
                raise ValueError(
                    "Could not infer longitude coordinate. "
                    "Please specify x (longitude) explicitly."
                )

            if y is not None:
                y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(
                    da, y
                )
            elif auto_y_values is not None:
                y_values = auto_y_values
                y_name = auto_y_name
                y_metadata = auto_y_metadata
                y_units = auto_y_units
            else:
                raise ValueError(
                    "Could not infer latitude coordinate. "
                    "Please specify y (latitude) explicitly."
                )

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
                x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(
                    da, x
                )
                y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(
                    da, y
                )
            elif y is not None and x is None:
                # Only y specified - check if it matches the auto-detected x coordinate
                y_values, y_name, y_metadata, y_units = self._resolve_coordinate_spec(
                    da, y
                )

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
                x_values, x_name, x_metadata, x_units = self._resolve_coordinate_spec(
                    da, x
                )

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
                auto_x_metadata = (
                    dict(x_coord.attrs) if hasattr(x_coord, "attrs") else {}
                )
                auto_x_units = auto_x_metadata.get("units")
            else:
                auto_x_values = np.arange(nx)

            if y_dim in da.coords:
                y_coord = da.coords[y_dim]
                auto_y_values = y_coord.values
                auto_y_name = y_dim
                auto_y_metadata = (
                    dict(y_coord.attrs) if hasattr(y_coord, "attrs") else {}
                )
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
        if isinstance(spec, np.ndarray):
            # Explicit array provided
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

        For Datasets, extracts metadata from the selected variable (if available).
        For DataArrays, extracts from the DataArray attrs.

        Can also extract metadata for specific coordinates/variables when key matches
        a coordinate or variable name.

        Parameters
        ----------
        key : str
            Metadata key or variable/coordinate name.
        default : Any
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value, coordinate attrs dict, or default.
        """
        # First check if key is a coordinate or variable name
        # If so, return its attrs as a dict
        if isinstance(self.data, xr.Dataset):
            # Check in data variables
            if key in self.data.data_vars:
                return dict(self.data[key].attrs) if self.data[key].attrs else {}
            # Check in coordinates
            if key in self.data.coords:
                return (
                    dict(self.data.coords[key].attrs)
                    if self.data.coords[key].attrs
                    else {}
                )
        elif isinstance(self.data, xr.DataArray):
            # Check in coordinates
            if key in self.data.coords:
                return (
                    dict(self.data.coords[key].attrs)
                    if self.data.coords[key].attrs
                    else {}
                )
            # Check in dimensions
            if key in self.data.dims and key in self.data.coords:
                return (
                    dict(self.data.coords[key].attrs)
                    if self.data.coords[key].attrs
                    else {}
                )

        # Not a coordinate/variable name - look for metadata key in attrs
        # Prefer selected DataArray attrs if available (for Dataset case)
        if self._selected_dataarray is not None:
            if hasattr(self._selected_dataarray, "attrs"):
                return self._selected_dataarray.attrs.get(key, default)

        # Fall back to main data attrs
        if hasattr(self.data, "attrs"):
            return self.data.attrs.get(key, default)

        return default

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

        # Try to use earthkit-data to extract projection from CF conventions
        try:
            import earthkit.data as ek_data

            # Get the data to convert
            # For Datasets, pass the whole Dataset to preserve grid_mapping references
            # For DataArrays, pass the DataArray directly
            if isinstance(self.data, xr.Dataset):
                data_to_convert = self.data
            else:
                data_to_convert = self.data

            # Convert to earthkit-data object
            earthkit_data = ek_data.from_object(data_to_convert)

            # Extract projection and convert to cartopy CRS
            if hasattr(earthkit_data, "projection"):
                projection = earthkit_data.projection()
                if projection is not None and hasattr(projection, "to_cartopy_crs"):
                    return projection.to_cartopy_crs()

        except (ImportError, AttributeError, Exception):
            # If earthkit-data is not available or conversion fails, return None
            pass

        return None

    def get_gridspec(self) -> Any | None:
        """
        Extract gridspec from xarray attrs.

        Returns
        -------
        GridSpec or None
            Grid specification if found in metadata.
        """
        if hasattr(self.data, "attrs"):
            if "gridSpec" in self.data.attrs:
                return self.data.attrs["gridSpec"]
            elif "grid_spec" in self.data.attrs:
                return self.data.attrs["grid_spec"]

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
            da = (
                self._selected_dataarray
                if self._selected_dataarray is not None
                else self.data
            )

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

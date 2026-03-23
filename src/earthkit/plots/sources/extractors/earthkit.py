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

import cartopy.crs as ccrs
import numpy as np

from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates
from earthkit.plots.sources.extractors.base import BaseExtractor


def iter_plot_groups(fields, groupby, mode, combine_vectors=False):
    """
    Yield ``(key, [Field, ...])`` tuples for an earthkit FieldList.

    Parameters
    ----------
    fields : earthkit.data.FieldList
        Input FieldList.
    groupby : str or None
        Metadata key to split on (one panel per unique value).
    mode : str
        ``"auto"``, ``"overlay"``, or ``"split"``.
    combine_vectors : bool, optional
        When ``True``, matching U/V component pairs are identified via
        ``parameter.variable`` and yielded together as a two-field list
        so the caller can dispatch them to a quiver plot.  Default ``False``.

    Yields
    ------
    key : hashable
        Group identifier.
    targets : list of earthkit Field
        One or more fields to overlay on the same subplot.
    """
    from earthkit.plots.utils import iter_utils

    if mode == "overlay":
        yield None, list(fields)
        return

    if mode == "split":
        for i, field in enumerate(fields):
            yield i, [field]
        return

    # mode == "auto"
    if groupby:
        # Support xarray-style dotted keys like "time.valid_datetime".
        # earthkit-data's Field.metadata() only accepts the leaf key, but
        # FieldList.sel() key format has changed across versions: older versions
        # require the full dotted key; newer versions require the leaf key.
        # We always use the leaf for metadata extraction, and try the leaf for
        # sel first, falling back to the full dotted key if it yields nothing.
        meta_key = groupby.split(".")[-1] if "." in groupby else groupby
        unique_values = iter_utils.flatten(field.metadata(meta_key) for field in fields)
        unique_values = [v for v in dict.fromkeys(unique_values) if v is not None]
        for val in unique_values:
            group_list = list(fields.sel(**{meta_key: val}))
            if not group_list and meta_key != groupby:
                group_list = list(fields.sel(**{groupby: val}))
            if group_list:
                yield val, group_list
    else:
        # Group fields by variable so that all fields of the same variable
        # share a colorbar.  Try parameter.variable first (the canonical
        # earthkit key), then fall back to short_name and paramId.
        def _var_key(field):
            for key in ("parameter.variable", "short_name", "paramId"):
                try:
                    val = field.metadata(key)
                    if val is not None:
                        return (key, val)
                except Exception:
                    pass
            return ("__index__", id(field))

        # Preserve insertion order of first occurrence
        seen = {}
        for field in fields:
            k = _var_key(field)
            seen.setdefault(k, []).append(field)

        if len(seen) > 1:
            # Multiple variables — optionally combine UV pairs, then yield
            # each variable's fields as individual panels.
            var_names = [k[1] for k in seen]

            vector_pair = None
            remaining_keys = list(seen.keys())
            if combine_vectors:
                from earthkit.plots import identifiers

                pair = identifiers.find_uv_pair(var_names)
                if pair is not None:
                    u_name, v_name = pair
                    vector_pair = (u_name, v_name)
                    remaining_keys = [k for k in seen if k[1] not in pair]

            if vector_pair is not None:
                u_name, v_name = vector_pair
                u_key = next(k for k in seen if k[1] == u_name)
                v_key = next(k for k in seen if k[1] == v_name)
                u_fields = seen[u_key]
                v_fields = seen[v_key]
                # Pair up U and V fields positionally (one panel per pair)
                for u_field, v_field in zip(u_fields, v_fields):
                    yield ("__vector__", u_name, v_name), [u_field, v_field]

            for k in remaining_keys:
                group_fields = seen[k]
                var_name = k[1]
                if len(group_fields) == 1:
                    yield var_name, group_fields
                else:
                    for field in group_fields:
                        yield var_name, [field]
        else:
            # Single variable or unable to detect — one panel per field.
            for field in fields:
                yield None, [field]


class EarthkitExtractor(BaseExtractor):
    """
    Extractor for earthkit.data objects (Field, FieldList, etc.).

    Handles geographic data with built-in coordinate extraction
    and metadata access.
    """

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
        Extract coordinates from earthkit data with metadata.

        Parameters
        ----------
        x : str, np.ndarray, or None
            X coordinate specification.
        y : str, np.ndarray, or None
            Y coordinate specification.
        z : str, np.ndarray, or None
            Z variable name or array.
        u : str, np.ndarray, or None
            U component specification (for vector plots).
        v : str, np.ndarray, or None
            V component specification (for vector plots).
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        # Extract z values (the field data)
        z_name = ""
        if isinstance(z, str):
            # Select specific variable by name
            z_values = self.data.sel(short_name=z).to_numpy(flatten=False)
            z_name = z
        elif isinstance(z, np.ndarray):
            z_values = z
        else:
            # Use all data
            z_values = self.data.to_numpy(flatten=False)

        # Extract x, y coordinates
        if isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
            # Explicit coordinates provided
            x_values = x
            y_values = y
        else:
            # Extract from earthkit data
            x_values, y_values = self._extract_coordinates_from_data()

        # Infer coordinate names based on grid type
        x_name, y_name = self._infer_coordinate_names()

        # Build CoordinateInfo objects
        # For earthkit data, extract all metadata and pass it to z dimension
        # since earthkit objects are 2D fields with global metadata (not data cubes)
        z_metadata = self._extract_all_metadata()
        units = z_metadata.get("units")

        x_info = CoordinateInfo(
            values=x_values,
            name=x_name,
            source_units=None,
            metadata={},
        )
        y_info = CoordinateInfo(
            values=y_values,
            name=y_name,
            source_units=None,
            metadata={},
        )
        z_info = None
        if z_values is not None:
            z_info = CoordinateInfo(
                values=z_values,
                name=z_name,
                source_units=units,
                metadata=z_metadata,  # Pass all global metadata to z dimension
            )

        # Extract u and v components
        u_info, v_info = self._extract_uv_components(u, v)

        return ExtractedCoordinates(x=x_info, y=y_info, z=z_info, u=u_info, v=v_info)

    def _extract_coordinates_from_data(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract coordinates from earthkit data object in native CRS.

        Strategy:
        1. Try to_points() first - returns native coordinates (x/y for projected, lon/lat for geographic)
        2. Fall back to to_latlon() if to_points() not implemented
        3. Generate indices as last resort

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (x, y) arrays in the data's native CRS.
        """
        # Try to_points method first - gives native coordinates
        if hasattr(self.data.geography, "points"):
            try:
                return self.data.geography.points(flatten=False)
            except (AttributeError, NotImplementedError, ValueError):
                pass

        # Fallback to to_latlon if to_points not available
        if hasattr(self.data.geography, "latlons"):
            try:
                lats, lons = self.data.geography.latlons(flatten=False)
                return lons, lats  # Return in (x, y) order as (lon, lat)
            except (AttributeError, NotImplementedError, ValueError):
                pass

        # Last resort: generate index arrays
        z_values = self.data.to_numpy(flatten=False)
        if z_values.ndim == 2:
            ny, nx = z_values.shape
            x_values = np.arange(nx)
            y_values = np.arange(ny)
            return x_values, y_values
        elif z_values.ndim == 1:
            x_values = np.arange(len(z_values))
            y_values = np.zeros(len(z_values))
            return x_values, y_values

        raise ValueError("Could not extract coordinates from earthkit data")

    def _infer_coordinate_names(self) -> tuple[str, str]:
        """
        Infer coordinate names based on earthkit data grid type.

        For regular_ll grids: returns ("longitude", "latitude")
        For other grids: returns ("x", "y")

        Returns
        -------
        tuple[str, str]
            (x_name, y_name) coordinate names.
        """
        # Try to get grid_type metadata
        grid_type = self.get_metadata("gridType")

        # For regular lat-lon grids, use geographic names
        if grid_type == "regular_ll":
            return ("longitude", "latitude")

        # For other grid types (projected, reduced, etc.), use generic x/y
        return ("x", "y")

    def _extract_all_metadata(self) -> dict:
        """
        Extract all available metadata from earthkit data as a dictionary.

        This allows z.metadata() to access any field metadata without
        needing to know the keys in advance.

        Returns
        -------
        dict
            Dictionary of all available metadata from the earthkit field.
        """
        metadata_dict = {}

        if not hasattr(self.data, "metadata"):
            return metadata_dict

        # Common GRIB keys to extract
        # These are the most commonly used metadata keys
        common_keys = [
            "units",
            "long_name",
            "short_name",
            "name",
            "standard_name",
            "param",
            "paramId",
            "centre",
            "centreDescription",
            "dataDate",
            "dataTime",
            "validityDate",
            "validityTime",
            "stepRange",
            "level",
            "levelType",
            "gridType",
            "Nx",
            "Ny",
            "numberOfPoints",
        ]

        for key in common_keys:
            try:
                value = self.data.metadata(key)
                if value is not None:
                    metadata_dict[key] = value
            except (AttributeError, KeyError, NotImplementedError):
                pass

        return metadata_dict

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from earthkit data.

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
        if hasattr(self.data, "metadata"):
            try:
                value = self.data.metadata(key)
                if value is not None:
                    return value
            except (AttributeError, KeyError, NotImplementedError):
                pass

        if hasattr(self.data, "get"):
            try:
                value = self.data.get(key)
                if value is not None:
                    return value
            except (AttributeError, KeyError, NotImplementedError):
                pass

        return default

    def get_crs(self) -> Any | None:
        """
        Extract CRS from earthkit data.

        Returns
        -------
        CRS or None
            Coordinate reference system.
        """
        if hasattr(self.data, "geography"):
            try:
                proj = self.data.geography.projection()
                if hasattr(proj, "to_cartopy_crs"):
                    return proj.to_cartopy_crs()
                return proj
            except (AttributeError, NotImplementedError):
                pass

        # Default to PlateCarree for geographic data
        return ccrs.PlateCarree()

    def get_gridspec(self) -> Any | None:
        """
        Extract gridspec from earthkit data.

        Returns
        -------
        GridSpec or None
            Grid specification for regridding.
        """
        # Import gridspec utilities
        from earthkit.plots.sources.gridspec import get_grid_spec

        try:
            return get_grid_spec(self.data)
        except (AttributeError, ImportError):
            return None

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
            U component specification (parameter name or array).
        v : str, np.ndarray, or None
            V component specification (parameter name or array).

        Returns
        -------
        tuple[Optional[CoordinateInfo], Optional[CoordinateInfo]]
            (u_info, v_info) - returns (None, None) if no vector data.
        """
        # Case 1: Both u and v explicitly specified
        if u is not None and v is not None:
            if isinstance(u, str) and isinstance(v, str):
                # Extract by parameter name
                try:
                    u_field = self.data.sel(short_name=u)
                    v_field = self.data.sel(short_name=v)
                except (AttributeError, KeyError):
                    # Try param instead of short_name
                    try:
                        u_field = self.data.sel(param=u)
                        v_field = self.data.sel(param=v)
                    except (AttributeError, KeyError):
                        raise ValueError(
                            f"Could not find u='{u}' and v='{v}' in data. "
                            "Try using 'short_name' or 'param' selectors."
                        )

                u_values = u_field.to_numpy(flatten=False)
                v_values = v_field.to_numpy(flatten=False)

                # Extract metadata
                u_metadata = self._extract_all_metadata_from_field(u_field)
                v_metadata = self._extract_all_metadata_from_field(v_field)
                u_units = u_metadata.get("units")
                v_units = v_metadata.get("units")

                u_info = CoordinateInfo(
                    values=u_values,
                    name=u,
                    source_units=u_units,
                    metadata=u_metadata,
                )
                v_info = CoordinateInfo(
                    values=v_values,
                    name=v,
                    source_units=v_units,
                    metadata=v_metadata,
                )
                return u_info, v_info

            elif isinstance(u, np.ndarray) and isinstance(v, np.ndarray):
                # Explicit arrays provided
                u_info = CoordinateInfo(
                    values=u,
                    name="",
                    source_units=None,
                    metadata={},
                )
                v_info = CoordinateInfo(
                    values=v,
                    name="",
                    source_units=None,
                    metadata={},
                )
                return u_info, v_info

        # Case 2: Only one specified - error
        elif u is not None or v is not None:
            raise ValueError(
                "Both u and v components must be specified for vector plots. "
                f"Got u={'specified' if u is not None else 'None'}, "
                f"v={'specified' if v is not None else 'None'}"
            )

        # Case 3: Neither specified - try auto-detection from FieldList
        else:
            return self._try_auto_detect_uv_from_fieldlist()

        # No vector data
        return None, None

    def _try_auto_detect_uv_from_fieldlist(
        self,
    ) -> tuple[CoordinateInfo | None, CoordinateInfo | None]:
        """
        Try to auto-detect U/V from earthkit FieldList.

        Uses data.get("parameter.variable") to retrieve parameter names for
        all fields, then identifies UV pairs via the identifiers module.

        Returns
        -------
        tuple[Optional[CoordinateInfo], Optional[CoordinateInfo]]
            (u_info, v_info) if detected, else (None, None).
        """
        from earthkit.plots import identifiers

        try:
            params = self.data.get("parameter.variable")
        except (AttributeError, KeyError, TypeError):
            return None, None

        if not params:
            return None, None

        # Find UV pair
        uv_pair = identifiers.find_uv_pair(params)
        if uv_pair is None:
            return None, None

        u_param, v_param = uv_pair

        u_field = self.data.sel(**{"parameter.variable": u_param})
        v_field = self.data.sel(**{"parameter.variable": v_param})

        if not u_field or not v_field:
            return None, None

        # Build CoordinateInfo objects
        u_values = u_field.to_numpy(flatten=False).squeeze()
        u_metadata = self._extract_all_metadata_from_field(u_field)
        u_units = u_metadata.get("units")
        u_info = CoordinateInfo(
            values=u_values,
            name=u_param,
            source_units=u_units,
            metadata=u_metadata,
        )

        v_values = v_field.to_numpy(flatten=False).squeeze()
        v_metadata = self._extract_all_metadata_from_field(v_field)
        v_units = v_metadata.get("units")
        v_info = CoordinateInfo(
            values=v_values,
            name=v_param,
            source_units=v_units,
            metadata=v_metadata,
        )

        return u_info, v_info

    def _extract_all_metadata_from_field(self, field) -> dict:
        """
        Extract all metadata from a single field.

        Parameters
        ----------
        field : earthkit.data Field
            Single field to extract metadata from.

        Returns
        -------
        dict
            Dictionary of all metadata.
        """
        metadata = {}
        if hasattr(field, "metadata"):
            # Common GRIB keys
            keys = [
                "short_name",
                "param",
                "level",
                "levelist",
                "units",
                "long_name",
                "standard_name",
                "grid_type",
            ]
            for key in keys:
                try:
                    value = field.metadata(key)
                    if value is not None:
                        metadata[key] = value
                except (AttributeError, KeyError):
                    pass
        return metadata

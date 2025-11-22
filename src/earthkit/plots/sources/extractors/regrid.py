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

import re
from abc import ABCMeta, abstractmethod
from typing import Any, Optional

import numpy as np

HEALPIX_PATTERN = re.compile(r"^[Hh]\d+$")
RGG_PATTERN = re.compile(r"^[OoNn]\d+$")

# TODO: refactor this when the gridSpec is implemented in earthkit


def get_points(dx):
    """Get points for a grid with a given resolution."""
    lat_v = np.linspace(90, -90, int(180 / dx) + 1)
    lon_v = np.linspace(0, 360 - dx, int(360 / dx))
    lon, lat = np.meshgrid(lon_v, lat_v)
    return lon, lat


class GridIdentifier(metaclass=ABCMeta):
    """
    A specification of a grid used in a Source.

    Parameters
    ----------
    data : Any
        The data object containing the grid metadata.
    """

    GRIDSPEC_KEYS: Optional[list[str]] = None
    NAME: str
    LONG_NAME: str

    @classmethod
    def from_data(cls, data: Any) -> Optional["GridIdentifier"]:
        """
        Identify and create a GridIdentifier object from the given data.

        Parameters
        ----------
        data : Any
            The data object containing the grid metadata.

        Returns
        -------
        GridIdentifier or None
            A GridIdentifier subclass instance if a matching grid type is found,
            None otherwise.
        """
        d = cls._first(data)
        for gs in GRIDS:
            if gs.type_match(d):
                return gs(d)
        return None

    def __init__(self, data: Any) -> None:
        self.data = data

    @staticmethod
    @abstractmethod
    def type_match(data: Any) -> bool:
        """
        Check if the given data matches this grid type.

        Parameters
        ----------
        data : Any
            The data object to check.

        Returns
        -------
        bool
            True if the data matches this grid type, False otherwise.
        """
        pass

    @staticmethod
    def _guess_grid(data: Any) -> Optional[str]:
        """
        Try to guess the grid type from metadata.

        Parameters
        ----------
        data : Any
            The data object to inspect.

        Returns
        -------
        str or None
            The grid type string if found, None otherwise.
        """
        if isinstance(data, dict):
            gs = data.get("gridSpec")
            if gs:
                grid = gs.get("grid")
                if grid:
                    return grid

            return data.get("gridType")

        data = GridIdentifier._first(data)

        # ecCodes does not yet support the gridSpec key and prints a warning
        # when accessing it. We only try to get it for a non-GRIB field
        gs = None
        if hasattr(data, "_metadata") and data._metadata.data_format() != "grib":
            gs = data.metadata("gridSpec", default=None)

        if gs:
            grid = gs.get("grid")
            if grid:
                return grid

        grid = data.metadata("gridType", default=None)
        return grid

    def _from_gridspec(self, data: Any) -> Optional[dict[str, Any]]:
        """
        Extract grid specification from data metadata.

        Parameters
        ----------
        data : Any
            The data object to extract gridSpec from.

        Returns
        -------
        dict or None
            Dictionary containing grid specification if found, None otherwise.
        """
        def _get_first(x: Any) -> Any:
            if isinstance(x, list):
                return x[0]
            return x

        # try gridSpec metadata key
        # ecCodes does not yet support the gridSpec key and prints a warning
        # when accessing it. We only try to get it for a non-GRIB field
        gs = None
        if hasattr(data, "_metadata") and data._metadata.data_format() != "grib":
            gs = data.metadata("gridSpec", default=None)

        if gs:
            return _get_first(gs)

        # try method on metadata object
        if self.GRIDSPEC_KEYS and hasattr(data, "metadata"):
            try:
                # Get the gridspec from metadata
                gridspec_data = data.metadata("gridSpec", default=None)
                if gridspec_data:
                    gs = {k: gridspec_data.get(k) for k in self.GRIDSPEC_KEYS if gridspec_data.get(k) is not None}
                    if gs:
                        return _get_first(gs)
            except Exception:
                pass

        return None
    
    def to_regular_ll(self, x, y, values, target_resolution=0.1) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Regrid the data values to a regular lat-lon grid.
        
        Parameters
        ----------
        values : numpy.ndarray
            The data values to regrid.
        target_resolution : float, optional
            The target resolution in degrees for the regular lat-lon grid. Default is 0.2 degrees.

        Returns
        -------
        tuple of numpy.ndarray
            A tuple containing the longitude values, latitude values, and regridded data values.
        """
        try:
            import earthkit.regrid
        except ImportError:
            raise ImportError(
                f"earthkit-regrid is required to regrid a {self.LONG_NAME} grid.\n"
                "You can install it via pip:\n\n    pip install earthkit-regrid"
            )
        longitudes, latitudes = get_points(target_resolution)
        import time
        _start = time.time()
        def interpolate(v):
            return earthkit.regrid.interpolate(
                v,
                self.to_dict(),
                {"grid": [target_resolution] * 2},
            )
    
        if values.ndim == 2:  # In case of FieldList
            values = np.array([interpolate(v) for v in values])
        else:
            values = interpolate(values)
        
        return longitudes, latitudes, values
    
    def auto_regrid(self, x, y, values, **kwargs) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Automatically regrid the data values to a regular lat-lon grid if not already on one.
        
        Parameters
        ----------
        x : numpy.ndarray
            The x-coordinate values (e.g., longitudes).
        y : numpy.ndarray
            The y-coordinate values (e.g., latitudes).
        values : numpy.ndarray
            The data values to regrid.
        
        Returns
        -------
        tuple of numpy.ndarray
            A tuple containing the longitude values, latitude values, and regridded data values.
        """
        return self.to_regular_ll(x, y, values, **kwargs)

    @abstractmethod
    def to_dict(self) -> Optional[dict[str, Any]]:
        """
        Convert the grid specification to a dictionary.

        Returns
        -------
        dict or None
            Dictionary representation of the grid specification if available,
            None otherwise.
        """
        pass

    @staticmethod
    def _first(data: Any) -> Any:
        """
        Get the first element if data is a sequence, otherwise return data as-is.

        Parameters
        ----------
        data : Any
            The data object.

        Returns
        -------
        Any
            First element if data has length, otherwise the data itself.
        """
        # Special handling for xarray Dataset - don't try to index
        try:
            import xarray as xr
            if isinstance(data, xr.Dataset):
                return data
        except ImportError:
            pass

        if hasattr(data, "__len__") and not isinstance(data, (str, dict)):
            return data[0]
        return data

    @property
    def name(self) -> str:
        """Return the name of this grid type."""
        return self.NAME


class ReducedGG(GridIdentifier):
    """
    A reduced Gaussian grid specification.

    Supports both octahedral (O) and standard (N) reduced Gaussian grids.
    """

    GRIDSPEC_KEYS = ["grid"]
    NAME = "reduced_gg"
    LONG_NAME = "Reduced Gaussian"

    def to_dict(self) -> Optional[dict[str, Any]]:
        """
        Convert the reduced Gaussian grid to a dictionary.

        Returns
        -------
        dict or None
            Dictionary with 'grid' key (e.g., {'grid': 'O1280'}) if the grid
            specification can be determined, None otherwise.
        """
        d = self._first(self.data)

        gs = self._from_gridspec(d)
        if gs:
            return gs

        # try to build from raw metadata keys
        n = d.metadata("N", default=None)
        if n is not None:
            if d.metadata("isOctahedral", default=0):
                g = f"O{n}"
            else:
                g = f"N{n}"

            return {"grid": g}

        grid = GridIdentifier._guess_grid(d)
        if isinstance(grid, str) and RGG_PATTERN.match(grid):
            return {"grid": grid.upper()}

        return None

    @staticmethod
    def type_match(data: Any) -> bool:
        """
        Check if the data represents a reduced Gaussian grid.

        Parameters
        ----------
        data : Any
            The data object to check.

        Returns
        -------
        bool
            True if the data is a reduced Gaussian grid, False otherwise.
        """
        try:
            grid = GridIdentifier._guess_grid(data)
            if isinstance(grid, str):
                if grid == "reduced_gg":
                    return True
                if RGG_PATTERN.match(grid):
                    return True
        except Exception:
            pass

        return False

    def grid_cells(
        self,
        subplot: Any,
        dimension_set: Any,
        z_values: np.ndarray,
        style: Any,
        method_name: str,
        kwargs: dict[str, Any],
    ) -> Any:
        """
        Plot octahedral/reduced Gaussian grid data using grid cells visualization.

        Octahedral grids are used for certain types of global atmospheric models
        and require specialized plotting functions.

        Parameters
        ----------
        subplot : Subplot
            The subplot instance to plot on.
        dimension_set : DimensionSet
            The dimension set containing the data.
        z_values : array-like
            The z values to plot.
        style : Style
            The style object for plotting.
        method_name : str
            The plotting method name (unused, for compatibility).
        kwargs : dict
            Keyword arguments for plotting.

        Returns
        -------
        Any
            The matplotlib mappable object.
        """
        import warnings
        from earthkit.plots.geo import octahedral
        from earthkit.plots.sources.core import DimensionSet

        warnings.warn(
            "Octahedral grid cell plotting is experimental and may be very slow. "
            "It is not recommended for anything other than very low resolution grids."
        )

        # Extract x and y values from dimension set
        if isinstance(dimension_set, DimensionSet):
            x_values = dimension_set.x.values
            y_values = dimension_set.y.values
        else:
            # Legacy source compatibility
            x_values = dimension_set.x_values
            y_values = dimension_set.y_values

        return octahedral.plot_octahedral_grid(
            x_values,
            y_values,
            z_values,
            subplot.ax,
            style=style,
            **kwargs,
        )


class HEALPix(GridIdentifier):
    """
    A HEALPix grid specification.

    HEALPix (Hierarchical Equal Area isoLatitude Pixelation) is a spherical
    pixelation scheme commonly used for cosmic microwave background data and
    other astrophysical applications.
    """

    GRIDSPEC_KEYS = ["grid", "ordering"]
    NAME = "healpix"
    LONG_NAME = "HEALPix"

    def to_dict(self) -> Optional[dict[str, Any]]:
        """
        Convert the HEALPix grid to a dictionary.

        Returns
        -------
        dict or None
            Dictionary with 'grid' and 'ordering' keys (e.g., {'grid': 'H32',
            'ordering': 'nested'}) if the grid specification can be determined,
            None otherwise.
        """
        d = self._first(self.data)

        gs = self._from_gridspec(d)
        if gs:
            return gs

        # try to build from raw metadata keys
        n = d.metadata("Nside", default=None)
        o = d.metadata("orderingConvention", default=None)
        if isinstance(o, list):
            o = o[0]
            n = n[0]
        if n is not None and o is not None:
            return {"grid": f"H{n}", "ordering": o}

        return None

    @staticmethod
    def type_match(data: Any) -> bool:
        """
        Check if the data represents a HEALPix grid.

        Parameters
        ----------
        data : Any
            The data object to check.

        Returns
        -------
        bool
            True if the data is a HEALPix grid, False otherwise.
        """
        try:
            grid = GridIdentifier._guess_grid(data)
            if isinstance(grid, str):
                if grid == "healpix":
                    return True
                if HEALPIX_PATTERN.match(grid):
                    return True
        except Exception:
            pass
        return False

    def grid_cells(
        self,
        subplot: Any,
        dimension_set: Any,
        z_values: np.ndarray,
        style: Any,
        method_name: str,
        kwargs: dict[str, Any],
    ) -> Any:
        """
        Plot HEALPix grid data using grid cells visualization.

        HEALPix (Hierarchical Equal Area isoLatitude Pixelization) grids require
        special handling due to their unique coordinate system and pixel structure.

        Parameters
        ----------
        subplot : Subplot
            The subplot instance to plot on.
        dimension_set : DimensionSet
            The dimension set containing the data.
        z_values : array-like
            The z values to plot.
        style : Style
            The style object for plotting.
        method_name : str
            The plotting method name (unused, for compatibility).
        kwargs : dict
            Keyword arguments for plotting.

        Returns
        -------
        Any
            The matplotlib mappable object.
        """
        from earthkit.plots.geo import healpix

        # Determine if the grid uses nested ordering
        convention = dimension_set.metadata("orderingConvention")
        if isinstance(convention, list):
            convention = convention[0]
        nest = convention == "nested"

        # Set the coordinate transformation
        kwargs["transform"] = subplot.crs

        # Use the HEALPix-specific plotting function
        return healpix.nnshow(z_values, ax=subplot.ax, nest=nest, style=style, **kwargs)


GRIDS: list[type[GridIdentifier]] = [HEALPix, ReducedGG]
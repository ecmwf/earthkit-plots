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

from functools import cached_property

import cartopy.crs as ccrs
import numpy as np

from earthkit.plots.identifiers import U, V
from earthkit.plots.schemas import schema
from earthkit.plots.sources.single import SingleSource

_NO_EARTHKIT_REGRID = False
try:
    import earthkit.regrid
except ImportError:
    _NO_EARTHKIT_REGRID = True


VARIABLE_KEYS = [
    "short_name",
    "standard_name",
    "long_name",
    "name",
]

AXIS_NAMES = {"x": "lon", "y": "lat"}


def get_points(dx):
    """Get points for a grid with a given resolution."""
    lat_v = np.linspace(90, -90, int(180 / dx) + 1)
    lon_v = np.linspace(0, 360 - dx, int(360 / dx))
    lon, lat = np.meshgrid(lon_v, lat_v)
    return lon, lat


class EarthkitSource(SingleSource):
    """
    Source class for earthkit data, allowing flexible x, y, z extraction using
    dimension names or values and supporting regridding if needed.
    """

    def __init__(self, *args, x=None, y=None, z=None, **kwargs):
        super().__init__(*args, x=x, y=y, z=z, **kwargs)

    def datetime(self, *args, **kwargs):
        """
        Get the datetime of the data.

        Parameters
        ----------
        *args
            The positional arguments to pass to the data object's `datetime` method.
        **kwargs
            The keyword arguments to pass to the data object's `datetime` method.
        """
        return self.data.datetime(*args, **kwargs)

    def _infer_xyz(self):
        """Infers x, y, and z values based on inputs."""

        # Determine z values
        if isinstance(self._z, str):
            # Select a specific variable for z if specified
            z_values = self.data.sel(short_name=self._z).to_numpy(flatten=False)
        else:
            # Default to the main data values for z
            z_values = self.data.to_numpy(flatten=False)

        if (
            self.gridspec is not None
            and self.regrid
            and self.gridspec.to_dict() is not None
        ):
            if _NO_EARTHKIT_REGRID:
                raise ImportError(
                    f"earthkit-regrid is required for plotting data on a"
                    f"'{self.gridspec.__class__.__name__}' grid"
                )

            x_values, y_values = get_points(schema.interpolate_target_resolution)

            z_values = earthkit.regrid.interpolate(
                z_values,
                self.gridspec.to_dict(),
                {"grid": [schema.interpolate_target_resolution] * 2},
            )
        else:
            x_values = self._extract_coord_values(self._x, axis="x")
            y_values = self._extract_coord_values(self._y, axis="y")
        return x_values, y_values, z_values

    def _extract_coord_values(self, coord, axis):
        """Extracts coordinate values based on axis name or dimension."""
        if isinstance(coord, str):
            # Retrieve the coordinate by name
            return self.data.sel(short_name=coord).to_numpy(flatten=False)
        else:
            # Automatically infer coordinate values from data dimensions or metadata
            try:
                points = (
                    self.data.to_points(flatten=False)
                    if hasattr(self.data, "to_points")
                    else None
                )
                if points:
                    return points[axis]
            except NotImplementedError:
                pass

            latlon = self.data.to_latlon(flatten=False)
            axis = AXIS_NAMES.get(axis, axis)
            return (
                latlon[axis]
                if axis in latlon
                else np.arange(self.data.shape[axis == "x"])
            )

    @cached_property
    def data(self):
        """Return the original earthkit data."""
        return (
            self._data[0]
            if hasattr(self._data, "__len__") and len(self._data) == 1
            else self._data
        )

    @cached_property
    def x_values(self):
        """The x values of the data."""
        return self._x_values

    @cached_property
    def y_values(self):
        """The y values of the data."""
        return self._y_values

    @cached_property
    def z_values(self):
        """The z values of the data."""
        return self._z_values

    @property
    def crs(self):
        """Return the CRS of the data."""
        if self._crs is None:
            try:
                self._crs = self.data.projection().to_cartopy_crs()
            except AttributeError:
                self._crs = ccrs.PlateCarree()
        return self._crs

    def metadata(self, key, default=None):
        """
        Extract metadata from the data.

        Parameters
        ----------
        key : str
            The metadata key to extract.
        default : any, optional
            The default value to return if the key is not found.
        """
        value = super().metadata(key, default)
        if value == default:
            try:
                value = self.data.metadata(key, default=default)
            except NotImplementedError:
                pass
        return value

    def extract_u(data, u=None):
        u_data = None
        if u is not None:
            for key in VARIABLE_KEYS:
                u_data = data.sel(**{key: u})
                if u_data:
                    break
        else:
            for key in VARIABLE_KEYS:
                for u_name in U:
                    u_data = data.sel(**{key: u_name})
                    if u_data:
                        break
                else:
                    continue
                break
        return u_data

    def extract_v(data, v=None):
        v_data = None
        if v is not None:
            for key in VARIABLE_KEYS:
                v_data = data.sel(**{key: v})
                if v_data:
                    break
        else:
            for key in VARIABLE_KEYS:
                for v_name in V:
                    v_data = data.sel(**{key: v_name})
                    if v_data:
                        break
                else:
                    continue
                break
        return v_data

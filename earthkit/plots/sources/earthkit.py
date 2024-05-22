# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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

from earthkit.plots.sources.single import SingleSource

_NO_EARTHKIT_REGRID = False
try:
    import earthkit.regrid
except ImportError:
    _NO_EARTHKIT_REGRID = True


def get_points(dx):
    lat_v = np.linspace(90, -90, int(180 / dx) + 1)
    lon_v = np.linspace(0, 360 - dx, int(360 / dx))
    lon, lat = np.meshgrid(lon_v, lat_v)
    return {"x": lon, "y": lat}


class EarthkitSource(SingleSource):
    @cached_property
    def data(self):
        if hasattr(self._data, "__len__") and len(self._data) == 1:
            return self._data[0]
        return self._data

    def metadata(self, key, default=None):
        value = super().metadata(key, default)
        if value == default:
            value = self.data.metadata(key, default=default)
        return value

    def datetime(self, *args, **kwargs):
        return self.data.datetime(*args, **kwargs)

    def extract_xyz(self):
        x, y, z = self._x, self._y, self._z
        if self._x is None and self._y is None and self._z is None:
            x, y = self.extract_xy()
        return x, y, z

    @cached_property
    def dims(self):
        return list(self.data.dims)

    def extract_xy(self):
        if self.regrid and self.gridspec is not None:
            if _NO_EARTHKIT_REGRID:
                raise ImportError(
                    f"earthkit-regrid is required for plotting data on a"
                    f"'{self.gridspec['grid']}' grid"
                )
            points = get_points(1)
        else:
            points = self.data.to_points(flatten=False)
        x = points["x"]
        y = points["y"]
        return x, y

    def extract_x(self):
        return self.extract_xy()[0]

    def extract_y(self):
        return self.extract_xy()[1]

    def extract_z(self):
        z_values = self.data.to_numpy(flatten=False)
        if self.regrid and self.gridspec is not None:
            if _NO_EARTHKIT_REGRID:
                raise ImportError(
                    f"earthkit-regrid is required for plotting data on a"
                    f"'{self.gridspec['grid']}' grid"
                )
            z_values = earthkit.regrid.interpolate(
                z_values,
                self.gridspec.to_dict(),
                {"grid": [1, 1]},
            )
        return z_values

    @property
    def crs(self):
        if self._crs is None:
            try:
                self._crs = self.data.projection().to_cartopy_crs()
            except AttributeError:
                self._crs = ccrs.PlateCarree()
        return self._crs

    @cached_property
    def x_values(self):
        return self.extract_x()

    @cached_property
    def y_values(self):
        return self.extract_y()

    @cached_property
    def z_values(self):
        return self.extract_z()

    @cached_property
    def u_values(self):
        if self._u is None:
            self._u = "u"
        return self.data.sel(short_name=self._u).to_numpy(flatten=False).squeeze()

    @cached_property
    def v_values(self):
        if self._v is None:
            self._v = "v"
        return self.data.sel(short_name=self._v).to_numpy(flatten=False).squeeze()

    @cached_property
    def magnitude_values(self):
        return (self.u_values**2 + self.v_values**2) ** 0.5

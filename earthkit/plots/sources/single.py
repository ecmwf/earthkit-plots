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

from collections.abc import Iterable
from functools import cached_property

import earthkit.data

from earthkit.plots.sources import gridspec

_NO_EARTHKIT_REGRID = False
try:
    import earthkit.regrid
except ImportError:
    _NO_EARTHKIT_REGRID = True


class SingleSource:
    def __init__(
        self,
        *args,
        data=None,
        x=None,
        y=None,
        z=None,
        u=None,
        v=None,
        crs=None,
        style=None,
        regrid=False,
        **kwargs,
    ):
        if args:
            if data is not None:
                raise ValueError(
                    f"{self.__class__.__name__} cannot accept `data` named "
                    "argument if positional arguments are provided"
                )
            if len(args) >= 2:
                if not all(kwarg is None for kwarg in (x, y, z)):
                    raise ValueError(
                        "Multiple positional arguments are not compatible with an "
                        "explicit value of 'x', 'y' or 'z'; either pass each "
                        "component as a positional argument or named argument only"
                    )
                self._x, self._y, *self._z = args
                self._z = self._z or None
                if self._z is not None:
                    self._z = self._z[0]
                self._data = None
            else:
                self._data = args[0]
                self._x = x
                self._y = y
                self._z = z
        else:
            self._data = data
            self._x = x
            self._y = y
            self._z = z

        self._u = u
        self._v = v

        self._x_label = None
        self._y_label = None
        self._z_label = None

        self._crs = crs

        self.style = style

        self._metadata = kwargs

        self._earthkit_data = None
        self._gridspec = None
        self.regrid = regrid

    @property
    def data(self):
        return self._data

    @property
    def gridspec(self):
        if self._gridspec is None:
            self._gridspec = gridspec.GridSpec.from_data(self.data)
        return self._gridspec

    @property
    def coordinate_axis(self):
        if self.x_values is not None and self.y_values is None:
            return "x"
        else:
            return "y"

    @property
    def values(self):
        if self._z is None:
            return self.y_values
        else:
            return self.z_values

    def to_earthkit(self):
        if self._earthkit_data is None:
            if not isinstance(self.data, (earthkit.data.core.Base)):
                self._earthkit_data = earthkit.data.from_object(self.data)
        return self._earthkit_data

    def metadata(self, key, default=None):
        return self._metadata.get(key, default)

    @property
    def crs(self):
        return self._crs

    @cached_property
    def units(self):
        result = self.metadata("units")
        if isinstance(result, list):
            result = result[0]
        return result

    def guess_xyz(method):
        def wrapper(self, *args, **kwargs):
            self._x, self._y, self._z = self.extract_xyz()
            return method(self, *args, **kwargs)

        return wrapper

    def extract_xyz(self):
        xyz = self._x, self._y, self._z
        if xyz == (None, None, None):
            if isinstance(self.data, Iterable):
                if isinstance(self.data[0], Iterable):
                    xyz = (
                        list(range(len(self.data[0]))),
                        list(range(len(self.data))),
                        self.data,
                    )
                else:
                    xyz = list(range(len(self.data))), self.data, None
        elif self.data is not None and xyz.count(None) >= 2:
            if self._x is None:
                xyz = self.data, self._y, self._z
            elif self._y is None:
                xyz = self._x, self.data, self._z
        return xyz

    def extract_x(self):
        return self._x

    def extract_y(self):
        return self._y

    def extract_z(self):
        return self._z

    @cached_property
    @guess_xyz
    def x_values(self):
        if self._x is None:
            self._x = self.extract_x()
        return self._x

    @cached_property
    @guess_xyz
    def y_values(self):
        if self._y is None:
            self._y = self.extract_y()
        return self._y

    @cached_property
    @guess_xyz
    def z_values(self):
        if self._z is not None:
            self._z = self.extract_z()
        return self._z

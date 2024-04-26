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

import matplotlib.pyplot as plt

from earthkit.plots.sources import gridspec

import earthkit.data


_NO_EARTHKIT_REGRID = False
try:
    import earthkit.regrid
except ImportError:
    _NO_EARTHKIT_REGRID = True


class SingleSource:
    
    def __init__(self, data=None, x=None, y=None, z=None, u=None, v=None, crs=None, style=None, regrid=False, **kwargs):
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
    def gridspec(self):
        if self._gridspec is None:
            self._gridspec = gridspec.GridSpec.from_data(self.data)
        return self._gridspec

    @property
    def coordinate_axis(self):
        if self._x is not None and self._y is None:
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
        return self._x, self._y, self._z
    
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
    
    def plot(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection=self.crs)
        if self.z_values is not None:
            ax.pcolormesh(self.x_values, self.y_values, self.z_values)
        else:
            ax.plot(self.x_values, self.y_values)

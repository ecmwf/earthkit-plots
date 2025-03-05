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

import earthkit.data
import numpy as np

from earthkit.plots.sources.earthkit import EarthkitSource
from earthkit.plots.sources.numpy import NumpySource


class MultiSource:
    def __init__(self, data, **kwargs):
        self._data = data
        self._kwargs = kwargs

    @cached_property
    def data(self):
        if not isinstance(self._data, (earthkit.data.core.Base, list, np.ndarray)):
            self._data = earthkit.data.from_object(self._data)
        return self._data

    def x_values(self):
        return [source.x_values for source in self]

    def y_values(self):
        return [source.y_values for source in self]

    def z_values(self):
        return [source.z_values for source in self]

    def crs(self):
        return [source.crs for source in self]

    def metadata(self, key, default=None):
        return [source.metadata(key, default) for source in self]

    def u_values(self):
        return [source.u_values for source in self]

    def v_values(self):
        return [source.v_values for source in self]

    def __iter__(self):
        if isinstance(self.data, (list, np.ndarray)):
            yield NumpySource(self.data, **self._kwargs)
        else:
            for field in self.data:
                yield EarthkitSource(field, **self._kwargs)

    def __getitem__(self, index):
        return EarthkitSource(self.data[index], **self._kwargs)

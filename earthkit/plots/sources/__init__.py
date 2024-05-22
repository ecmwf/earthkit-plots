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

import earthkit.data as ek_data

from earthkit.plots.sources.earthkit import EarthkitSource
from earthkit.plots.sources.numpy import NumpySource
from earthkit.plots.sources.xarray import XarraySource


def get_source(*args, data=None, x=None, y=None, z=None, u=None, v=None, **kwargs):
    cls = NumpySource
    core_data = data
    if len(args) == 1 and core_data is None:
        core_data = args[0]
    if core_data is not None:
        if data.__class__.__name__ in ("Dataset", "DataArray"):
            cls = XarraySource
        elif isinstance(core_data, ek_data.core.Base):
            cls = EarthkitSource
    return cls(*args, data=data, x=x, y=y, z=z, u=u, v=v, **kwargs)

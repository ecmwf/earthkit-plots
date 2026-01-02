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

# Marker constant used to reference the selected DataArray's/Field's data values
# Used in coordinate extraction to distinguish "use this variable's data" from "use this coordinate"
SELECTED_DATA = "__selected_data__"

from earthkit.plots.sources.adaptors.base import BaseAdaptor
from earthkit.plots.sources.adaptors.earthkit import EarthkitAdaptor
from earthkit.plots.sources.adaptors.numpy import NumpyAdaptor
from earthkit.plots.sources.adaptors.xarray import XarrayAdaptor

__all__ = [
    "BaseAdaptor",
    "NumpyAdaptor",
    "XarrayAdaptor",
    "EarthkitAdaptor",
    "SELECTED_DATA",
]

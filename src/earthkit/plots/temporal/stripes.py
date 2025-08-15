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

from earthkit.plots.temporal.timeseries import TimeSeries

DEFAULT_COLORS = [
    "#08306b",
    "#08519c",
    "#2171b5",
    "#4292c6",
    "#6baed6",
    "#9ecae1",
    "#c6dbef",
    "#deebf7",
    "#ffffff",
    "#fee0d2",
    "#fcbba1",
    "#fc9272",
    "#fb6a4a",
    "#ef3b2c",
    "#cb181d",
    "#a50f15",
    "#67000d",
]


class Stripes(TimeSeries):
    """
    A specialized Subplot class for time series plots.

    This class inherits from Subplot and provides specialized functionality
    for plotting time series data, including automatic time axis detection
    and appropriate default sizing.
    """

    def __init__(self, *args, size=(8, 3), **kwargs):
        super().__init__(*args, size=size, **kwargs)

    def stripes(self, *args, colors=DEFAULT_COLORS, **kwargs):
        """
        Plot climate stripes using this `Style`.
        """
        super().stripes(*args, colors=colors, **kwargs)

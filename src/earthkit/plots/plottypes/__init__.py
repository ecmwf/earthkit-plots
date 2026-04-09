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

from earthkit.plots.plottypes.multiboxplot import (
    MultiboxplotResult,
    draw_multiboxplot,
    draw_multiboxplot_legend,
)
from earthkit.plots.plottypes.rgb_composite import (
    RGBCompositeResult,
    prepare_rgb_composite,
)

__all__ = [
    "bandplot",
    "boxplot",
    "draw_multiboxplot",
    "draw_multiboxplot_legend",
    "MultiboxplotResult",
    "prepare_rgb_composite",
    "RGBCompositeResult",
]


def __getattr__(name):
    if name in ("bandplot", "boxplot"):
        from earthkit.plots.plottypes.statistics import bandplot, boxplot

        globals()["bandplot"] = bandplot
        globals()["boxplot"] = boxplot
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

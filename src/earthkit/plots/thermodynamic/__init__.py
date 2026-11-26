# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

"""
Thermodynamic diagrams: tephigrams, skew-T log-p diagrams and emagrams.

The thermodynamic computations are done with earthkit-meteo, which is
installed with ``pip install 'earthkit-plots[thermo]'``.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from earthkit.plots.thermodynamic.diagrams import Emagram, SkewT, Tephigram, ThermoDiagram
    from earthkit.plots.thermodynamic.grid import LineFamily, ThermoGrid

__all__ = ["ThermoDiagram", "Tephigram", "SkewT", "Emagram", "ThermoGrid", "LineFamily"]

_LAZY = {
    "ThermoDiagram": "earthkit.plots.thermodynamic.diagrams",
    "Tephigram": "earthkit.plots.thermodynamic.diagrams",
    "SkewT": "earthkit.plots.thermodynamic.diagrams",
    "Emagram": "earthkit.plots.thermodynamic.diagrams",
    "ThermoGrid": "earthkit.plots.thermodynamic.grid",
    "LineFamily": "earthkit.plots.thermodynamic.grid",
}


def __getattr__(name):
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

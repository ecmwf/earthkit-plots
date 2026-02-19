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

"""
Backwards-compatibility shim.

The regridding logic previously in this module has been consolidated into
:class:`earthkit.plots.resample.Regrid`.  Public helpers are re-exported here
so that existing imports continue to work.
"""

from earthkit.plots.resample import Regrid, _call_regrid_compat


def can_regrid():
    """Return True if earthkit-regrid is installed and usable."""
    return Regrid.available()


def has_subarea_support():
    """Return True if the available executor supports sub-area regridding."""
    return Regrid.has_subarea_support()


def regrid(array, in_grid, out_grid):
    """Call earthkit-regrid directly (legacy helper)."""
    return _call_regrid_compat(array, in_grid, out_grid)

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

import numpy as np

from earthkit.plots.styles.levels import auto_range


def _is_strictly_increasing(levels):
    return all(a < b for a, b in zip(levels, levels[1:]))


def test_auto_range_constant_field_is_increasing():
    """A constant field must yield strictly increasing levels.

    Regression test for ``ValueError: Contour levels must be increasing`` (#150)
    raised when plotting data made up of a single value (e.g. NaNs and zeros):
    ``auto_range`` returned a list of identical values.
    """
    data = np.zeros((5, 5))
    data[0, 0] = np.nan
    levels = auto_range(data)
    assert _is_strictly_increasing(levels)


def test_auto_range_constant_field_centred_on_value():
    """Levels for a constant field are centred on that value."""
    levels = auto_range(np.full((5, 5), 5.0))
    assert _is_strictly_increasing(levels)
    assert min(levels) < 5.0 < max(levels)


def test_auto_range_all_nan_does_not_crash():
    """An all-NaN field falls back to a valid range instead of crashing."""
    levels = auto_range(np.full((4, 4), np.nan))
    assert _is_strictly_increasing(levels)


def test_auto_range_normal_data_unaffected():
    """Regular data still produces sensible, increasing levels."""
    levels = auto_range(np.linspace(0, 100, 50).reshape(5, 10))
    assert _is_strictly_increasing(levels)
    assert min(levels) <= 0
    assert max(levels) >= 100

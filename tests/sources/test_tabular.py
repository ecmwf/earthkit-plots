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

import numpy as np
import pytest

try:
    import pandas as pd
except ImportError:
    pytest.skip(
        "skipping tests in sources/tabular (no pandas)", allow_module_level=True
    )

from earthkit.plots.sources.tabular import TabularSource


def test_TabularSource_Series():
    series = pd.Series([4, 5, 7])
    source = TabularSource(series)
    assert np.array_equal(source.x_values, [0, 1, 2])  # auto-generated index
    assert np.array_equal(source.y_values, [4, 5, 7])
    assert source.z_values is None


def test_TabularSource_singlecol():
    df = pd.DataFrame({"values": [4, 5, 7]})
    source = TabularSource(df)
    assert np.array_equal(source.x_values, [0, 1, 2])  # auto-generated index
    assert np.array_equal(source.y_values, [4, 5, 7])
    assert source.z_values is None


def test_TabularSource_multicol_identification():
    df = pd.DataFrame({"x": [3, 4, 5], "y": [4, 5, 7]})
    source = TabularSource(df)
    assert np.array_equal(source.x_values, [3, 4, 5])
    assert np.array_equal(source.y_values, [4, 5, 7])
    assert source.z_values is None


def test_TabularSource_multicol_manual_2D():
    df = pd.DataFrame({"foo": [4, 5, 6], "y": [3, 2, 1], "baz": [7, 8, 9]})
    source = TabularSource(df, x="y", y="foo")  # override y-detection
    assert np.array_equal(source.x_values, [3, 2, 1])
    assert np.array_equal(source.y_values, [4, 5, 6])
    assert source.z_values is None


def test_TabularSource_multicol_manual_3D():
    df = pd.DataFrame({"foo": [4, 5, 6], "bar": [3, 2, 1], "baz": [7, 8, 9]})
    source = TabularSource(df, x="baz", y="foo", z="bar")
    assert np.array_equal(source.x_values, [7, 8, 9])
    assert np.array_equal(source.y_values, [4, 5, 6])
    assert np.array_equal(source.z_values, [3, 2, 1])

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

from earthkit.plots.sources.numpy import NumpySource


def test_NumpySource_1D_data():
    source = NumpySource([1, 2, 3])
    assert np.array_equal(source.x_values, [0, 1, 2])
    assert np.array_equal(source.y_values, [1, 2, 3])
    assert source.z_values is None


def test_NumpySource_2D_data():
    source = NumpySource([[1, 2, 3], [4, 5, 6]])
    assert np.array_equal(source.x_values, [0, 1, 2])
    assert np.array_equal(source.y_values, [0, 1])
    assert np.array_equal(source.z_values, [[1, 2, 3], [4, 5, 6]])


def test_NumpySource_mixed_args():
    with pytest.raises(ValueError):
        NumpySource([1, 2, 3], data=[4, 5, 6])


def test_NumpySource_2_args():
    source = NumpySource([1, 2, 3, 4], [3, 1, 4, 2])
    assert np.array_equal(source.x_values, [1, 2, 3, 4])
    assert np.array_equal(source.y_values, [3, 1, 4, 2])
    assert source.z_values is None


def test_NumpySource_xy():
    source = NumpySource(x=[1, 2, 3, 4], y=[3, 1, 4, 2])
    assert np.array_equal(source.x_values, [1, 2, 3, 4])
    assert np.array_equal(source.y_values, [3, 1, 4, 2])
    assert source.z_values is None


def test_NumpySource_3_args():
    source = NumpySource([1, 2, 3], [3, 6, 4], [[1, 2, 3], [4, 5, 6]])
    assert np.array_equal(source.x_values, [1, 2, 3])
    assert np.array_equal(source.y_values, [3, 6, 4])
    assert np.array_equal(source.z_values, [[1, 2, 3], [4, 5, 6]])

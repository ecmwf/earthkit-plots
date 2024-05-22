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

import pytest

from earthkit.plots.sources.single import SingleSource


def test_SingleSource_1D_data():
    source = SingleSource([1, 2, 3])
    assert source.x_values == [0, 1, 2]
    assert source.y_values == [1, 2, 3]
    assert source.z_values is None


def test_SingleSource_2D_data():
    source = SingleSource([[1, 2, 3], [4, 5, 6]])
    assert source.y_values == [0, 1]
    assert source.x_values == [0, 1, 2]
    assert source.z_values == [[1, 2, 3], [4, 5, 6]]


def test_SingleSource_mixed_args():
    with pytest.raises(ValueError):
        SingleSource([1, 2, 3], data=[4, 5, 6])


def test_SingleSource_positional_plus_xyz():
    with pytest.raises(ValueError):
        SingleSource([1, 2, 3], [4, 5, 6], x=[4, 5, 6])


def test_SingleSource_2_args():
    source = SingleSource([1, 2, 3], [3, 6, 4])
    assert source.x_values == [1, 2, 3]
    assert source.y_values == [3, 6, 4]
    assert source.z_values is None


def test_SingleSource_xy():
    source = SingleSource(x=[1, 2, 3], y=[3, 6, 4])
    assert source.x_values == [1, 2, 3]
    assert source.y_values == [3, 6, 4]
    assert source.z_values is None


def test_SingleSource_3_args():
    source = SingleSource([1, 2, 3], [3, 6, 4], [[1, 2, 3], [4, 5, 6]])
    assert source.y_values == [3, 6, 4]
    assert source.x_values == [1, 2, 3]
    assert source.z_values == [[1, 2, 3], [4, 5, 6]]


def test_SingleSource_named_x():
    source = SingleSource([4, 5, 6], x=[1, 2, 3])
    assert source.y_values == [4, 5, 6]
    assert source.x_values == [1, 2, 3]
    assert source.z_values is None

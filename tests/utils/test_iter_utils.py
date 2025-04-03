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

from earthkit.plots.utils import iter_utils


def test_symmetrical_iter_empty_list():
    assert list(iter_utils.symmetrical_iter([])) == []


def test_symmetrical_iter_single():
    assert list(iter_utils.symmetrical_iter([1])) == [1]


def test_symmetrical_iter_double():
    assert list(iter_utils.symmetrical_iter([1, 2])) == [(1, 2)]


def test_symmetrical_iter_triple():
    assert list(iter_utils.symmetrical_iter([1, 2, 3])) == [(1, 3), 2]


def test_symmetrical_iter_quadrouple():
    assert list(iter_utils.symmetrical_iter([1, 2, 3, 4])) == [(1, 4), (2, 3)]

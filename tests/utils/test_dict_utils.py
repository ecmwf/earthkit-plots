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

from earthkit.plots.utils import dict_utils


def test_recursive_dict_update_unnested():
    dict_1 = {"a": 1, "b": 2}
    dict_2 = {"a": 10, "c": 3}
    assert dict_utils.recursive_dict_update(dict_1, dict_2) == {"a": 10, "b": 2, "c": 3}


def test_recursive_dict_update_nested():
    dict_1 = {"font": {"size": 10, "family": "Lato"}, "size": 20}
    dict_2 = {"font": {"size": 12, "color": "red"}}
    assert dict_utils.recursive_dict_update(dict_1, dict_2) == {
        "font": {"size": 12, "color": "red", "family": "Lato"},
        "size": 20,
    }

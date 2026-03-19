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

from earthkit.plots.utils import string_utils


def test_list_to_human_single_item():
    items = ["sausage"]
    assert string_utils.list_to_human(items) == "sausage"


def test_list_to_human_two_items():
    items = ["sausage", "egg"]
    assert string_utils.list_to_human(items) == "sausage and egg"


def test_list_to_human_three_items():
    items = ["sausage", "egg", "chips"]
    assert string_utils.list_to_human(items) == "sausage, egg and chips"


def test_list_to_human_oxford_comma():
    items = ["sausage", "egg", "chips"]
    assert (
        string_utils.list_to_human(items, oxford_comma=True)
        == "sausage, egg, and chips"
    )


def test_list_to_human_conjunction():
    items = ["sausage", "egg", "chips"]
    assert (
        string_utils.list_to_human(items, conjunction="or") == "sausage, egg or chips"
    )


def test_split_camel_case_single_chunk():
    string = "Camel"
    assert string_utils.split_camel_case(string) == ["Camel"]


def test_split_camel_case_multi_chunk():
    string = "ACamelCaseString"
    assert string_utils.split_camel_case(string) == ["A", "Camel", "Case", "String"]


def test_split_camel_case_snake_case():
    string = "a_snake_case_string"
    assert string_utils.split_camel_case(string) == ["a_snake_case_string"]


def test_magnitude_string_from_components_wind():
    u_name = "u_component_of_wind"
    v_name = "v_component_of_wind"
    assert string_utils.magnitude_string_from_components(u_name, v_name) == "wind"


def test_magnitude_string_from_components_with_prefix():
    u_name = "10m u-component of wind"
    v_name = "10m v-component of wind"
    assert string_utils.magnitude_string_from_components(u_name, v_name) == "10m wind"


def test_magnitude_string_from_components_snake_case():
    u_name = "10m_u_component_of_wind"
    v_name = "10m_v_component_of_wind"
    assert string_utils.magnitude_string_from_components(u_name, v_name) == "10m wind"


def test_magnitude_string_from_components_east_north():
    u_name = "eastward wind"
    v_name = "northward wind"
    assert string_utils.magnitude_string_from_components(u_name, v_name) == "wind"


def test_magnitude_string_from_components_no_common():
    u_name = "temperature"
    v_name = "humidity"
    assert (
        string_utils.magnitude_string_from_components(u_name, v_name)
        == "temperature and humidity"
    )


def test_magnitude_string_from_components_no_common_components():
    u_name = "U component of bananas"
    v_name = "V component of apples"
    assert (
        string_utils.magnitude_string_from_components(u_name, v_name)
        == "U component of bananas and V component of apples"
    )


def test_magnitude_string_from_components_not_wind():
    u_name = "u_component_of_bananas"
    v_name = "v_component_of_bananas"
    assert string_utils.magnitude_string_from_components(u_name, v_name) == "bananas"

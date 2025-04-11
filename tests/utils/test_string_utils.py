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

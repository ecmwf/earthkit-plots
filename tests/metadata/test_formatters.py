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

from earthkit.plots.metadata import formatters


def test_BaseFormatter_convert_field_upper():
    formatter = formatters.BaseFormatter()
    assert formatter.convert_field("test", "u") == "TEST"


def test_BaseFormatter_convert_field_lower():
    formatter = formatters.BaseFormatter()
    assert formatter.convert_field("Test", "l") == "test"


def test_BaseFormatter_convert_field_capitalize():
    formatter = formatters.BaseFormatter()
    assert formatter.convert_field("this is a test", "c") == "This is a test"


def test_BaseFormatter_convert_field_title():
    formatter = formatters.BaseFormatter()
    assert formatter.convert_field("this is a test", "t") == "This Is A Test"

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


import pytest

from earthkit.plots.components.layouts import rows_cols


def test_rows_cols_with_preset_shapes():
    # Test cases for values in PRESET_SHAPES
    assert rows_cols(1) == (1, 1)
    assert rows_cols(5) == (2, 3)
    assert rows_cols(10) == (2, 5)
    assert rows_cols(20) == (4, 5)


def test_rows_cols_calculate_from_max_columns():
    # Test calculation when neither rows nor columns are provided
    assert rows_cols(21) == (3, 8)  # Default max_columns=8
    assert rows_cols(30, max_columns=6) == (5, 6)  # Custom max_columns


def test_rows_cols_with_specified_rows():
    # Test calculation when rows are specified
    assert rows_cols(10, rows=2) == (2, 5)
    assert rows_cols(11, rows=2) == (2, 6)
    assert rows_cols(5, rows=1) == (1, 5)


def test_rows_cols_with_specified_columns():
    # Test calculation when columns are specified
    assert rows_cols(10, columns=5) == (2, 5)
    assert rows_cols(11, columns=5) == (3, 5)
    assert rows_cols(7, columns=1) == (7, 1)


def test_rows_cols_with_both_rows_and_columns():
    # Test when both rows and columns are provided
    assert rows_cols(6, rows=2, columns=3) == (2, 3)

    with pytest.raises(ValueError, match="6 subplots is too many"):
        rows_cols(6, rows=2, columns=2)


def test_edge_cases():
    # Test edge cases
    assert rows_cols(0) == (0, 0)  # No subplots
    assert rows_cols(1) == (1, 1)  # Single subplot
    assert rows_cols(2, rows=1) == (1, 2)  # All in a single row


def test_large_number_of_subplots():
    # Test for a large number of subplots
    assert rows_cols(100) == (13, 8)  # Default max_columns=8
    assert rows_cols(100, max_columns=10) == (10, 10)

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

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

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


# TimeFormatter Tests
def test_TimeFormatter_single_time():
    """Test TimeFormatter with a single time entry."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        }
    ]
    formatter = formatters.TimeFormatter(time_data)

    assert formatter.base_time == [datetime(2024, 1, 1, 0, 0)]
    assert formatter.valid_time == [datetime(2024, 1, 1, 6, 0)]
    assert formatter.lead_time == [6]


def test_TimeFormatter_multiple_times():
    """Test TimeFormatter with multiple time entries."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 12, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 18, 0),
        },
    ]
    formatter = formatters.TimeFormatter(time_data)

    expected_base_time = [datetime(2024, 1, 1, 0, 0)]
    expected_valid_times = [
        datetime(2024, 1, 1, 6, 0),
        datetime(2024, 1, 1, 12, 0),
        datetime(2024, 1, 1, 18, 0),
    ]
    expected_lead_times = [6, 12, 18]

    assert formatter.base_time == expected_base_time
    assert formatter.valid_time == expected_valid_times
    assert formatter.lead_time == expected_lead_times


def test_TimeFormatter_lead_time_indexing():
    """Test that lead_time indexing works correctly."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 12, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 18, 0),
        },
    ]
    formatter = formatters.TimeFormatter(time_data)

    lead_times = formatter.lead_time

    # Test indexing
    assert lead_times[0] == 6
    assert lead_times[1] == 12
    assert lead_times[2] == 18

    # Test that indexing works for the bug fix
    assert len(lead_times) == 3


def test_TimeFormatter_lead_time_with_different_base_times():
    """Test lead_time calculation with different base times."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 6, 0),
            "valid_time": datetime(2024, 1, 1, 12, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 12, 0),
            "valid_time": datetime(2024, 1, 1, 18, 0),
        },
    ]
    formatter = formatters.TimeFormatter(time_data)

    expected_lead_times = [6]
    assert formatter.lead_time == expected_lead_times


def test_TimeFormatter_lead_time_with_missing_times():
    """Test lead_time calculation with missing base_time or valid_time."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        },
        {"base_time": None, "valid_time": datetime(2024, 1, 1, 12, 0)},
        {"base_time": datetime(2024, 1, 1, 0, 0), "valid_time": None},
    ]
    formatter = formatters.TimeFormatter(time_data)

    lead_times = formatter.lead_time
    # Should preserve None values and deduplicate non-None values
    assert 6 in lead_times  # The valid lead time should be present
    assert None in lead_times  # None values should be preserved
    assert len(lead_times) >= 2  # Should have at least the valid value and None


def test_TimeFormatter_lead_time_with_all_none():
    """Test lead_time calculation when all times are None."""
    time_data = [
        {"base_time": None, "valid_time": None},
        {"base_time": None, "valid_time": None},
    ]
    formatter = formatters.TimeFormatter(time_data)

    lead_times = formatter.lead_time
    # Should preserve all None values
    assert lead_times == [None, None]


def test_TimeFormatter_time_zone_conversion():
    """Test time zone conversion functionality with a non-zero UTC offset."""
    time_data = [
        {
            "base_time": datetime(2024, 7, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            "valid_time": datetime(2024, 7, 1, 6, 0, tzinfo=ZoneInfo("UTC")),
        },
    ]
    # Paris is UTC+2 (CEST) in July
    formatter = formatters.TimeFormatter(time_data, time_zone="Europe/Paris")

    # Test that time zone conversion works
    base_times = formatter.base_time
    valid_times = formatter.valid_time

    # Should be converted to Paris time (UTC+2 in July)
    assert base_times[0].tzinfo == ZoneInfo("Europe/Paris")
    assert valid_times[0].tzinfo == ZoneInfo("Europe/Paris")
    assert base_times[0].utcoffset().total_seconds() == 7200  # 2 hours offset
    assert valid_times[0].utcoffset().total_seconds() == 7200


def test_TimeFormatter_utc_offset():
    """Test UTC offset calculation."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            "valid_time": datetime(2024, 1, 1, 6, 0, tzinfo=ZoneInfo("UTC")),
        },
        {
            "base_time": datetime(2024, 1, 1, 0, 0, tzinfo=ZoneInfo("Europe/London")),
            "valid_time": datetime(2024, 1, 1, 6, 0, tzinfo=ZoneInfo("Europe/London")),
        },
    ]
    formatter = formatters.TimeFormatter(time_data)

    utc_offsets = formatter.utc_offset
    assert "UTC+0" in utc_offsets


def test_TimeFormatter_unique_times():
    """Test that duplicate times are handled correctly."""
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        },
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 6, 0),
        },  # Duplicate
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 12, 0),
        },
    ]
    formatter = formatters.TimeFormatter(time_data)

    # Should deduplicate while preserving order
    assert len(formatter.base_time) == 1
    assert len(formatter.valid_time) == 2
    assert len(formatter.lead_time) == 2


def test_TimeFormatter_lead_time_edge_cases():
    """Test edge cases for lead_time calculation."""
    # Test negative lead time
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 6, 0),
            "valid_time": datetime(2024, 1, 1, 0, 0),
        }
    ]
    formatter = formatters.TimeFormatter(time_data)
    assert formatter.lead_time == [-6]

    # Test zero lead time
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 1, 0, 0),
        }
    ]
    formatter = formatters.TimeFormatter(time_data)
    assert formatter.lead_time == [0]

    # Test large lead time
    time_data = [
        {
            "base_time": datetime(2024, 1, 1, 0, 0),
            "valid_time": datetime(2024, 1, 2, 0, 0),
        }
    ]
    formatter = formatters.TimeFormatter(time_data)
    assert formatter.lead_time == [24]


def test_TimeFormatter_named_time_fallback():
    """Test that _named_time falls back to 'time' when specific time is missing."""
    time_data = [{"time": datetime(2024, 1, 1, 0, 0)}]
    formatter = formatters.TimeFormatter(time_data)

    # Should use 'time' as fallback for both base_time and valid_time
    assert formatter.base_time == [datetime(2024, 1, 1, 0, 0)]
    assert formatter.valid_time == [datetime(2024, 1, 1, 0, 0)]
    assert formatter.lead_time == [0]


def test_SubplotFormatter_layer_indexing():
    """Test that SubplotFormatter handles layer indexing correctly."""
    # Mock subplot with multiple layers
    class MockLayer:
        def __init__(self, value):
            self.value = value

        def format_key(self, key):
            return self.value

    class MockSubplot:
        def __init__(self, layers):
            self.layers = layers

    layers = [MockLayer("first"), MockLayer("second"), MockLayer("third")]
    subplot = MockSubplot(layers)
    formatter = formatters.SubplotFormatter(subplot)

    # Test indexing
    assert formatter.convert_field(["first", "second", "third"], "0") == "first"
    assert formatter.convert_field(["first", "second", "third"], "1") == "second"
    assert formatter.convert_field(["first", "second", "third"], "2") == "third"


def test_SubplotFormatter_index_out_of_range():
    """Test that SubplotFormatter raises appropriate error for out-of-range indices."""
    formatter = formatters.SubplotFormatter(None)

    with pytest.raises(IndexError, match="Layer index 5 in title is out of range"):
        formatter.convert_field(["a", "b", "c"], "5")


def test_FigureFormatter_layer_indexing():
    """Test that FigureFormatter handles layer indexing correctly."""
    formatter = formatters.FigureFormatter([])

    # Test indexing
    assert formatter.convert_field(["first", "second", "third"], "0") == "first"
    assert formatter.convert_field(["first", "second", "third"], "1") == "second"
    assert formatter.convert_field(["first", "second", "third"], "2") == "third"


def test_FigureFormatter_non_numeric_conversion():
    """Test that FigureFormatter handles non-numeric conversions correctly."""
    formatter = formatters.FigureFormatter([])

    # Non-numeric conversion should be applied to all values
    result = formatter.convert_field(["test", "value"], "u")
    assert result == ["TEST", "VALUE"]

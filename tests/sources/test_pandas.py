# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

"""Tests for pandas sources using the unified Source system."""

import datetime

import numpy as np
import pytest

from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.extractors.pandas import PandasExtractor

pd = pytest.importorskip("pandas")


@pytest.fixture
def station():
    """A sounding at a station, like the output of earthkit-data's BUFR to_pandas()."""
    df = pd.DataFrame({
        "data_datetime": pd.to_datetime(["2008-12-08 12:00"] * 4),
        "latitude": [4.27] * 4,
        "longitude": [117.88] * 4,
        "stationNumber": [481] * 4,
        "pressure": [100000.0, 85000.0, 70000.0, 50000.0],
        "airTemperature": [299.2, 290.1, np.nan, 268.4],
    })
    df.attrs["units"] = {"airTemperature": "K", "pressure": "Pa"}
    df.attrs["institution"] = "ECMWF"
    return df


def test_extractor_selected(station):
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    assert isinstance(source._extractor, PandasExtractor)
    source = get_source(station["airTemperature"], context=PlotContext.CARTESIAN_1D)
    assert isinstance(source._extractor, PandasExtractor)


def test_column_names(station):
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    np.testing.assert_array_equal(source.x.values, station["pressure"])
    np.testing.assert_array_equal(source.y.values, station["airTemperature"])
    assert source.x.name == "pressure"
    assert source.y.name == "airTemperature"


def test_units_from_attrs_mapping(station):
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    assert source.x.source_units == "Pa"
    assert source.y.source_units == "K"
    assert source.source_units == "K"


def test_unit_conversion(station):
    source = get_source(
        station, x="pressure", y="airTemperature", y_units="celsius", x_units="hPa", context=PlotContext.CARTESIAN_1D
    )
    np.testing.assert_allclose(source.y.values[0], 299.2 - 273.15)
    np.testing.assert_allclose(source.x.values, [1000, 850, 700, 500])


def test_unknown_column(station):
    source = get_source(station, x="pressure", y="temperature", context=PlotContext.CARTESIAN_1D)
    with pytest.raises(ValueError, match="'temperature' given for 'y' not found"):
        source.y


def test_several_columns_need_a_name(station):
    source = get_source(station, context=PlotContext.CARTESIAN_1D)
    with pytest.raises(ValueError, match="name the column to plot with y="):
        source.y


def test_constant_columns_are_metadata(station):
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    assert source.metadata("latitude") == pytest.approx(4.27)
    assert source.metadata("longitude") == pytest.approx(117.88)
    assert source.metadata("stationNumber") == 481
    assert isinstance(source.metadata("stationNumber"), int)
    # varying columns are not metadata
    assert source.metadata("pressure") is None


def test_constant_column_ignores_missing_values(station):
    station.loc[2, "latitude"] = np.nan
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    assert source.metadata("latitude") == pytest.approx(4.27)


def test_name_and_frame_attrs(station):
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    source.y  # the plotted column is known once the coordinates are extracted, as when plotting
    assert source.metadata("name") == "airTemperature"
    assert source.metadata("institution") == "ECMWF"


def test_user_metadata_takes_priority(station):
    source = get_source(
        station, x="pressure", y="airTemperature", metadata={"latitude": 0.0}, context=PlotContext.CARTESIAN_1D
    )
    assert source.metadata("latitude") == 0.0


def test_datetime_from_constant_column(station):
    source = get_source(station, x="pressure", y="airTemperature", context=PlotContext.CARTESIAN_1D)
    dt = source.datetime()
    assert dt["valid_time"] == datetime.datetime(2008, 12, 8, 12)
    assert dt["base_time"] == datetime.datetime(2008, 12, 8, 12)


def test_datetime_base_and_step():
    df = pd.DataFrame({
        "forecast_reference_time": pd.to_datetime(["2024-01-01 00:00"] * 2),
        "step": pd.to_timedelta(["6h", "6h"]),
        "t2m": [280.0, 281.0],
    })
    dt = get_source(df, y="t2m", context=PlotContext.CARTESIAN_1D).datetime()
    assert dt["base_time"] == datetime.datetime(2024, 1, 1)
    assert dt["lead_time"] == datetime.timedelta(hours=6)
    assert dt["valid_time"] == datetime.datetime(2024, 1, 1, 6)


def test_no_datetime():
    df = pd.DataFrame({"a": [1.0, 2.0]})
    assert get_source(df, context=PlotContext.CARTESIAN_1D).datetime() == {"base_time": None, "valid_time": None}


def test_series():
    s = pd.Series([1.0, 2.0, 3.0], name="t2m")
    s.attrs["units"] = "K"
    source = get_source(s, context=PlotContext.CARTESIAN_1D)
    np.testing.assert_array_equal(source.x.values, [0, 1, 2])
    np.testing.assert_array_equal(source.y.values, [1.0, 2.0, 3.0])
    assert source.metadata("name") == "t2m"
    assert source.source_units == "K"


def test_series_from_frame_keeps_column_units(station):
    # pandas copies the attrs of a DataFrame to its columns
    source = get_source(station["airTemperature"], context=PlotContext.CARTESIAN_1D)
    assert source.source_units == "K"


def test_series_against_datetime_index():
    index = pd.date_range("2024-01-01", periods=3, freq="D", name="time")
    s = pd.Series([1.0, 2.0, 3.0], index=index, name="t2m")
    source = get_source(s, context=PlotContext.CARTESIAN_1D)
    np.testing.assert_array_equal(source.x.values, index.to_numpy())
    assert source.x.name == "time"


def test_index_as_coordinate(station):
    # When y names the index, the values are on x (e.g. a vertical profile)
    frame = station.set_index("pressure")
    source = get_source(frame, x="airTemperature", y="pressure", context=PlotContext.CARTESIAN_1D)
    np.testing.assert_array_equal(source.y.values, frame.index)
    assert source.metadata("name") == "airTemperature"
    assert source.source_units == "K"
    assert source.metadata("latitude") == pytest.approx(4.27)


def test_index_as_coordinate_series():
    s = pd.Series([290.0, 280.0], index=pd.Index([1000.0, 850.0], name="pressure"), name="t")
    source = get_source(s, y="pressure", context=PlotContext.CARTESIAN_1D)
    np.testing.assert_array_equal(source.x.values, [290.0, 280.0])
    np.testing.assert_array_equal(source.y.values, [1000.0, 850.0])


def test_series_coordinates_without_data(station):
    # Series given as x and y (previously rejected as "No data provided")
    source = get_source(x=station["pressure"], y=station["airTemperature"], context=PlotContext.CARTESIAN_1D)
    np.testing.assert_array_equal(source.y.values, station["airTemperature"])


def test_geographic_columns():
    df = pd.DataFrame({"lon": [0.0, 10.0], "lat": [50.0, 55.0], "t2m": [280.0, 285.0]})
    source = get_source(df, x="lon", y="lat", z="t2m", context=PlotContext.GEOGRAPHIC_1D)
    np.testing.assert_array_equal(source.z.values, [280.0, 285.0])
    assert source.metadata("name") == "t2m"

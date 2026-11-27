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

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

pytest.importorskip("earthkit.meteo")
pd = pytest.importorskip("pandas")

from earthkit.plots.thermodynamic import SkewT, Tephigram  # noqa: E402
from earthkit.plots.thermodynamic.profiles import extract, pandas_profile  # noqa: E402

K = 273.15


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def sounding():
    """A BUFR-like sounding: Pa and K, top-down, with wind-only levels (NaN temperatures)."""
    return pd.DataFrame({
        "data_datetime": pd.to_datetime(["2008-12-08 12:00"] * 5),
        "latitude": [4.27] * 5,
        "longitude": [117.88] * 5,
        "pressure": [30000.0, 50000.0, 70000.0, 85000.0, 100000.0],
        "airTemperature": [240.0, 260.0, np.nan, 285.0, 300.0],
        "dewpointTemperature": [220.0, 250.0, 270.0, np.nan, 295.0],
    })


def test_pandas_profile(sounding):
    frame, column, p_name = pandas_profile(sounding, column="airTemperature", p="pressure", units="K", p_units="Pa")
    assert (column, p_name) == ("airTemperature", "pressure")
    # missing levels dropped, ordered from the bottom up, °C and hPa
    np.testing.assert_allclose(frame.index, [1000, 850, 500, 300])
    np.testing.assert_allclose(frame[column], np.array([300.0, 285.0, 260.0, 240.0]) - K)
    assert frame.attrs["units"] == {"airTemperature": "celsius", "pressure": "hPa"}
    # the other columns are kept as metadata
    assert (frame["latitude"] == 4.27).all()
    # the input is not modified
    assert sounding["pressure"].iloc[0] == 30000.0


def test_pandas_profile_units_from_attrs(sounding):
    sounding.attrs["units"] = {"airTemperature": "K", "pressure": "Pa"}
    frame, _, _ = pandas_profile(sounding, column="airTemperature", p="pressure")
    np.testing.assert_allclose(frame.index, [1000, 850, 500, 300])
    np.testing.assert_allclose(frame["airTemperature"].iloc[0], 300.0 - K)


def test_pandas_profile_pressure_index(sounding):
    indexed = sounding.set_index("pressure")
    frame, _, p_name = pandas_profile(indexed, column="airTemperature", units="K", p_units="Pa")
    assert p_name == "pressure"
    np.testing.assert_allclose(frame.index, [1000, 850, 500, 300])


def test_pandas_profile_series_with_pressure_values():
    t = pd.Series([20.0, 10.0, -5.0], name="t")
    frame, column, p_name = pandas_profile(t, p=[1000.0, 850.0, 700.0])
    assert column == "t"
    np.testing.assert_allclose(frame.index, [1000, 850, 700])
    np.testing.assert_allclose(frame["t"], [20, 10, -5])


def test_pandas_profile_needs_column(sounding):
    with pytest.raises(ValueError, match="column="):
        pandas_profile(sounding, p="pressure")


def test_pandas_profile_needs_pressure():
    with pytest.raises(ValueError, match="p="):
        pandas_profile(pd.DataFrame({"t": [1.0, 2.0]}), column="t")


def test_extract_dataframe(sounding):
    values, p = extract(sounding, p="pressure", column="dewpointTemperature", units="K", p_units="Pa")
    np.testing.assert_allclose(p, [1000, 700, 500, 300])
    np.testing.assert_allclose(values, np.array([295.0, 270.0, 250.0, 220.0]) - K)


def test_temperature_from_dataframe(sounding):
    d = Tephigram()
    d.temperature(sounding, column="airTemperature", p="pressure", units="K", p_units="Pa")
    (line,) = [ln for ln in d.ax.lines if ln.get_label() == "Temperature"]
    np.testing.assert_allclose(line.get_xdata(), np.array([300.0, 285.0, 260.0, 240.0]) - K)
    np.testing.assert_allclose(line.get_ydata(), [1000, 850, 500, 300])


def test_title_from_dataframe_metadata(sounding):
    d = SkewT()
    d.temperature(sounding, column="airTemperature", p="pressure", units="K", p_units="Pa")
    d.dewpoint(sounding, column="dewpointTemperature", p="pressure", units="K", p_units="Pa")
    title = d.title("{latitude:%Lt}, {longitude:%Ln} {time:%Y-%m-%d %H} UTC")
    assert title.get_text() == "4.27°N, 117.88°E 2008-12-08 12 UTC"


def test_envelope_from_dataframes(sounding):
    d = SkewT()
    band = d.envelope(sounding, sounding, p="pressure", column="airTemperature", units="K", p_units="Pa")
    assert len(band.get_paths()) > 0


def test_series_still_supported(sounding):
    t = sounding.dropna(subset=["airTemperature"])
    d = Tephigram()
    d.temperature(t["airTemperature"], p=t["pressure"], units="K", p_units="Pa")
    (line,) = [ln for ln in d.ax.lines if ln.get_label() == "Temperature"]
    np.testing.assert_allclose(line.get_ydata(), [1000, 850, 500, 300])

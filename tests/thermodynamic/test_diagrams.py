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

import earthkit.plots as ekp  # noqa: E402
from earthkit.plots.thermodynamic import Emagram, SkewT, Tephigram, ThermoGrid  # noqa: E402
from earthkit.plots.thermodynamic.axes import ThermoAxes  # noqa: E402
from earthkit.plots.thermodynamic.grid import LineFamily  # noqa: E402
from earthkit.plots.thermodynamic.ticks import pressure_ticks, temperature_ticks  # noqa: E402

DIAGRAMS = [Tephigram, SkewT, Emagram]

P = np.array([1000.0, 925.0, 850.0, 700.0, 500.0, 300.0, 200.0])
T = np.array([25.0, 20.0, 16.0, 7.0, -10.0, -38.0, -55.0])
Q = np.array([15.0, 12.0, 9.0, 4.0, 1.0, 0.1, 0.02]) / 1000.0


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _profile_da(values, units, p_units="hPa"):
    xr = pytest.importorskip("xarray")
    p = P if p_units == "hPa" else P * 100.0
    return xr.DataArray(
        values,
        dims=["pressure_level"],
        coords={"pressure_level": ("pressure_level", p, {"units": p_units})},
        attrs={"units": units},
    )


def _line_tp(line):
    """The (T, p) data of a line drawn on a ThermoAxes."""
    return np.asarray(line.get_xdata(), dtype=float), np.asarray(line.get_ydata(), dtype=float)


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_axes_and_extent(cls):
    d = cls(temperature_range=(-30, 40), pressure_range=(1000, 200))
    ax = d.ax
    assert isinstance(ax, ThermoAxes)
    x0, x1, y0, y1 = d.extent
    assert ax.get_xlim() == pytest.approx((x0, x1))
    assert ax.get_ylim() == pytest.approx((y0, y1))
    # The bottom-left corner is (minimum temperature, bottom pressure) except
    # on the tephigram, whose bottom isobar arches upwards.
    t, p = d.geometry.inverse(x0, d.geometry.isobar_y(1000.0, x0))
    assert float(t) == pytest.approx(-30.0, abs=0.05)


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_defaults(cls):
    d = cls()
    assert d.temperature_range == cls.default_temperature_range
    assert d.pressure_range == cls.default_pressure_range


@pytest.mark.parametrize("cls", DIAGRAMS)
@pytest.mark.parametrize(
    "kwargs",
    [{"pressure_range": (100, 1000)}, {"temperature_range": (40, -30)}],
)
def test_invalid_ranges(cls, kwargs):
    with pytest.raises(ValueError):
        cls(**kwargs)


def test_reject_non_thermo_axes():
    _, ax = plt.subplots()
    with pytest.raises(TypeError):
        SkewT(ax=ax)


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_plot_uses_temperature_pressure(cls):
    d = cls()
    (line,) = d.ax.plot(T, P)
    # The line keeps its (T, p) data and is mapped through the diagram transform
    t, p = _line_tp(line)
    np.testing.assert_array_equal(t, T)
    np.testing.assert_array_equal(p, P)
    x, y = d.geometry.forward(T, P)
    expected = d.ax.transData.transform(np.column_stack([x, y]))
    np.testing.assert_allclose(line.get_transform().transform(np.column_stack([T, P])), expected)


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_ticks_on_edges(cls):
    d = cls()
    x0, x1, y0, y1 = d.extent
    xpos, xlabels = temperature_ticks(d.geometry, d.extent)
    t, _ = d.geometry.inverse(xpos, np.full_like(xpos, y0))
    np.testing.assert_allclose(t, [float(v) for v in xlabels], atol=1e-6)
    assert np.all((xpos >= x0) & (xpos <= x1))

    ypos, ylabels = pressure_ticks(d.geometry, d.extent)
    _, p = d.geometry.inverse(np.full_like(ypos, x0), ypos)
    np.testing.assert_allclose(p, [float(v) for v in ylabels], rtol=1e-4)
    assert "500" in ylabels


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_grid_drawn_and_removed(cls):
    d = cls()
    d.ax
    n = len(d._grid_artists)
    assert n > 50
    d.grid(False)
    assert d._grid_artists == []
    assert len(d.ax.lines) == 0
    d.grid(mixing_ratios=False)
    assert 0 < len(d._grid_artists) < n


def test_set_extent_redraws():
    d = SkewT()
    d.ax
    before = d.extent
    d.set_extent(pressure_range=(1000, 300))
    assert d.extent != before
    assert d.ax.get_ylim() == pytest.approx(d.extent[2:])


def test_grid_layer():
    assert ThermoGrid().zorder < 2 < ThermoGrid(layer="foreground").zorder
    with pytest.raises(ValueError):
        ThermoGrid(layer="middle")


def test_line_family_update():
    fam = LineFamily(style={"color": "red"})
    assert fam.update(False).enabled is False
    new = fam.update({"color": "grey", "label_frequency": 2, "values": [1, 2]})
    assert new.style["color"] == "grey"
    assert new.label_frequency == 2
    assert new.values == [1, 2]
    assert fam.style["color"] == "red"  # the original is unchanged


def test_saturated_adiabats_reach_the_top():
    # The cold saturated adiabats must not be clamped at about 133 K
    d = Tephigram(
        pressure_range=(1050, 20),
        grid={"isobars": False, "isotherms": False, "dry_adiabats": False, "mixing_ratios": False},
    )
    d.ax
    lines = [a for a in d._grid_artists if hasattr(a, "get_xdata")]
    t_top = [_line_tp(line)[0][-1] for line in lines]
    assert min(t_top) < -140.0


def test_temperature_from_xarray_kelvin_pa():
    d = SkewT()
    line = d.temperature(_profile_da(T + 273.15, "K", p_units="Pa"))
    line = line[0] if isinstance(line, list) else line
    t, p = _line_tp(line)
    np.testing.assert_allclose(t, T)
    np.testing.assert_allclose(p, P)
    assert line.get_label() == "Temperature"


def test_temperature_from_numpy():
    d = Emagram()
    line = d.temperature(T + 273.15, p=P * 100.0, units="K", p_units="Pa", label="T")
    line = line[0] if isinstance(line, list) else line
    t, p = _line_tp(line)
    np.testing.assert_allclose(t, T)
    np.testing.assert_allclose(p, P)


def test_temperature_numpy_requires_pressure():
    with pytest.raises(ValueError):
        SkewT().temperature(T)


def test_dewpoint_from_specific_humidity():
    from earthkit.meteo.thermo import array as thermo

    d = Tephigram()
    line = d.dewpoint(specific_humidity=_profile_da(Q, "kg kg**-1"))
    line = line[0] if isinstance(line, list) else line
    t, p = _line_tp(line)
    np.testing.assert_allclose(p, P)
    np.testing.assert_allclose(t, thermo.dewpoint_from_specific_humidity(Q, P * 100.0) - 273.15)
    assert line.get_linestyle() == "--"


def test_dewpoint_from_relative_humidity():
    d = SkewT()
    line = d.dewpoint(relative_humidity=np.full_like(T, 100.0), temperature=T, p=P)
    line = line[0] if isinstance(line, list) else line
    t, _ = _line_tp(line)
    # saturated air: the dewpoint equals the temperature
    np.testing.assert_allclose(t, T, atol=0.01)


def test_dewpoint_requires_input():
    with pytest.raises(ValueError):
        SkewT().dewpoint()


@pytest.mark.parametrize(
    "method, cls",
    [("add_tephigram", Tephigram), ("add_skewt", SkewT), ("add_emagram", Emagram)],
)
def test_figure_add(method, cls):
    fig = ekp.Figure(rows=1, columns=2)
    d = getattr(fig, method)(pressure_range=(1000, 200))
    assert isinstance(d, cls)
    assert d in fig.subplots
    assert d.pressure_range == (1000.0, 200.0)


def test_top_level_exports():
    assert ekp.Tephigram is Tephigram
    assert ekp.SkewT is SkewT
    assert ekp.Emagram is Emagram


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_wind_barbs_on_isobars(cls):
    d = cls()
    u = np.array([5.0, 10.0, 20.0, 30.0, 40.0, 30.0, 20.0])
    v = np.zeros_like(u)
    barbs = d.wind(u, v, p=P, position=0.9)
    offsets = barbs.get_offsets()
    x0, x1, _, _ = d.extent
    np.testing.assert_allclose(offsets[:, 0], x0 + 0.9 * (x1 - x0))
    # each barb is at the height where its isobar crosses the column
    _, p = d.geometry.inverse(offsets[:, 0], offsets[:, 1])
    np.testing.assert_allclose(p, P, rtol=1e-4)
    # drawn in knots by default
    np.testing.assert_allclose(barbs.u, u * 3600.0 / 1852.0)


def test_wind_speed_direction_matches_components():
    d = SkewT()
    speed = np.full(P.shape, 10.0)
    direction = np.full(P.shape, 270.0)  # westerly
    barbs = d.wind(speed=speed, direction=direction, p=P, knots=False)
    np.testing.assert_allclose(barbs.u, 10.0)
    np.testing.assert_allclose(barbs.v, 0.0, atol=1e-12)


def test_wind_every_and_outside_levels():
    d = SkewT(pressure_range=(1000, 300))
    barbs = d.wind(np.ones_like(P), np.ones_like(P), p=P, every=2)
    # levels 1000, 850, 500, 200 -> 200 hPa is above the top of the diagram
    assert len(barbs.get_offsets()) == 3


def test_wind_requires_input():
    with pytest.raises(ValueError):
        SkewT().wind()


@pytest.mark.parametrize("temperature_range", [(-110.0, 30.0), (-60.0, 60.0), (-20.0, 50.0)])
def test_tephigram_bottom_isobar_level(temperature_range):
    d = Tephigram(temperature_range=temperature_range, pressure_range=(1015, 100))
    # isobars are horizontal at T = a
    t_a = d.geometry.a - 273.15
    assert temperature_range[0] < t_a < temperature_range[1]
    x, y = d.geometry.forward(np.array([t_a - 0.5, t_a + 0.5]), 1015.0)
    assert np.degrees(np.arctan2(y[1] - y[0], x[1] - x[0])) == pytest.approx(0.0, abs=0.1)
    # the ends of the bottom isobar are level, so both bottom corners are on it
    x0, x1, y0, _ = d.extent
    _, p_corners = d.geometry.inverse(np.array([x0, x1]), np.array([y0, y0]))
    np.testing.assert_allclose(p_corners, 1015.0, rtol=0.02)


def test_tephigram_explicit_a():
    assert Tephigram(a=273.15).geometry.a == 273.15


def _fill_tp(collection):
    """The (T, p) vertices of the polygons of a fill on a ThermoAxes."""
    return np.concatenate([path.vertices for path in collection.get_paths()])


@pytest.mark.parametrize("cls", DIAGRAMS)
def test_envelope_numpy(cls):
    d = cls()
    band = d.envelope(T - 2.0, T + 3.0, p=P, color="green", label="spread")
    verts = _fill_tp(band)
    # the band spans the pressure levels and the two bounding profiles
    assert verts[:, 1].min() == pytest.approx(P.min())
    assert verts[:, 1].max() == pytest.approx(P.max())
    for t_lo, t_hi, p in zip(T - 2.0, T + 3.0, P):
        at_p = verts[np.isclose(verts[:, 1], p), 0]
        assert at_p.min() == pytest.approx(t_lo)
        assert at_p.max() == pytest.approx(t_hi)
    assert band.get_label() == "spread"
    # drawn in (T, p) data coordinates through the diagram transform
    assert band.get_transform() == d.ax.transThermoData or band.get_transform().contains_branch(d.ax.transThermo)


def test_envelope_xarray_kelvin_pa():
    d = SkewT()
    lo = _profile_da(T + 273.15 - 1.0, "K", p_units="Pa")
    hi = _profile_da(T + 273.15 + 1.0, "K", p_units="Pa")
    verts = _fill_tp(d.envelope(lo, hi))
    np.testing.assert_allclose(sorted(set(np.round(verts[:, 1], 6))), sorted(P))
    assert verts[:, 0].min() == pytest.approx(T.min() - 1.0)
    assert verts[:, 0].max() == pytest.approx(T.max() + 1.0)


def test_envelope_numpy_units():
    d = SkewT()
    verts = _fill_tp(d.envelope(T + 273.15, T + 274.15, p=P * 100.0, units="K", p_units="Pa"))
    assert verts[:, 0].min() == pytest.approx(T.min())
    assert verts[:, 1].max() == pytest.approx(P.max())


def test_envelope_requires_same_levels():
    d = SkewT()
    lower = _profile_da(T, "degC")
    upper = _profile_da(T + 1.0, "degC").assign_coords(pressure_level=P - 5.0)
    with pytest.raises(ValueError, match="same pressure levels"):
        d.envelope(lower, upper)


def test_envelope_numpy_requires_pressure():
    with pytest.raises(ValueError):
        SkewT().envelope(T, T + 1.0)

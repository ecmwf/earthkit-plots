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

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

pytest.importorskip("earthkit.meteo")

from earthkit.plots.thermodynamic import SkewT, Tephigram  # noqa: E402
from earthkit.plots.thermodynamic.grid import single_line  # noqa: E402
from earthkit.plots.thermodynamic.parcel import ParcelProfiles, level, shading_top  # noqa: E402

K = 273.15
NAN_LEVEL = SimpleNamespace(p=np.nan, t=np.nan)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _level(p_hpa, t_c):
    return SimpleNamespace(p=np.float64(p_hpa * 100.0), t=np.float64(t_c + K))


def _path(lfc=True, el=True):
    """A parcel path like the one returned by earthkit-meteo: K and Pa, ascending pressure, NaN below ground."""
    p = np.array([200.0, 300.0, 500.0, 700.0, 850.0, 900.0, 1000.0, np.nan]) * 100.0
    # parcel minus environment: negative near the ground (CIN), positive aloft
    # (CAPE) and negative again above the EL at about 250 hPa
    tv_env = np.array([-50.0, -40.0, -10.0, 5.0, 15.0, 18.0, 25.0, np.nan]) + K
    tv = tv_env + np.array([-3.0, 2.0, 4.0, 3.0, 1.0, -1.0, 0.0, np.nan])
    return SimpleNamespace(
        p=p,
        t=tv - 1.0,
        tv=tv,
        tv_env=tv_env,
        lcl=_level(920.0, 20.0),
        lfc=_level(880.0, 17.0) if lfc else NAN_LEVEL,
        el=_level(250.0, -45.0) if el else NAN_LEVEL,
    )


def test_parcel_profiles_from_path():
    prof = ParcelProfiles.from_path(_path())
    # ordered from the start of the ascent upwards, NaN levels removed, °C and hPa
    np.testing.assert_allclose(prof.p, [1000, 900, 850, 700, 500, 300, 200])
    np.testing.assert_allclose(prof.tv_env, [25, 18, 15, 5, -10, -40, -50])
    np.testing.assert_allclose(prof.tv - prof.tv_env, [0, -1, 1, 3, 4, 2, -3])
    np.testing.assert_allclose(prof.t, prof.tv - 1.0)


def test_parcel_profiles_requires_single_profile():
    path = _path()
    path.p = np.stack([path.p, path.p], axis=1)
    with pytest.raises(ValueError, match="single profile"):
        ParcelProfiles.from_path(path)


def test_parcel_profiles_requires_pressure():
    path = _path()
    del path.p
    with pytest.raises(TypeError, match="pressure"):
        ParcelProfiles.from_path(path)


def test_level():
    assert level(_level(850.0, 10.0)) == pytest.approx((850.0, 10.0))
    assert level(NAN_LEVEL) is None


def test_shading_top():
    assert shading_top(_path()) == pytest.approx(250.0)
    # buoyant up to the top of the profile
    assert shading_top(_path(el=False)) == -np.inf
    # no free convection
    assert shading_top(_path(lfc=False, el=False)) is None


@pytest.mark.parametrize("virtual", [True, False])
def test_parcel_line(virtual):
    d = Tephigram()
    line = d.parcel(_path(), virtual=virtual)
    line = line[0] if isinstance(line, list) else line
    prof = ParcelProfiles.from_path(_path())
    np.testing.assert_allclose(line.get_xdata(), prof.tv if virtual else prof.t)
    np.testing.assert_allclose(line.get_ydata(), prof.p)
    assert line.get_linestyle() == "--"
    assert line.get_label() == "Parcel"


def _polygon_tp(collection):
    """The (T, p) vertices of the polygons of a fill."""
    return [path.vertices for path in collection.get_paths()]


def test_cape_cin_areas():
    d = SkewT()
    positive, negative = d.cape_cin(_path(), positive_color="red", negative_color="blue")
    assert positive is not None and negative is not None

    pos = np.concatenate(_polygon_tp(positive))
    neg = np.concatenate(_polygon_tp(negative))
    # nothing is shaded above the EL (250 hPa)
    assert pos[:, 1].min() >= 250.0 - 1e-6
    assert neg[:, 1].min() >= 250.0 - 1e-6
    # the positive area reaches up to where the parcel becomes colder than its
    # environment, between 300 and 200 hPa
    assert pos[:, 1].min() < 300.0
    # the negative area near the ground lies between the start and the LFC
    assert neg[:, 1].max() <= 1000.0 + 1e-6
    assert neg[:, 1].min() > 850.0

    np.testing.assert_allclose(positive.get_facecolor()[0][:3], (1.0, 0.0, 0.0))
    np.testing.assert_allclose(negative.get_facecolor()[0][:3], (0.0, 0.0, 1.0))


def test_cape_cin_without_free_convection():
    d = SkewT()
    assert d.cape_cin(_path(lfc=False, el=False)) == (None, None)


def test_cape_cin_up_to_top_without_el():
    # Without an EL the areas are not limited at the top, so the negative area
    # above the last crossing (about 260 hPa) is shaded up to the top of the path
    d = SkewT()
    _, negative = d.cape_cin(_path(el=False))
    neg = np.concatenate(_polygon_tp(negative))
    assert neg[:, 1].min() == pytest.approx(200.0)


def test_info_box_dict_alignment():
    d = SkewT()
    box = d.info_box({"Mode": "surface", "CAPE": "2881 J/kg", "Start p": "1008 hPa"})
    lines = box.txt.get_text().split("\n")
    assert lines == ["   Mode: surface", "   CAPE: 2881 J/kg", "Start p: 1008 hPa"]
    assert box in d.ax.artists
    assert box.txt._text.get_fontfamily() == ["monospace"]


def test_info_box_list_and_str():
    d = SkewT()
    assert d.info_box(["a", "b"]).txt.get_text() == "a\nb"
    assert d.info_box("text").txt.get_text() == "text"


def test_isotherm():
    d = Tephigram()
    line = d.isotherm(0, color="red")
    np.testing.assert_allclose(line.get_xdata(), 0.0)
    p = line.get_ydata()
    # drawn over the full pressure range, independently of the extent
    assert p.max() >= 1100.0 - 1e-6 and p.min() <= 1.0 + 1e-6
    assert line.get_color() == "red"


def test_isobar():
    line = SkewT().isobar(500)
    np.testing.assert_allclose(line.get_ydata(), 500.0)


def test_dry_adiabat():
    from earthkit.meteo.thermo import array as thermo

    line = Tephigram().dry_adiabat(30)
    theta = thermo.potential_temperature(np.asarray(line.get_xdata()) + K, np.asarray(line.get_ydata()) * 100.0)
    np.testing.assert_allclose(theta, 30.0 + K, rtol=1e-10)


def test_saturated_adiabat_through_theta_w():
    t, p = single_line("saturated_adiabats", 20.0)
    # theta_w is the temperature of the pseudoadiabat at 1000 hPa
    assert np.interp(1000.0, p[::-1], t[::-1]) == pytest.approx(20.0, abs=0.05)


def test_mixing_ratio_line_top_pressure():
    from earthkit.meteo.thermo import array as thermo

    line = SkewT().mixing_ratio_line(4, top_pressure=500)
    p = np.asarray(line.get_ydata())
    assert p.min() == pytest.approx(500.0)
    w = thermo.mixing_ratio_from_dewpoint(np.asarray(line.get_xdata()) + K, p * 100.0)
    np.testing.assert_allclose(w, 0.004, rtol=1e-6)


def test_single_line_unknown_family():
    with pytest.raises(ValueError):
        single_line("isohumes", 1.0)


def test_with_earthkit_meteo_parcel():
    from earthkit.meteo import thermo

    # a warm, moist, conditionally unstable sounding with heights from the
    # hypsometric equation
    p = np.array([1000.0, 950, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100]) * 100.0
    t = np.array([30.0, 26, 23, 20, 17, 10, 3, -5, -15, -30, -40, -52, -62, -70]) + K
    td = np.array([24.0, 21, 18, 15, 12, 0, -10, -20, -30, -45, -55, -65, -75, -85]) + K
    q = thermo.specific_humidity_from_dewpoint(td, p)
    tv = thermo.virtual_temperature(t, q)
    dz = 287.0597 * 0.5 * (tv[1:] + tv[:-1]) / 9.80665 * np.log(p[:-1] / p[1:])
    zh = np.concatenate([[0.0], np.cumsum(dz)])

    cape, cin, extras = thermo.surface_cape_cin(
        p[1:], t[1:], q[1:], zh[1:], p[0], t[0], q[0], zh[0], extra_outputs=["parcel_path"]
    )
    path = extras["parcel_path"]
    if not hasattr(path, "p"):
        pytest.skip("earthkit-meteo ParcelPath has no pressure")
    assert cape > 0

    d = Tephigram()
    line = d.parcel(path)
    line = line[0] if isinstance(line, list) else line
    assert line.get_ydata()[0] == pytest.approx(1000.0)
    positive, _ = d.cape_cin(path)
    assert positive is not None and len(positive.get_paths()) > 0

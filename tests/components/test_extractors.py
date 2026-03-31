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

"""
Tests for _apply_data_resampling in extractors.py.

Scope: verify the extractor's branching and argument-passing logic.  We use
lightweight fake objects instead of real Resample/Chain instances — testing
whether Regrid/Unstructured/Bilinear produce numerically correct output is
the responsibility of the resample module's own test suite.
"""

import numpy as np
import pytest

from earthkit.plots.components.extractors import (
    PixelSamplingResult,
    _apply_data_resampling,
    _apply_pixel_sampling,
    _get_subplot_bbox,
)

# ---------------------------------------------------------------------------
# Minimal fakes — enough for isinstance() checks to work correctly
# ---------------------------------------------------------------------------


class _FakeResample:
    """Concrete base; mirrors Resample.apply signature."""

    def __init__(self, name="generic"):
        self._name = name
        self.calls = []  # records (x, y, z) each time apply() is called

    def apply(self, x, y, z, **_kw):
        self.calls.append((x, y, z))
        # Return arrays scaled by 2 so tests can verify the call happened
        return x * 2, y * 2, z * 2


class _FakePixelSampler(_FakeResample):
    """Fake _PixelSampler subclass."""

    pass


class _FakeRegrid(_FakeResample):
    """Fake Regrid: expects gridspec and context kwargs."""

    def apply(self, x, y, z, *, gridspec=None, context=None, **_kw):
        self.calls.append({"x": x, "y": y, "z": z, "gridspec": gridspec, "context": context})
        return x * 2, y * 2, z * 2


class _FakeUnstructured(_FakeResample):
    """Fake Unstructured: records source_crs / target_crs kwargs."""

    def __init__(self, transform=False, **kw):
        super().__init__(**kw)
        self.transform = transform

    def apply(self, x, y, z, *, source_crs=None, target_crs=None, **_kw):
        self.calls.append({"x": x, "y": y, "z": z, "source_crs": source_crs, "target_crs": target_crs})
        return x * 2, y * 2, z * 2


class _FakeChain(_FakeResample):
    """Fake Chain that exposes data_steps and pixel_step."""

    def __init__(self, data_steps=None, pixel_step=None):
        super().__init__(name="chain")
        self.data_steps = data_steps or []
        self.pixel_step = pixel_step


class _FakeSource:
    def __init__(self, gridspec=None, crs=None):
        self.gridspec = gridspec
        self.crs = crs


class _FakeSubplot:
    def __init__(self, crs=None):
        self.crs = crs


# ---------------------------------------------------------------------------
# Monkeypatch helpers
# ---------------------------------------------------------------------------


def _patch_resample_module(monkeypatch, fake_classes):
    """
    Monkeypatch the resample import inside _apply_data_resampling so that
    isinstance() checks resolve against our fake classes.

    fake_classes is a dict with keys: Resample, Chain, Regrid, Unstructured, _PixelSampler.
    """
    import earthkit.plots.resample as resample_mod

    for attr, cls in fake_classes.items():
        monkeypatch.setattr(resample_mod, attr, cls, raising=False)

    # The function does `from earthkit.plots.resample import ...` inside the
    # body, so we also need to patch the module-level names that will be
    # imported at call time.  We achieve this by patching the resample module
    # object itself (already done above) and ensuring the import resolves from
    # there.  No additional action needed because `from X import Y` inside a
    # function reads from sys.modules at call time.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def xyz():
    """Small coordinate / data arrays."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([10.0, 20.0, 30.0])
    z = np.array([100.0, 200.0, 300.0])
    return x, y, z


@pytest.fixture()
def source():
    return _FakeSource(gridspec="gs", crs="src_crs")


@pytest.fixture()
def subplot():
    return _FakeSubplot(crs="tgt_crs")


# ---------------------------------------------------------------------------
# No-op cases
# ---------------------------------------------------------------------------


class TestNoOp:
    def test_false_returns_unchanged(self, xyz, source, subplot):
        x, y, z = xyz
        rx, ry, rz, suppressed = _apply_data_resampling(x, y, z, False, source, subplot, "contourf")
        np.testing.assert_array_equal(rx, x)
        np.testing.assert_array_equal(ry, y)
        np.testing.assert_array_equal(rz, z)
        assert suppressed is False

    def test_none_returns_unchanged(self, xyz, source, subplot):
        x, y, z = xyz
        rx, ry, rz, suppressed = _apply_data_resampling(x, y, z, None, source, subplot, "contourf")
        np.testing.assert_array_equal(rx, x)
        np.testing.assert_array_equal(rz, z)
        assert suppressed is False


# ---------------------------------------------------------------------------
# Generic Resample step
# ---------------------------------------------------------------------------


class TestGenericResample:
    def test_generic_step_called(self, monkeypatch, xyz, source, subplot):
        x, y, z = xyz
        step = _FakeResample()

        import earthkit.plots.resample as rm

        monkeypatch.setattr(rm, "Chain", _FakeChain, raising=False)
        monkeypatch.setattr(rm, "Regrid", _FakeRegrid, raising=False)
        monkeypatch.setattr(rm, "Unstructured", _FakeUnstructured, raising=False)
        monkeypatch.setattr(rm, "_PixelSampler", _FakePixelSampler, raising=False)
        monkeypatch.setattr(rm, "Resample", _FakeResample, raising=False)

        rx, ry, rz, suppressed = _apply_data_resampling(x, y, z, step, source, subplot, "contourf")

        assert len(step.calls) == 1
        np.testing.assert_array_equal(rx, x * 2)
        assert suppressed is False

    def test_generic_step_receives_no_extra_kwargs(self, monkeypatch, xyz, source, subplot):
        """Generic Resample.apply(x, y, z) — no gridspec/crs keywords."""
        x, y, z = xyz
        received_kwargs = {}

        class _Capturing(_FakeResample):
            def apply(self, x, y, z, **kwargs):
                received_kwargs.update(kwargs)
                return x, y, z

        step = _Capturing()

        import earthkit.plots.resample as rm

        monkeypatch.setattr(rm, "Chain", _FakeChain, raising=False)
        monkeypatch.setattr(rm, "Regrid", _FakeRegrid, raising=False)
        monkeypatch.setattr(rm, "Unstructured", _FakeUnstructured, raising=False)
        monkeypatch.setattr(rm, "_PixelSampler", _FakePixelSampler, raising=False)
        monkeypatch.setattr(rm, "Resample", _Capturing, raising=False)

        _apply_data_resampling(x, y, z, step, source, subplot, "contourf")
        assert received_kwargs == {}


# ---------------------------------------------------------------------------
# Regrid step
# ---------------------------------------------------------------------------


class TestRegridStep:
    def _patch(self, monkeypatch):
        import earthkit.plots.resample as rm

        monkeypatch.setattr(rm, "Chain", _FakeChain, raising=False)
        monkeypatch.setattr(rm, "Regrid", _FakeRegrid, raising=False)
        monkeypatch.setattr(rm, "Unstructured", _FakeUnstructured, raising=False)
        monkeypatch.setattr(rm, "_PixelSampler", _FakePixelSampler, raising=False)
        monkeypatch.setattr(rm, "Resample", _FakeResample, raising=False)

    def test_regrid_called_with_gridspec_and_context(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeRegrid()

        _apply_data_resampling(x, y, z, step, source, subplot, "contourf")

        assert len(step.calls) == 1
        call = step.calls[0]
        assert call["gridspec"] == source.gridspec
        assert call["context"] is not None  # PlotContext inferred

    def test_regrid_output_returned(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeRegrid()

        rx, ry, rz, _ = _apply_data_resampling(x, y, z, step, source, subplot, "contourf")
        np.testing.assert_array_equal(rx, x * 2)
        np.testing.assert_array_equal(rz, z * 2)

    def test_regrid_does_not_suppress_domain(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeRegrid()
        _, _, _, suppressed = _apply_data_resampling(x, y, z, step, source, subplot, "contourf")
        assert suppressed is False


# ---------------------------------------------------------------------------
# Unstructured step
# ---------------------------------------------------------------------------


class TestUnstructuredStep:
    def _patch(self, monkeypatch):
        import earthkit.plots.resample as rm

        monkeypatch.setattr(rm, "Chain", _FakeChain, raising=False)
        monkeypatch.setattr(rm, "Regrid", _FakeRegrid, raising=False)
        monkeypatch.setattr(rm, "Unstructured", _FakeUnstructured, raising=False)
        monkeypatch.setattr(rm, "_PixelSampler", _FakePixelSampler, raising=False)
        monkeypatch.setattr(rm, "Resample", _FakeResample, raising=False)

    def test_unstructured_called_with_crs(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeUnstructured()

        _apply_data_resampling(x, y, z, step, source, subplot, "contourf")

        assert len(step.calls) == 1
        call = step.calls[0]
        assert call["source_crs"] == source.crs
        assert call["target_crs"] == subplot.crs

    def test_unstructured_no_transform_does_not_suppress(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeUnstructured(transform=False)

        kw = {"transform": "PLATE_CARREE", "other": 1}
        _, _, _, suppressed = _apply_data_resampling(x, y, z, step, source, subplot, "contourf", kwargs=kw)
        assert suppressed is False
        assert "transform" in kw  # not popped

    def test_unstructured_transform_pops_kwargs_and_suppresses(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeUnstructured(transform=True)

        kw = {"transform": "PLATE_CARREE", "transform_first": True, "other": 1}
        _, _, _, suppressed = _apply_data_resampling(x, y, z, step, source, subplot, "contourf", kwargs=kw)
        assert suppressed is True
        assert "transform" not in kw
        assert "transform_first" not in kw
        assert kw == {"other": 1}  # unrelated key preserved

    def test_unstructured_no_kwargs_dict_still_suppresses(self, monkeypatch, xyz, source, subplot):
        """kwargs=None: suppression flag still set, no KeyError."""
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeUnstructured(transform=True)

        _, _, _, suppressed = _apply_data_resampling(x, y, z, step, source, subplot, "contourf", kwargs=None)
        assert suppressed is True


# ---------------------------------------------------------------------------
# Pixel sampler handling
# ---------------------------------------------------------------------------


class TestPixelSamplerHandling:
    def _patch(self, monkeypatch):
        import earthkit.plots.resample as rm

        monkeypatch.setattr(rm, "Chain", _FakeChain, raising=False)
        monkeypatch.setattr(rm, "Regrid", _FakeRegrid, raising=False)
        monkeypatch.setattr(rm, "Unstructured", _FakeUnstructured, raising=False)
        monkeypatch.setattr(rm, "_PixelSampler", _FakePixelSampler, raising=False)
        monkeypatch.setattr(rm, "Resample", _FakeResample, raising=False)

    def test_pixel_sampler_raises_when_not_allowed(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakePixelSampler()

        with pytest.raises(ValueError, match="pixel-sampler"):
            _apply_data_resampling(x, y, z, step, source, subplot, "scatter", allow_pixel_samplers=False)

    def test_pixel_sampler_skipped_when_allowed(self, monkeypatch, xyz, source, subplot):
        """2D context: pixel step deferred to Step 8.5 — arrays unchanged."""
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakePixelSampler()

        rx, ry, rz, suppressed = _apply_data_resampling(
            x, y, z, step, source, subplot, "contourf", allow_pixel_samplers=True
        )
        # apply() must NOT have been called
        assert step.calls == []
        np.testing.assert_array_equal(rx, x)
        assert suppressed is False


# ---------------------------------------------------------------------------
# Chain dispatch
# ---------------------------------------------------------------------------


class TestChainDispatch:
    def _patch(self, monkeypatch):
        import earthkit.plots.resample as rm

        monkeypatch.setattr(rm, "Chain", _FakeChain, raising=False)
        monkeypatch.setattr(rm, "Regrid", _FakeRegrid, raising=False)
        monkeypatch.setattr(rm, "Unstructured", _FakeUnstructured, raising=False)
        monkeypatch.setattr(rm, "_PixelSampler", _FakePixelSampler, raising=False)
        monkeypatch.setattr(rm, "Resample", _FakeResample, raising=False)

    def test_chain_data_steps_applied_in_order(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        step1 = _FakeResample(name="s1")
        step2 = _FakeResample(name="s2")
        chain = _FakeChain(data_steps=[step1, step2], pixel_step=None)

        rx, ry, rz, _ = _apply_data_resampling(x, y, z, chain, source, subplot, "contourf")

        # Each step doubles the values, so 2 steps → ×4
        np.testing.assert_array_equal(rx, x * 4)
        assert len(step1.calls) == 1
        assert len(step2.calls) == 1

    def test_chain_pixel_step_not_applied(self, monkeypatch, xyz, source, subplot):
        """Pixel step inside Chain is skipped in data-space resampling."""
        self._patch(monkeypatch)
        x, y, z = xyz
        pixel_step = _FakePixelSampler()
        chain = _FakeChain(data_steps=[], pixel_step=pixel_step)

        rx, ry, rz, _ = _apply_data_resampling(x, y, z, chain, source, subplot, "contourf", allow_pixel_samplers=True)
        assert pixel_step.calls == []
        np.testing.assert_array_equal(rx, x)

    def test_chain_pixel_step_raises_when_not_allowed(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        pixel_step = _FakePixelSampler()
        chain = _FakeChain(data_steps=[], pixel_step=pixel_step)

        with pytest.raises(ValueError, match="pixel-sampler"):
            _apply_data_resampling(x, y, z, chain, source, subplot, "scatter", allow_pixel_samplers=False)

    def test_chain_regrid_and_pixel_step(self, monkeypatch, xyz, source, subplot):
        """Chain(Regrid, Bilinear): data step applied, pixel step skipped."""
        self._patch(monkeypatch)
        x, y, z = xyz
        regrid = _FakeRegrid()
        pixel = _FakePixelSampler()
        chain = _FakeChain(data_steps=[regrid], pixel_step=pixel)

        rx, ry, rz, suppressed = _apply_data_resampling(
            x, y, z, chain, source, subplot, "contourf", allow_pixel_samplers=True
        )
        assert len(regrid.calls) == 1
        assert pixel.calls == []
        np.testing.assert_array_equal(rx, x * 2)
        assert suppressed is False


# ===========================================================================
# Tests for _apply_pixel_sampling
#
# Scope: verify the branching logic inside _apply_pixel_sampling.
# CRS/subplot/style dependencies are replaced by lightweight fakes.
# Calls to reproject_to_grid / _reproject_nn are intercepted via
# monkeypatching so that we test dispatch logic, not reprojection numerics.
# ===========================================================================

# ---------------------------------------------------------------------------
# Minimal fakes for pixel-sampling tests
# ---------------------------------------------------------------------------


class _FakeCRS:
    """Pretend CRS — only class name matters for same-CRS detection."""

    def __init__(self, name="PlateCarree"):
        self.__class__ = type(name, (_FakeCRS,), {})


class _FakePixelSamplerResolvable(_FakePixelSampler):
    """Pixel sampler that also exposes resolve()."""

    def __init__(self, nx=10, ny=10, **kw):
        super().__init__(**kw)
        self._nx = nx
        self._ny = ny

    def resolve(self, bbox, crs=None):
        return self._nx, self._ny


class _FakeNearestNeighbour(_FakePixelSamplerResolvable):
    """Fake NearestNeighbour sampler."""

    pass


class _FakeBilinear(_FakePixelSamplerResolvable):
    """Fake Bilinear sampler."""

    pass


class _FakeAx:
    """Minimal matplotlib axes fake."""

    def __init__(self, extent=(-180, 180, -90, 90)):
        self._extent = extent
        self.imshow_calls = []

    def get_extent(self, crs=None):
        return self._extent

    def imshow(self, image, extent=None, origin=None, **kwargs):
        self.imshow_calls.append({"image": image, "extent": extent, "origin": origin, "kwargs": kwargs})
        return object()  # fake mappable


class _FakeSubplotWithCRS:
    def __init__(self, crs=None, ax=None, domain=None):
        self.crs = crs or _FakeCRS("Mollweide")
        self.ax = ax or _FakeAx()
        self.domain = domain


class _FakeSubplotNoCRS:
    """Subplot without a crs attribute — non-geographic axes."""

    ax = _FakeAx()


class _FakeSourcePS:
    def __init__(self, crs=None):
        self.crs = crs
        self.domain = None


class _FakeStyle:
    def to_pcolormesh_kwargs(self, data):
        return {"vmin": 0.0, "vmax": 1.0}


# ---------------------------------------------------------------------------
# Helpers to monkeypatch pixel-sampler isinstance checks
# ---------------------------------------------------------------------------


def _patch_ps_module(monkeypatch, nn_cls, bilinear_cls, pixel_sampler_cls, chain_cls):
    import earthkit.plots.resample as rm

    monkeypatch.setattr(rm, "NearestNeighbour", nn_cls, raising=False)
    monkeypatch.setattr(rm, "Bilinear", bilinear_cls, raising=False)
    monkeypatch.setattr(rm, "_PixelSampler", pixel_sampler_cls, raising=False)
    monkeypatch.setattr(rm, "Chain", chain_cls, raising=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def regular_grid():
    """2-D regular lat/lon meshgrid with scalar z."""
    lons = np.linspace(-10, 10, 5)
    lats = np.linspace(40, 60, 4)
    lon2d, lat2d = np.meshgrid(lons, lats)
    z = np.ones((4, 5))
    return lon2d, lat2d, z


@pytest.fixture()
def scattered():
    """1-D scattered (x, y, z) arrays."""
    x = np.array([-5.0, 0.0, 5.0])
    y = np.array([45.0, 50.0, 55.0])
    z = np.array([1.0, 2.0, 3.0])
    return x, y, z


# ---------------------------------------------------------------------------
# No-op guard conditions
# ---------------------------------------------------------------------------


class TestPixelSamplingNoOp:
    def test_no_pixel_sampler_returns_unchanged(self, regular_grid):
        """Non-pixel resample object → inputs returned unchanged."""
        x, y, z = regular_grid
        result = _apply_pixel_sampling(
            _FakeSubplotWithCRS(),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=_FakeResample(),  # generic, not a _PixelSampler
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=None,
            kwargs={},
        )
        assert isinstance(result, PixelSamplingResult)
        np.testing.assert_array_equal(result.x, x)
        assert result.reprojected is False
        assert result.mappable is None

    def test_no_style_returns_unchanged(self, monkeypatch, regular_grid):
        """no_style=True → pixel sampling skipped entirely."""
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        sampler = _FakeNearestNeighbour()
        result = _apply_pixel_sampling(
            _FakeSubplotWithCRS(),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=True,
            style=None,
            data_crs=None,
            kwargs={},
        )
        assert result.reprojected is False
        assert result.mappable is None

    def test_unsupported_method_returns_unchanged(self, monkeypatch, regular_grid):
        """Method 'scatter' does not support pixel sampling."""
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        sampler = _FakeBilinear()
        result = _apply_pixel_sampling(
            _FakeSubplotWithCRS(),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="scatter",
            no_style=False,
            style=None,
            data_crs=None,
            kwargs={},
        )
        assert result.reprojected is False

    def test_no_crs_on_subplot_returns_unchanged(self, monkeypatch, regular_grid):
        """Non-geographic subplot (no .crs) → no-op."""
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        sampler = _FakeBilinear()
        result = _apply_pixel_sampling(
            _FakeSubplotNoCRS(),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=None,
            kwargs={},
        )
        assert result.reprojected is False

    def test_same_crs_non_scattered_returns_unchanged(self, monkeypatch, regular_grid):
        """Same source and target CRS with non-scattered data → no-op."""
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        shared_crs = _FakeCRS("PlateCarree")
        subplot = _FakeSubplotWithCRS(crs=shared_crs)
        sampler = _FakeBilinear()
        result = _apply_pixel_sampling(
            subplot,
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=shared_crs,
            kwargs={},
        )
        assert result.reprojected is False


# ---------------------------------------------------------------------------
# Bilinear reprojection path
# ---------------------------------------------------------------------------


class TestBilinearPath:
    def test_bilinear_sets_transform_and_reprojected(self, monkeypatch, regular_grid):
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )

        reprojected_arrays = [np.ones((10, 10)), np.ones((10, 10)), np.ones((10, 10))]
        monkeypatch.setattr(
            "earthkit.plots.components._pixel_sampling._reproject_bilinear",
            lambda *a, **kw: tuple(reprojected_arrays),
        )

        target_crs = _FakeCRS("Mollweide")
        subplot = _FakeSubplotWithCRS(crs=target_crs)
        sampler = _FakeBilinear()
        kwargs = {}

        result = _apply_pixel_sampling(
            subplot,
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=_FakeCRS("PlateCarree"),
            kwargs=kwargs,
        )

        assert result.reprojected is True
        assert result.mappable is None
        assert kwargs.get("transform") is target_crs

    def test_pcolormesh_also_triggers_bilinear(self, monkeypatch, regular_grid):
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        monkeypatch.setattr(
            "earthkit.plots.components._pixel_sampling._reproject_bilinear",
            lambda *a, **kw: (x, y, z),
        )
        sampler = _FakeBilinear()
        result = _apply_pixel_sampling(
            _FakeSubplotWithCRS(crs=_FakeCRS("Mollweide")),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="pcolormesh",
            no_style=False,
            style=None,
            data_crs=_FakeCRS("PlateCarree"),
            kwargs={},
        )
        assert result.reprojected is True


# ---------------------------------------------------------------------------
# NearestNeighbour — regular grid → imshow path
# ---------------------------------------------------------------------------


class TestNearestNeighbourImshowPath:
    def test_regular_grid_produces_mappable(self, monkeypatch, regular_grid):
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )

        fake_image = np.ones((10, 10))
        fake_extent = (-10, 10, 40, 60)
        monkeypatch.setattr(
            "earthkit.plots.resample.reproject._reproject_nn",
            lambda *a, **kw: (fake_image, fake_extent),
        )
        # Also patch the module-level import path used inside the function
        import earthkit.plots.resample.reproject as rp

        monkeypatch.setattr(rp, "_reproject_nn", lambda *a, **kw: (fake_image, fake_extent))

        ax = _FakeAx()
        subplot = _FakeSubplotWithCRS(crs=_FakeCRS("Mollweide"), ax=ax)
        sampler = _FakeNearestNeighbour()
        result = _apply_pixel_sampling(
            subplot,
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=False,
            style=_FakeStyle(),
            data_crs=_FakeCRS("PlateCarree"),
            kwargs={},
        )

        assert result.reprojected is True
        assert result.mappable is not None
        assert len(ax.imshow_calls) == 1
        call = ax.imshow_calls[0]
        assert call["extent"] == fake_extent
        assert call["origin"] == "lower"

    def test_imshow_strips_transform_kwargs(self, monkeypatch, regular_grid):
        """Transform and transform_first must not be forwarded to imshow."""
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        import earthkit.plots.resample.reproject as rp

        monkeypatch.setattr(rp, "_reproject_nn", lambda *a, **kw: (np.ones((10, 10)), (-10, 10, 40, 60)))

        ax = _FakeAx()
        subplot = _FakeSubplotWithCRS(crs=_FakeCRS("Mollweide"), ax=ax)
        sampler = _FakeNearestNeighbour()
        kwargs = {"transform": "PLATE_CARREE", "transform_first": True, "alpha": 0.8}
        _apply_pixel_sampling(
            subplot,
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=_FakeCRS("PlateCarree"),
            kwargs=kwargs,
        )

        forwarded = ax.imshow_calls[0]["kwargs"]
        assert "transform" not in forwarded
        assert "transform_first" not in forwarded
        assert forwarded.get("alpha") == 0.8


# ---------------------------------------------------------------------------
# NearestNeighbour — curvilinear fallback to Bilinear
# ---------------------------------------------------------------------------


class TestNearestNeighbourCurvilinearFallback:
    def test_curvilinear_grid_falls_back_to_bilinear(self, monkeypatch):
        """Curvilinear NN grid falls back to _reproject_bilinear."""
        # Build a deliberately non-regular 2-D grid (rows not constant)
        x = np.array([[0, 1, 2], [0.5, 1.5, 2.5]])
        y = np.array([[40, 40, 40], [50, 51, 52]])  # not constant along rows
        z = np.ones((2, 3))

        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )

        bilinear_called = []
        monkeypatch.setattr(
            "earthkit.plots.components._pixel_sampling._reproject_bilinear",
            lambda *a, **kw: bilinear_called.append(kw) or (x, y, z),
        )

        sampler = _FakeNearestNeighbour()
        result = _apply_pixel_sampling(
            _FakeSubplotWithCRS(crs=_FakeCRS("Mollweide")),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=sampler,
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=_FakeCRS("PlateCarree"),
            kwargs={},
        )

        assert len(bilinear_called) == 1
        assert bilinear_called[0]["use_nearest"] is True
        assert result.reprojected is True
        assert result.mappable is None


# ---------------------------------------------------------------------------
# Chain with pixel step
# ---------------------------------------------------------------------------


class TestChainWithPixelStep:
    def test_chain_pixel_step_used_as_sampler(self, monkeypatch, regular_grid):
        """Pixel step inside a Chain is used when CRS differs."""
        x, y, z = regular_grid
        _patch_ps_module(
            monkeypatch,
            _FakeNearestNeighbour,
            _FakeBilinear,
            _FakePixelSamplerResolvable,
            _FakeChain,
        )
        monkeypatch.setattr(
            "earthkit.plots.components._pixel_sampling._reproject_bilinear",
            lambda *a, **kw: (x, y, z),
        )

        pixel = _FakeBilinear()
        chain = _FakeChain(data_steps=[], pixel_step=pixel)
        result = _apply_pixel_sampling(
            _FakeSubplotWithCRS(crs=_FakeCRS("Mollweide")),
            _FakeSourcePS(),
            x,
            y,
            z,
            resample=chain,
            method_name="contourf",
            no_style=False,
            style=None,
            data_crs=_FakeCRS("PlateCarree"),
            kwargs={},
        )
        assert result.reprojected is True


# ---------------------------------------------------------------------------
# _get_subplot_bbox
# ---------------------------------------------------------------------------


class TestGetSubplotBbox:
    def test_uses_ax_get_extent(self):
        ax = _FakeAx(extent=(-90, 90, -45, 45))
        subplot = _FakeSubplotWithCRS(ax=ax)
        bbox = _get_subplot_bbox(subplot, subplot.crs)
        assert bbox == (-90, 90, -45, 45)

    def test_falls_back_to_domain_bbox(self):
        class _FakeAx2:
            def get_extent(self, crs=None):
                raise AttributeError("no get_extent")

        class _FakeDomain:
            class bbox:
                @staticmethod
                def to_cartopy_bounds():
                    return (-10, 10, 40, 60)

        subplot = type("S", (), {"ax": _FakeAx2(), "domain": _FakeDomain(), "crs": None})()
        bbox = _get_subplot_bbox(subplot, None)
        assert bbox == (-10, 10, 40, 60)

    def test_falls_back_to_global_when_no_domain(self):
        class _FakeAx3:
            def get_extent(self, crs=None):
                raise AttributeError

        subplot = type("S", (), {"ax": _FakeAx3(), "domain": None, "crs": None})()
        bbox = _get_subplot_bbox(subplot, None)
        assert bbox == (-180, 180, -90, 90)

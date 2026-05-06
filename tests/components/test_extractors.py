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


# ---------------------------------------------------------------------------
# 0-360 longitude normalisation (bug: data west of 0° invisible with
# crs=PlateCarree() on fieldlist / regular lat-lon data)
# ---------------------------------------------------------------------------


class TestLongitudeNormalisation:
    """
    extract_plottables_2D must normalise 0–360 longitudes to –180..+180
    before passing them to matplotlib when both source and target CRS are
    cylindrical (e.g. PlateCarree).  Without this, cartopy clips everything
    west of 0° because the axes extent is –180..+180 but the data runs 0..360.

    We intercept the matplotlib call via monkeypatching to inspect the
    x-values that would be rendered, avoiding any figure/display dependency.
    Uses earthkit.plots.Map() directly (standalone, no Figure.add_map()) to
    avoid the lazy-gridspec None-return issue.
    """

    def _make_0_360_data(self, as_2d_meshgrid=False):
        """Return an xarray DataArray with 0–360 longitudes."""
        import xarray as xr

        lons = np.linspace(0, 359, 36)
        lats = np.linspace(-90, 90, 19)
        z = np.random.default_rng(0).random((len(lats), len(lons)))

        if as_2d_meshgrid:
            lon2d, lat2d = np.meshgrid(lons, lats)
            return xr.DataArray(
                z,
                dims=["y", "x"],
                coords={"latitude": (["y", "x"], lat2d), "longitude": (["y", "x"], lon2d)},
            )
        return xr.DataArray(
            z,
            dims=["latitude", "longitude"],
            coords={"latitude": lats, "longitude": lons},
        )

    def _run_and_capture(self, data, monkeypatch, crs=None):
        """
        Run extract_plottables_2D with a Map(crs=...) and capture the
        x-values passed to the matplotlib contourf call.

        Uses earthkit.plots.Map() standalone so subplot is a real Map object,
        then forces axes creation via subplot.ax before patching contourf.
        """
        import cartopy.crs as ccrs
        import matplotlib.pyplot as plt

        import earthkit.plots
        from earthkit.plots.components._pipeline import extract_plottables_2D

        if crs is None:
            crs = ccrs.PlateCarree()

        # Standalone Map creates its own Figure(1, 1) lazily — subplot is real.
        subplot = earthkit.plots.Map(crs=crs)

        # Force axes creation now so we can patch the live axes class.
        ax = subplot.ax

        captured = {}
        real_contourf = ax.__class__.contourf

        def _fake_contourf(self_ax, x, y, z, **kwargs):
            captured["x"] = np.asarray(x)
            return real_contourf(self_ax, x, y, z, **kwargs)

        monkeypatch.setattr(ax.__class__, "contourf", _fake_contourf)

        try:
            extract_plottables_2D(
                subplot=subplot,
                method_name="contourf",
                args=(data,),
                resample=False,
            )
        finally:
            # Always restore, then close figure to avoid matplotlib state leak.
            monkeypatch.setattr(ax.__class__, "contourf", real_contourf)
            plt.close("all")

        return captured.get("x")

    def test_1d_lons_normalised_to_minus180_180(self, monkeypatch):
        """1D longitude coordinate (xarray dim-coord path) is normalised to –180..+180."""
        data = self._make_0_360_data(as_2d_meshgrid=False)
        x = self._run_and_capture(data, monkeypatch)
        assert x is not None, "contourf was never called"
        assert x.max() <= 180, f"x.max()={x.max():.1f} — expected ≤ 180"
        assert x.min() >= -180, f"x.min()={x.min():.1f} — expected ≥ -180"

    def test_2d_lons_normalised_to_minus180_180(self, monkeypatch):
        """2D meshgrid longitude coordinate is normalised to –180..+180."""
        data = self._make_0_360_data(as_2d_meshgrid=True)
        x = self._run_and_capture(data, monkeypatch)
        assert x is not None, "contourf was never called"
        assert x.max() <= 180, f"x.max()={x.max():.1f} — expected ≤ 180"
        assert x.min() >= -180, f"x.min()={x.min():.1f} — expected ≥ -180"

    def test_minus180_180_data_unchanged(self, monkeypatch):
        """Data already in –180..+180 must not be modified by the normalisation step."""
        import xarray as xr

        lons = np.linspace(-180, 179, 36)
        lats = np.linspace(-90, 90, 19)
        z = np.random.default_rng(1).random((len(lats), len(lons)))
        data = xr.DataArray(
            z,
            dims=["latitude", "longitude"],
            coords={"latitude": lats, "longitude": lons},
        )
        x = self._run_and_capture(data, monkeypatch)
        assert x is not None, "contourf was never called"
        assert x.min() >= -180
        assert x.max() <= 180

    def test_no_normalisation_for_non_cylindrical_crs(self, monkeypatch):
        """
        With a non-cylindrical CRS (Robinson) the normalisation step must not
        fire — cartopy handles coordinate transformation itself for those
        projections.  The plot must complete without error.
        """
        import cartopy.crs as ccrs

        data = self._make_0_360_data()
        # Just check it doesn't raise; x capture is a bonus.
        self._run_and_capture(data, monkeypatch, crs=ccrs.Robinson())


# ---------------------------------------------------------------------------
# 0-360 longitude normalisation for the 1D pipeline (point_cloud / scatter)
# ---------------------------------------------------------------------------


class TestLongitudeNormalisation1D:
    """
    extract_plottables_1D must normalise 0–360 longitudes to –180..+180 when
    the subplot is a geographic Map with a cylindrical CRS (e.g. PlateCarree).

    point_cloud calls scatter which uses the 1D pipeline.  Without this fix,
    scatter points whose longitude > 180 fall outside the default axes extent
    and are invisible — producing the same half-globe symptom as the 2D bug.

    Data is a flat (unstructured) array of points, matching the GRIB fieldlist
    case where earthkit returns 1D lon/lat arrays.
    """

    def _make_0_360_points(self):
        """Return an xarray DataArray with unstructured points spanning 0–360."""
        import xarray as xr

        rng = np.random.default_rng(42)
        lons = np.linspace(0, 355, 72)
        lats = rng.uniform(-90, 90, 72)
        z = rng.random(72)
        return xr.DataArray(
            z,
            dims=["points"],
            coords={"longitude": ("points", lons), "latitude": ("points", lats)},
        )

    def _run_scatter_and_capture(self, data, monkeypatch, crs=None):
        """
        Run extract_plottables_1D with method_name='scatter' on a Map and
        capture the x-values passed to ax.scatter.
        """
        import cartopy.crs as ccrs
        import matplotlib.pyplot as plt

        import earthkit.plots
        from earthkit.plots.components._pipeline import extract_plottables_1D

        if crs is None:
            crs = ccrs.PlateCarree()

        subplot = earthkit.plots.Map(crs=crs)
        ax = subplot.ax

        captured = {}
        real_scatter = ax.__class__.scatter

        def _fake_scatter(self_ax, x, y, *args, **kwargs):
            captured["x"] = np.asarray(x)
            return real_scatter(self_ax, x, y, *args, **kwargs)

        monkeypatch.setattr(ax.__class__, "scatter", _fake_scatter)

        try:
            extract_plottables_1D(
                subplot=subplot,
                method_name="scatter",
                args=(data,),
                resample=False,
            )
        finally:
            monkeypatch.setattr(ax.__class__, "scatter", real_scatter)
            plt.close("all")

        return captured.get("x")

    def test_point_cloud_lons_normalised_to_minus180_180(self, monkeypatch):
        """scatter/point_cloud normalises 0–360 longitudes to –180..+180 on a PlateCarree map."""
        data = self._make_0_360_points()
        x = self._run_scatter_and_capture(data, monkeypatch)
        assert x is not None, "scatter was never called"
        assert x.max() <= 180, f"x.max()={x.max():.1f} — expected ≤ 180"
        assert x.min() >= -180, f"x.min()={x.min():.1f} — expected ≥ -180"

    def test_point_cloud_minus180_180_unchanged(self, monkeypatch):
        """Data already in –180..+180 is not modified by the normalisation step."""
        import xarray as xr

        rng = np.random.default_rng(7)
        lons = np.linspace(-180, 175, 72)
        lats = rng.uniform(-90, 90, 72)
        z = rng.random(72)
        data = xr.DataArray(
            z,
            dims=["points"],
            coords={"longitude": ("points", lons), "latitude": ("points", lats)},
        )
        x = self._run_scatter_and_capture(data, monkeypatch)
        assert x is not None, "scatter was never called"
        assert x.min() >= -180
        assert x.max() <= 180

    def test_point_cloud_no_normalisation_for_non_cylindrical_crs(self, monkeypatch):
        """Non-cylindrical CRS (Robinson) does not trigger normalisation."""
        import cartopy.crs as ccrs

        data = self._make_0_360_points()
        # Should complete without error; cartopy handles the transform itself.
        self._run_scatter_and_capture(data, monkeypatch, crs=ccrs.Robinson())


# ---------------------------------------------------------------------------
# resolve_auto unit tests
# ---------------------------------------------------------------------------


class _FakeAxWithSize:
    """Matplotlib Axes stub that reports a fixed pixel size via get_window_extent."""

    def __init__(self, width, height):
        self._width = width
        self._height = height

    def get_figure(self):
        return self

    def get_renderer(self):
        return None

    def canvas(self):
        return self

    def get_window_extent(self, renderer=None):
        class _BB:
            pass

        bb = _BB()
        bb.width = self._width
        bb.height = self._height
        return bb

    # figsize fallback attributes (used when get_window_extent raises)
    def get_figwidth(self):
        return self._width / 100.0

    def get_figheight(self):
        return self._height / 100.0

    dpi = 100

    def get_position(self):
        class _Pos:
            width = 1.0
            height = 1.0

        return _Pos()


class _FakeAxFallback:
    """Axes stub whose get_window_extent raises, forcing the figsize fallback path."""

    def __init__(self, figwidth_px, figheight_px):
        self._figwidth_px = figwidth_px
        self._figheight_px = figheight_px

    def get_figure(self):
        return self

    def get_renderer(self):
        raise RuntimeError("no renderer")

    def canvas(self):
        return self

    def get_window_extent(self, renderer=None):
        raise RuntimeError("no renderer pre-draw")

    def get_figwidth(self):
        return self._figwidth_px / 100.0

    def get_figheight(self):
        return self._figheight_px / 100.0

    dpi = 100

    def get_position(self):
        class _Pos:
            width = 1.0
            height = 1.0

        return _Pos()


class TestResolveAuto:
    """Unit tests for _PixelSampler.resolve_auto."""

    _BBOX = (-180, 180, -90, 90)
    _CRS = None  # not used by resolve_auto currently

    def _sampler(self, nx="auto", ny="auto"):
        from earthkit.plots.resample import Bilinear

        return Bilinear(nx=nx, ny=ny)

    # --- is_auto property ---------------------------------------------------

    def test_is_auto_true_when_both_auto(self):
        s = self._sampler()
        assert s.is_auto is True

    def test_is_auto_false_when_fixed(self):
        from earthkit.plots.resample import Bilinear

        assert Bilinear(500).is_auto is False

    def test_is_auto_true_when_one_axis_auto(self):
        s = self._sampler(nx="auto", ny=500)
        assert s.is_auto is True

    # --- repr ---------------------------------------------------------------

    def test_repr_auto(self):
        from earthkit.plots.resample import Bilinear

        assert repr(Bilinear("auto")) == "Bilinear(nx='auto', ny='auto')"

    def test_repr_mixed(self):
        from earthkit.plots.resample import Bilinear

        assert repr(Bilinear(nx="auto", ny=500)) == "Bilinear(nx='auto', ny=500)"

    # --- default cap only (no data, no ax) ----------------------------------

    def test_no_data_no_ax_returns_defaults(self):
        from earthkit.plots.resample import Bilinear

        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x_values=None, y_values=None, ax=None)
        assert nx == s.DEFAULT_NX
        assert ny == s.DEFAULT_NY

    def test_resolve_dispatches_to_resolve_auto_for_auto_mode(self):
        """resolve() on an auto sampler must not raise and returns defaults."""
        from earthkit.plots.resample import Bilinear

        s = Bilinear("auto")
        nx, ny = s.resolve(self._BBOX)
        assert nx == s.DEFAULT_NX
        assert ny == s.DEFAULT_NY

    # --- data cap -----------------------------------------------------------

    def test_data_cap_2d_grid(self):
        """Auto resolution is capped at source grid size - 1 for 2-D arrays."""
        from earthkit.plots.resample import Bilinear

        x = np.zeros((50, 30))  # ny=50, nx=30
        y = np.zeros((50, 30))
        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=None)
        assert nx == 29  # 30 - 1
        assert ny == 49  # 50 - 1

    def test_data_cap_1d_scattered(self):
        """Auto resolution is capped at array length - 1 for 1-D arrays."""
        from earthkit.plots.resample import Bilinear

        x = np.linspace(-10, 10, 100)
        y = np.linspace(40, 60, 80)
        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=None)
        assert nx == 99  # 100 - 1
        assert ny == 79  # 80 - 1

    def test_data_cap_does_not_go_below_2(self):
        """Floor of 2 even for tiny source arrays."""
        from earthkit.plots.resample import Bilinear

        x = np.array([0.0, 1.0])  # length 2 → cap = max(1, 2) = 2
        y = np.array([0.0])  # length 1 → cap = max(0, 2) = 2
        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=None)
        assert nx == 2
        assert ny == 2

    # --- pixel cap (renderer path) -----------------------------------------

    def test_pixel_cap_via_renderer(self):
        """Subplot pixel size is used when it is smaller than data and default."""
        from earthkit.plots.resample import Bilinear

        # Source is large (900×900), default is 1000 — pixel cap (200×150) wins.
        x = np.zeros((900, 900))
        y = np.zeros((900, 900))
        ax = _FakeAxWithSize(width=200, height=150)
        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=ax)
        assert nx == 200
        assert ny == 150

    # --- pixel cap (figsize fallback path) ----------------------------------

    def test_pixel_cap_via_figsize_fallback(self):
        """figsize×dpi fallback is used when get_window_extent raises."""
        from earthkit.plots.resample import Bilinear

        x = np.zeros((900, 900))
        y = np.zeros((900, 900))
        ax = _FakeAxFallback(figwidth_px=300, figheight_px=250)
        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=ax)
        assert nx == 300
        assert ny == 250

    # --- default cap wins ---------------------------------------------------

    def test_default_cap_wins_when_data_larger(self):
        """Default (1000) is the binding cap when data > 1000."""
        from earthkit.plots.resample import Bilinear

        x = np.zeros((1500, 1500))
        y = np.zeros((1500, 1500))
        s = Bilinear("auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=None)
        assert nx == s.DEFAULT_NX
        assert ny == s.DEFAULT_NY

    # --- mixed auto / fixed axes --------------------------------------------

    def test_mixed_auto_nx_fixed_ny(self):
        """nx='auto' is resolved; ny uses the fixed value unchanged."""
        from earthkit.plots.resample import Bilinear

        x = np.zeros((900, 50))
        y = np.zeros((900, 50))
        s = Bilinear(nx="auto", ny=300)
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=None)
        assert nx == 49  # data cap 50 - 1
        assert ny == 300  # fixed, untouched

    def test_mixed_fixed_nx_auto_ny(self):
        """ny='auto' is resolved; nx uses the fixed value unchanged."""
        from earthkit.plots.resample import Bilinear

        x = np.zeros((50, 900))
        y = np.zeros((50, 900))
        s = Bilinear(nx=400, ny="auto")
        nx, ny = s.resolve_auto(self._BBOX, self._CRS, x, y, ax=None)
        assert nx == 400  # fixed, untouched
        assert ny == 49  # data cap 50 - 1

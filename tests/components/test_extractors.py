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

from earthkit.plots.components.extractors import _apply_data_resampling


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
        self.calls.append(
            {"x": x, "y": y, "z": z, "source_crs": source_crs, "target_crs": target_crs}
        )
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
    import earthkit.plots.components.extractors as extractors_mod

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
        rx, ry, rz, suppressed = _apply_data_resampling(
            x, y, z, False, source, subplot, "contourf"
        )
        np.testing.assert_array_equal(rx, x)
        np.testing.assert_array_equal(ry, y)
        np.testing.assert_array_equal(rz, z)
        assert suppressed is False

    def test_none_returns_unchanged(self, xyz, source, subplot):
        x, y, z = xyz
        rx, ry, rz, suppressed = _apply_data_resampling(
            x, y, z, None, source, subplot, "contourf"
        )
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

        rx, ry, rz, suppressed = _apply_data_resampling(
            x, y, z, step, source, subplot, "contourf"
        )

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
        _, _, _, suppressed = _apply_data_resampling(
            x, y, z, step, source, subplot, "contourf", kwargs=kw
        )
        assert suppressed is False
        assert "transform" in kw  # not popped

    def test_unstructured_transform_pops_kwargs_and_suppresses(
        self, monkeypatch, xyz, source, subplot
    ):
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeUnstructured(transform=True)

        kw = {"transform": "PLATE_CARREE", "transform_first": True, "other": 1}
        _, _, _, suppressed = _apply_data_resampling(
            x, y, z, step, source, subplot, "contourf", kwargs=kw
        )
        assert suppressed is True
        assert "transform" not in kw
        assert "transform_first" not in kw
        assert kw == {"other": 1}  # unrelated key preserved

    def test_unstructured_no_kwargs_dict_still_suppresses(
        self, monkeypatch, xyz, source, subplot
    ):
        """kwargs=None: suppression flag still set, no KeyError."""
        self._patch(monkeypatch)
        x, y, z = xyz
        step = _FakeUnstructured(transform=True)

        _, _, _, suppressed = _apply_data_resampling(
            x, y, z, step, source, subplot, "contourf", kwargs=None
        )
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
            _apply_data_resampling(
                x, y, z, step, source, subplot, "scatter", allow_pixel_samplers=False
            )

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

        rx, ry, rz, _ = _apply_data_resampling(
            x, y, z, chain, source, subplot, "contourf", allow_pixel_samplers=True
        )
        assert pixel_step.calls == []
        np.testing.assert_array_equal(rx, x)

    def test_chain_pixel_step_raises_when_not_allowed(self, monkeypatch, xyz, source, subplot):
        self._patch(monkeypatch)
        x, y, z = xyz
        pixel_step = _FakePixelSampler()
        chain = _FakeChain(data_steps=[], pixel_step=pixel_step)

        with pytest.raises(ValueError, match="pixel-sampler"):
            _apply_data_resampling(
                x, y, z, chain, source, subplot, "scatter", allow_pixel_samplers=False
            )

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

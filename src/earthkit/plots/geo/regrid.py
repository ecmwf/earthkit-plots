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

import logging
from functools import cached_property

LOG = logging.getLogger(__name__)


def _convert_spec(spec):
    if not isinstance(spec, dict):
        if hasattr(spec, "spec"):
            return spec.spec
        elif hasattr(spec, "to_dict"):
            return spec.to_dict()
        raise ValueError(
            "Grid spec must be a dict or have 'spec' property or a 'to_dict' method."
        )
    return spec


class LegacyRegridExecutor:
    subarea_support = False

    @staticmethod
    def is_valid():
        try:
            from earthkit.regrid import interpolate  # noqa: F401

            return True
        except ImportError:
            return False

    def regrid(array, in_grid, out_grid):
        from earthkit.regrid import interpolate

        in_grid = _convert_spec(in_grid)
        out_grid = _convert_spec(out_grid)

        print(f"Regrid specs: in_grid={in_grid}, out_grid={out_grid}")
        LOG.debug(
            "Regridding using precomputed regridder, in_grid=",
            in_grid,
            " out_grid=",
            out_grid,
        )

        v = interpolate(array, in_grid=in_grid, out_grid=out_grid)
        # print(f"Regrid result: {v.max()}, {v.min()}, {v.shape}")
        # print(f" col: {v[::100,0]}")
        return v


class MirRegridExecutor:
    subarea_support = True

    @staticmethod
    def is_valid():
        try:
            from earthkit.regrid.array import regrid  # noqa: F401

            try:
                import mir  # noqa: F401
            except Exception:
                LOG.debug("mir package not available for MirRegridExecutor")
                return False
        except ImportError:
            return False

    @staticmethod
    def regrid(array, in_grid, out_grid):
        from earthkit.regrid.array import regrid

        in_grid = _convert_spec(in_grid)
        out_grid = _convert_spec(out_grid)

        # temporary workaround for icon grids until the linear interpolation is fixed
        _kwargs = {}
        if isinstance(in_grid, dict):
            if "icon" in in_grid.get("grid", "").lower():
                _kwargs["interpolation"] = "nn"

        LOG.debug(
            "Regridding using MIR regridder, in_grid=", in_grid, " out_grid=", out_grid
        )
        r = regrid(array, in_grid=in_grid, out_grid=out_grid, **_kwargs)
        v = r[0]
        return v


class Regrid:
    # from Python 3.12 onwards, cached_property is not thread safe.
    # Consider making this call thread safe if needed in future.
    @cached_property
    def executor(self):
        for r in [MirRegridExecutor, LegacyRegridExecutor]:
            if r.is_valid():
                return r
        return None

    def __call__(self, array, in_grid, out_grid):
        if self.executor is None:
            raise ImportError(
                "Regridding not available. Please install the earthkit-regrid package."
            )

        return self.executor.regrid(array, in_grid, out_grid)


REGRID = Regrid()


def can_regrid():
    r = REGRID.executor is not None
    return r is not None


def has_subarea_support():
    r = REGRID.executor
    if r is not None:
        return r.subarea_support
    return False


regrid = REGRID

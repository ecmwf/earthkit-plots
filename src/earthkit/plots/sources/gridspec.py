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
import re
from abc import ABCMeta, abstractmethod
from functools import cached_property

LOG = logging.getLogger(__name__)

HEALPIX_PATTERN = re.compile(r"^[Hh]\d+$")
RGG_PATTERN = re.compile(r"^[OoNn]\d+$")

# TODO: refactor this when the gridSpec is implemented in earthkit


class LegacyGridSpec(metaclass=ABCMeta):
    """
    A specification of a grid used in a Source.

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data object containing the grid metadata.
    """

    GRIDSPEC_KEYS = None

    @classmethod
    def from_data(cls, data):
        """
        Identify and create a LegacyGridSpec object from the given data.

        Parameters
        ----------
        data : earthkit.plots.sources.Source
            The data object containing the grid metadata.
        """
        d = cls._first(data)
        for gs in LEGACY_GRIDSPECS:
            if gs.type_match(d):
                return gs(d)

    def __init__(self, data):
        self.data = data

    @staticmethod
    @abstractmethod
    def type_match(data):
        pass

    @staticmethod
    def _guess_grid(data):
        if isinstance(data, dict):
            gs = data.get("gridSpec")
            if gs:
                grid = gs.get("grid")
                if grid:
                    return grid

            return data.get("gridType")

        data = LegacyGridSpec._first(data)

        # ecCodes does not yet support the gridSpec key and prints a warning
        # when accessing it. We only try to get it for a non-GRIB field
        gs = None
        if hasattr(data, "_metadata") and data._metadata.data_format() != "grib":
            gs = data.metadata("gridSpec", default=None)

        if gs:
            grid = gs.get("grid")
            if grid:
                return grid

        grid = data.metadata("gridType", default=None)
        return grid

    def _from_gridspec(self, data):
        def _get_first(x):
            if isinstance(x, list):
                return x[0]
            return x

        # try gridSpec metadata key
        # ecCodes does not yet support the gridSpec key and prints a warning
        # when accessing it. We only try to get it for a non-GRIB field
        gs = None
        if hasattr(data, "_metadata") and data._metadata.data_format() != "grib":
            gs = data.metadata("gridSpec", default=None)

        if gs:
            return _get_first(gs)

        # try method on metadata object
        if not gs:
            try:
                gs = {k: gs.get(k) for k in self.GRIDSPEC_KEYS if gs.get(k) is not None}
                if gs:
                    return _get_first(gs)
            except Exception:
                pass

    @abstractmethod
    def to_dict(self):
        pass

    @staticmethod
    def _first(data):
        if hasattr(data, "__len__"):
            return data[0]
        return data

    @property
    def name(self):
        return self.NAME


class ReducedGG(LegacyGridSpec):
    """A reduced Gaussian grid specification."""

    GRIDSPEC_KEYS = ["grid"]
    NAME = "reduced_gg"

    def to_dict(self):
        d = self._first(self.data)

        gs = self._from_gridspec(d)
        if gs:
            return gs

        # try to build from raw metadata keys
        n = d.metadata("N", default=None)
        if n is not None:
            if d.metadata("isOctahedral", default=0):
                g = f"O{n}"
            else:
                g = f"N{n}"

            return {"grid": g}

        grid = LegacyGridSpec._guess_grid(d)
        if isinstance(grid, str) and RGG_PATTERN.match(grid):
            return {"grid": grid.upper()}

    @staticmethod
    def type_match(data):
        try:
            grid = LegacyGridSpec._guess_grid(data)
            if isinstance(grid, str):
                if grid == "reduced_gg":
                    return True
                if RGG_PATTERN.match(grid):
                    return True
        except Exception:
            pass

        return False


class HEALPix(LegacyGridSpec):
    """A HEALPix grid specification."""

    GRIDSPEC_KEYS = ["grid", "ordering"]
    NAME = "healpix"

    def to_dict(self):
        d = self._first(self.data)

        gs = self._from_gridspec(d)
        if gs:
            return gs

        # try to build from raw metadata keys
        n = d.metadata("Nside", default=None)
        o = d.metadata("orderingConvention", default=None)
        if isinstance(o, list):
            o = o[0]
            n = n[0]
        if n is not None and o is not None:
            return {"grid": f"H{n}", "ordering": o}

    @staticmethod
    def type_match(data):
        try:
            grid = LegacyGridSpec._guess_grid(data)
            if isinstance(grid, str):
                if grid == "healpix":
                    return True
                if HEALPIX_PATTERN.match(grid):
                    return True
        except Exception:
            pass
        return False


LEGACY_GRIDSPECS = [HEALPix, ReducedGG]


class GridSpec:
    """
    A specification of a grid used in a Source.

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data object containing the grid metadata.
    """

    def __init__(self, gs: dict | str):
        from eckit.geo import Grid

        self._grid = Grid(gs)
        # TODO: we need to store the original grid spec because Grid.spec failing at the moment
        self._grid_spec_in = gs

    @staticmethod
    def from_data(data):
        def _get_one(d_data, keys):
            for key in keys:
                value = d_data.get(key)
                if value is not None:
                    return value
            return None

        gs = None

        if isinstance(data, dict):
            gs = _get_one(data, ["grid_spec", "gridSpec"])
        else:
            data = GridSpec._first(data)

            if hasattr(data, "grid_spec"):
                gs = data.grid_spec
            else:
                md = data.metadata()
                if hasattr(md, "grid_spec"):
                    gs = md.grid_spec
                else:
                    gs = md.geography.grid_spec()

                if gs is None:
                    try:
                        gs = _get_one(md, ["grid_spec", "gridSpec"])
                    except Exception:
                        pass

        if gs is not None:
            # TODO: converting legacy earthkit-data gridspec object to dict
            if not isinstance(gs, dict):
                if hasattr(gs, "_d"):
                    gs = dict(**gs._d)
                    # remove unsupported keys
                    for k in [
                        "j_points_consecutive",
                        "i_scans_negatively",
                        "j_scans_positively",
                        "type",
                    ]:
                        gs.pop(k, None)
            LOG.debug("Creating Grid from gridspec:", type(gs))
            return GridSpec(gs)

        return None

    @staticmethod
    def _first(data):
        if hasattr(data, "__len__"):
            return data[0]
        return data

    def to_dict(self):
        # TODO: refactor this
        # This is a temporary solution because the order/ordering default
        # is "nested" in eckit.geo.Grid but it is "ring" in the matrix interface of
        # earthkit-regrid.

        try:
            spec = self._grid.spec.copy()

        except Exception:
            # fallback to the original grid spec if Grid.spec is not working
            if isinstance(self._grid_spec_in, dict):
                spec = self._grid_spec_in.copy()
            else:
                import json

                spec = json.loads(self._grid_spec_in)

        if self.name == "healpix":
            if any(k in spec for k in ("ordering", "order")):
                return spec
            else:
                spec["order"] = "nested"
                return spec

        return spec

    @property
    def name(self):
        # TODO: refactor this

        # NOTE: Grid.spec failing at the moment, we need to use the original grid spec to guess the grid type for now
        try:
            grid = self._grid.spec.get("grid")
        except Exception:
            if isinstance(self._grid_spec_in, str):
                import json

                grid = json.loads(self._grid_spec_in).get("grid")
            elif isinstance(self._grid_spec_in, dict):
                grid = self._grid_spec_in.get("grid")

        if grid:
            if isinstance(grid, str):
                if HEALPIX_PATTERN.match(grid):
                    return "healpix"
                if RGG_PATTERN.match(grid):
                    return "reduced_gg"
        return "unknown"


class GridSpecAccessor:
    # from Python 3.12 onwards, cached_property is not thread safe.
    # Consider making this call thread safe if needed in future.
    @cached_property
    def has_grid(self):
        try:
            from earthkit.data.core.geography import Geography

            if hasattr(Geography, "grid_spec"):
                from eckit.geo import Grid  # noqa: F401

                return True
        except Exception:
            return False

    def __call__(self, data):
        if self.has_grid:
            return GridSpec.from_data(data)
        else:
            return LegacyGridSpec.from_data(data)


get_grid_spec = GridSpecAccessor()

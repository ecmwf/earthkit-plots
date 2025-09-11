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

import re
from abc import ABCMeta, abstractmethod

HEALPIX_PATTERN = re.compile(r"^[Hh]\d+$")
RGG_PATTERN = re.compile(r"^[OoNn]\d+$")

# TODO: refactor this when the gridSpec is implemented in earthkit


class GridSpec(metaclass=ABCMeta):
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
        Identify and create a GridSpec object from the given data.

        Parameters
        ----------
        data : earthkit.plots.sources.Source
            The data object containing the grid metadata.
        """
        d = cls._first(data)
        for gs in GRIDSPECS:
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

        data = GridSpec._first(data)
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


class ReducedGG(GridSpec):
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

        grid = GridSpec._guess_grid(d)
        if isinstance(grid, str) and RGG_PATTERN.match(grid):
            return {"grid": grid.upper()}

    @staticmethod
    def type_match(data):
        try:
            grid = GridSpec._guess_grid(data)
            if isinstance(grid, str):
                if grid == "reduced_gg":
                    return True
                if RGG_PATTERN.match(grid):
                    return True
        except Exception:
            pass

        return False


class HEALPix(GridSpec):
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
            grid = GridSpec._guess_grid(data)
            if isinstance(grid, str):
                if grid == "healpix":
                    return True
                if HEALPIX_PATTERN.match(grid):
                    return True
        except Exception:
            pass
        return False


GRIDSPECS = [HEALPix, ReducedGG]

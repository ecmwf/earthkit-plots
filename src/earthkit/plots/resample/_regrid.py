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

import numpy as np

from earthkit.plots.resample._base import Resample


def _convert_spec(spec):
    """Normalise a grid spec to a plain dict for earthkit-geo."""
    if not isinstance(spec, dict):
        if hasattr(spec, "spec"):
            return spec.spec
        elif hasattr(spec, "to_dict"):
            return spec.to_dict()
        raise ValueError("Grid spec must be a dict or have a 'spec' property or a 'to_dict' method.")
    return spec


def _is_structured_grid(gridspec):
    """
    Return True when *gridspec* indicates a HEALPix or reduced Gaussian grid —
    the only grids for which earthkit-geo is used.

    Gridspec objects (``GridSpec``, ``LegacyGridSpec``) carry a ``.name``
    property that returns ``'healpix'``, ``'reduced_gg'``, or ``'unknown'``.
    Plain dicts (e.g. from a user-supplied ``source_grid``) are inspected for a
    ``"grid"`` key whose value matches the HEALPix (``H<N>``) or reduced
    Gaussian (``O<N>`` / ``N<N>``) naming conventions.
    """
    if gridspec is None:
        return False

    # Prefer the .name property on GridSpec / LegacyGridSpec objects
    if hasattr(gridspec, "name"):
        return gridspec.name in ("healpix", "reduced_gg", "orca")

    # Fall back to inspecting the dict representation
    if isinstance(gridspec, dict):
        grid_value = gridspec.get("grid", "")
    else:
        try:
            d = _convert_spec(gridspec)
            grid_value = d.get("grid", "") if isinstance(d, dict) else ""
        except Exception:
            return False

    if not isinstance(grid_value, str):
        return False

    from earthkit.plots.sources.gridspec import (
        HEALPIX_PATTERN,
        ORCA_PATTERN,
        RGG_PATTERN,
    )

    # H<N> = HEALPix,  O<N> or N<N> = reduced Gaussian,  e?orca<N>_[TUVW] = ORCA
    return bool(HEALPIX_PATTERN.match(grid_value) or RGG_PATTERN.match(grid_value) or ORCA_PATTERN.match(grid_value))


def _generate_latlon_grid(resolution):
    """Generate a 2-D regular lat/lon meshgrid at *resolution* degrees."""
    lat_v = np.linspace(90, -90, int(180 / resolution) + 1)
    lon_v = np.linspace(0, 360 - resolution, int(360 / resolution))
    lon, lat = np.meshgrid(lon_v, lat_v)
    return lon, lat


class _MirRegridExecutor:
    subarea_support = True

    # Records why the last is_valid() check failed, so the eventual error message
    # can explain the real cause (e.g. a broken `mir` native library) instead of
    # always blaming earthkit-geo.
    last_import_error = None

    @staticmethod
    def is_valid():
        try:
            from earthkit.geo.grids.array import regrid  # noqa: F401
        except ImportError as err:
            _MirRegridExecutor.last_import_error = f"failed to import earthkit-geo: {err!r}"
            return False

        try:
            import mir  # noqa: F401
        except Exception as err:
            _MirRegridExecutor.last_import_error = f"failed to import mir: {err!r}"
            return False

        _MirRegridExecutor.last_import_error = None
        return True

    @staticmethod
    def call(array, in_grid, out_grid):
        import logging

        from earthkit.geo.grids.array import regrid

        LOG = logging.getLogger(__name__)
        _kwargs = {}
        if isinstance(in_grid, dict) and "icon" in in_grid.get("grid", "").lower():
            _kwargs["interpolation"] = "nn"
        LOG.debug("Regridding using MIR, in_grid=%s out_grid=%s", in_grid, out_grid)
        try:
            # Attempt to regrid using precomputed weights if possible, which is often faster
            r = regrid(
                array,
                in_grid=in_grid,
                out_grid=out_grid,
                backend="precomputed",
                **_kwargs,
            )
        except ValueError:
            # Fall back to mir regridding if precomputed weights are not available for this grid pair
            r = regrid(array, in_grid=in_grid, out_grid=out_grid, **_kwargs)
        return r[0]


_REGRID_METHOD_ALIASES = {
    "nearest": "nearest-neighbour",
}

_VALID_REGRID_METHODS = {"linear", "nearest-neighbour"}


class Regrid(Resample):
    """
    Resample data onto a regular latitude/longitude grid using earthkit-geo.

    This resampler converts the source data to a regular lat/lon grid **in data
    space** before plotting, making the result independent of the target map
    CRS.  Regridding via earthkit-geo is only attempted when the source data
    is on a HEALPix or reduced Gaussian grid (detected either from the source's
    own gridspec or from the explicit ``source_grid`` argument).  For all other
    grids the class raises an informative error — use :class:`Bilinear` or
    :class:`NearestNeighbour` for generic lat/lon data instead.

    Parameters
    ----------
    resolution : float, optional
        Output grid spacing in degrees.  Defaults to ``0.2``.
    method : str, optional
        Interpolation method: ``'linear'`` (default) or ``'nearest-neighbour'``
        (alias ``'nearest'``).
    source_grid : dict, optional
        Explicit earthkit-geo input grid spec.  If provided it overrides
        whatever gridspec the source carries.  Use this when the source does not
        carry metadata (e.g. raw numpy arrays) but the grid type is known.

    Examples
    --------
    >>> Regrid()  # 0.2° lat/lon, linear
    >>> Regrid(resolution=1.0)  # 1° lat/lon
    >>> Regrid(resolution=0.5, methoxwd="nearest")
    >>> Regrid(source_grid={"grid": "healpix", "ordering": "ring", "nside": 32})
    >>> Regrid.at_resolution(0.1)
    """

    DEFAULT_RESOLUTION = 0.2

    def __init__(self, resolution=None, out_grid=None, method="linear", in_grid=None):
        if out_grid is not None and resolution is None:
            resolution = out_grid["grid"][0]
        self._resolution = float(resolution) if resolution is not None else self.DEFAULT_RESOLUTION

        method = _REGRID_METHOD_ALIASES.get(method, method)
        if method not in _VALID_REGRID_METHODS:
            raise ValueError(f"Regrid: method must be one of {sorted(_VALID_REGRID_METHODS)!r}, got {method!r}.")
        self.method = method
        self.source_grid = in_grid

    @classmethod
    def at_resolution(cls, resolution, method="linear", source_grid=None):
        """
        Create a :class:`Regrid` resampler at a specific output resolution.

        Parameters
        ----------
        resolution : float
            Output grid spacing in degrees.
        method : str, optional
            Interpolation method (``'linear'`` or ``'nearest-neighbour'``).
        source_grid : dict, optional
            Explicit input grid spec for earthkit-geo.

        Returns
        -------
        Regrid
        """
        return cls(resolution=resolution, method=method, source_grid=source_grid)

    # ------------------------------------------------------------------
    # earthkit-geo availability helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_executor():
        """Return the best available regrid executor, or None."""
        for cls in [_MirRegridExecutor]:
            if cls.is_valid():
                return cls
        return None

    @classmethod
    def available(cls):
        """Return True if earthkit-geo is installed and usable."""
        return cls._find_executor() is not None

    @classmethod
    def has_subarea_support(cls):
        """Return True if the available executor supports sub-area regridding."""
        executor = cls._find_executor()
        return executor.subarea_support if executor is not None else False

    @staticmethod
    def _call_regrid(array, in_grid, out_grid):
        """Call the best available executor."""
        executor = Regrid._find_executor()
        if executor is None:
            detail = _MirRegridExecutor.last_import_error
            message = "Regridding not available. Please install the earthkit-geo package at a version >= 1.0.0rc6"
            if detail:
                message += f" (underlying cause: {detail})"
            raise ImportError(message)
        return executor.call(array, in_grid, out_grid)

    # ------------------------------------------------------------------
    # Public apply
    # ------------------------------------------------------------------

    def apply(self, x_values, y_values, z_values, gridspec=None, context=None):
        """
        Regrid ``z_values`` onto a regular lat/lon grid via earthkit-geo.

        Parameters
        ----------
        x_values, y_values : np.ndarray
            Source coordinate arrays (passed through unchanged; the regridder
            uses the gridspec, not the coordinate arrays).
        z_values : np.ndarray
            Source data values.
        gridspec : optional
            Grid specification from the source object.  Merged with
            ``self.source_grid`` (the explicit arg takes precedence).
        context : PlotContext, optional
            Only geographic plots are regridded; Cartesian plots are
            returned unchanged.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            ``(lon_2d, lat_2d, z_2d)`` on the regular lat/lon output grid.
        """
        from earthkit.plots.sources.context import PlotContext

        _context = context or PlotContext.GEOGRAPHIC_2D
        if not _context.is_geographic:
            return x_values, y_values, z_values

        # Determine the effective in_grid spec
        in_grid = self.source_grid or gridspec
        if in_grid is None or not _is_structured_grid(in_grid):
            raise ValueError(
                "Regrid can only be used with HEALPix or reduced Gaussian source grids. "
                "Pass source_grid=<gridspec> explicitly, or use Bilinear/NearestNeighbour "
                "for regular lat/lon data."
            )

        in_grid_spec = _convert_spec(in_grid)
        out_grid_spec = {"grid": [self._resolution, self._resolution]}
        if self.method == "nearest-neighbour":
            out_grid_spec["interpolation"] = "nearest-neighbour"

        z_new = self._call_regrid(z_values, in_grid=in_grid_spec, out_grid=out_grid_spec)
        lon_2d, lat_2d = _generate_latlon_grid(self._resolution)
        return lon_2d, lat_2d, z_new

    def __repr__(self):
        parts = [f"resolution={self._resolution}", f"method={self.method!r}"]
        if self.source_grid is not None:
            parts.append(f"source_grid={self.source_grid!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"


def _call_regrid_compat(array, in_grid, out_grid):
    """Module-level helper that exposes the regrid call for the geo/regrid shim."""
    in_grid = _convert_spec(in_grid)
    out_grid = _convert_spec(out_grid)
    return Regrid._call_regrid(array, in_grid=in_grid, out_grid=out_grid)

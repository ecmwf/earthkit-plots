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

"""Data-space Akima interpolation for rectilinear contour grids."""

import numpy as np

from earthkit.plots.resample._base import Resample


class Akima(Resample):
    """Resample a rectilinear grid using separable Akima interpolation.

    This is not a native 2-D Akima contour generator. Interpolation is performed
    in the input coordinate system, first across rows and then down columns.
    Missing values divide rows/columns into independent contiguous segments.

    Parameters
    ----------
    factor : int, default 3
        Number of subdivisions per original grid interval when nx/ny are not
        given. Useful for data-space resampling outside the plotting pipeline.
    nx, ny : int or ``"auto"``, optional
        Target axis lengths. ``"auto"`` uses the viewport's pixel dimensions
        (capped at 1000 per axis), just like ``Bilinear("auto")``. When one
        axis is specified, the other defaults to ``"auto"``.
    max_points : int, default 4000000
        Maximum number of points in the output grid (including masked points).
    """

    def __init__(self, factor=3, max_points=4_000_000, *, nx=None, ny=None):
        if isinstance(factor, (bool, np.bool_)) or not isinstance(factor, (int, np.integer)) or factor < 1:
            raise ValueError("Akima factor must be a positive integer")
        if isinstance(max_points, (bool, np.bool_)) or not isinstance(max_points, (int, np.integer)) or max_points < 4:
            raise ValueError("Akima max_points must be an integer of at least 4")
        self.factor = int(factor)
        self.max_points = int(max_points)
        for size, name in ((nx, "nx"), (ny, "ny")):
            if size is not None and size != "auto" and (
                isinstance(size, (bool, np.bool_)) or not isinstance(size, (int, np.integer)) or size < 2
            ):
                raise ValueError(f"Akima {name} must be 'auto' or an integer of at least 2")
        self.nx = nx
        self.ny = ny

    def resolve(self, ax=None):
        """Resolve configured nx/ny using the same pixel policy as Bilinear."""
        from earthkit.plots.resample._pixel_sampler import Bilinear

        # Skip Bilinear's source-size cap: Akima can also upscale coarse data.
        sampler = Bilinear(nx=self.nx if self.nx is not None else "auto", ny=self.ny if self.ny is not None else "auto")
        return sampler.resolve_auto(None, None, None, None, ax=ax)

    def apply(self, x, y, z, *, nx=None, ny=None):
        """Return interpolated ``(x, y, z)`` with optional target axis lengths.

        ``nx`` and ``ny`` override the interval-based ``factor`` for this call;
        unlike a factor, they can also downsample a dense input grid.
        """
        try:
            from scipy.interpolate import Akima1DInterpolator
        except ImportError as exc:
            raise ImportError("Akima interpolation requires SciPy; install earthkit-plots[akima].") from exc

        x, y = np.asarray(x), np.asarray(y)
        if x.ndim == y.ndim == 2 and x.shape == y.shape:
            x_axis, y_axis = x[0, :], y[:, 0]
            if not (np.allclose(x, x_axis[None, :]) and np.allclose(y, y_axis[:, None])):
                raise ValueError("Akima requires a rectilinear grid; regrid curvilinear coordinates first")
            meshgrid = True
        elif x.ndim == y.ndim == 1:
            x_axis, y_axis = x, y
            meshgrid = False
        else:
            raise ValueError("Akima requires 1-D x/y axes or matching 2-D rectilinear meshgrids")

        values = np.ma.asarray(z)
        if values.ndim != 2 or values.shape != (y_axis.size, x_axis.size):
            raise ValueError("Akima requires 2-D values with shape (len(y), len(x)); regrid scattered points first")
        if min(x_axis.size, y_axis.size) < 2:
            raise ValueError("Akima requires at least two coordinates on each axis")

        def direction(axis, name):
            if not np.issubdtype(axis.dtype, np.number) or not np.all(np.isfinite(axis)):
                raise ValueError(f"Akima {name} coordinates must be finite numbers")
            steps = np.diff(axis)
            if np.all(steps > 0):
                return 1
            if np.all(steps < 0):
                return -1
            raise ValueError(f"Akima {name} coordinates must be strictly monotonic and distinct")

        x_dir, y_dir = direction(x_axis, "x"), direction(y_axis, "y")
        for count, name in ((nx, "nx"), (ny, "ny")):
            if count is not None and (
                isinstance(count, (bool, np.bool_)) or not isinstance(count, (int, np.integer)) or count < 2
            ):
                raise ValueError(f"Akima {name} must be an integer of at least 2")
        if (self.nx is not None or self.ny is not None) and (nx is None or ny is None):
            resolved_nx, resolved_ny = self.resolve()
            nx = resolved_nx if nx is None else nx
            ny = resolved_ny if ny is None else ny
        nx = int(nx) if nx is not None else (x_axis.size - 1) * self.factor + 1
        ny = int(ny) if ny is not None else (y_axis.size - 1) * self.factor + 1
        if nx * ny > self.max_points:
            raise ValueError(f"Akima output would contain {nx * ny} points (limit {self.max_points})")

        x_new = np.linspace(x_axis[0], x_axis[-1], nx)
        y_new = np.linspace(y_axis[0], y_axis[-1], ny)
        # Reversing both axes keeps SciPy's interpolation coordinates increasing.
        x_in = x_axis[::x_dir]
        y_in = y_axis[::y_dir]
        data = np.ma.filled(values.astype(float), np.nan)[::y_dir, ::x_dir]
        x_out = x_new[::x_dir]
        y_out = y_new[::y_dir]

        def interpolate_lines(coords, target, array):
            result = np.full((array.shape[0], target.size), np.nan)
            for i, row in enumerate(array):
                valid = np.isfinite(row)
                edges = np.diff(np.r_[False, valid, False].astype(int))
                for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
                    inside = (target >= coords[start]) & (target <= coords[end - 1])
                    if end - start == 1:
                        inside &= np.isclose(target, coords[start], rtol=0, atol=abs(coords[-1] - coords[0]) * 1e-12)
                        result[i, inside] = row[start]
                    else:
                        result[i, inside] = Akima1DInterpolator(coords[start:end], row[start:end])(target[inside])
            return result

        # Work row-wise for both passes, transposing for the y direction.
        intermediate = interpolate_lines(x_in, x_out, data)
        output = interpolate_lines(y_in, y_out, intermediate.T).T
        if not np.all(np.isfinite(data)):
            # Never fill across an invalid original cell, even if the second
            # interpolation pass has valid values on both sides of the hole.
            def brackets(coords, target):
                right = np.searchsorted(coords, target)
                right = np.clip(right, 0, coords.size - 1)
                left = np.where(coords[right] == target, right, np.maximum(right - 1, 0))
                return left, right

            xl, xr = brackets(x_in, x_out)
            yl, yr = brackets(y_in, y_out)
            valid = np.isfinite(data)
            supported = valid[np.ix_(yl, xl)] & valid[np.ix_(yl, xr)]
            supported &= valid[np.ix_(yr, xl)] & valid[np.ix_(yr, xr)]
            output[~supported] = np.nan
        output = output[::y_dir, ::x_dir]
        if np.ma.isMaskedArray(z) or not np.all(np.isfinite(data)):
            output = np.ma.masked_invalid(output)
        if meshgrid:
            x_new, y_new = np.meshgrid(x_new, y_new)
        return x_new, y_new, output

    def __repr__(self):
        return f"Akima(factor={self.factor}, nx={self.nx!r}, ny={self.ny!r}, max_points={self.max_points})"

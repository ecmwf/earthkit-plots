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

import cartopy.crs as ccrs
import numpy as np
from scipy.interpolate import griddata

from earthkit.plots.geo import grids


class Resample:
    def apply(self, data):
        """
        Apply the resampling technique to the data. This method should be overridden by subclasses.

        Parameters
        ----------
        data : np.array
            The data to be resampled.

        Returns
        -------
        np.array
            The resampled data.

        Raises
        ------
        NotImplementedError
            If the subclass does not override this method.
        """
        raise NotImplementedError("Subclasses must override this method.")

    def __repr__(self):
        """
        Return a string representation of the resampler.

        Returns
        -------
        str
            A string that represents the resampler object. Can be customized by subclasses.
        """
        return f"{self.__class__.__name__}()"


class Subsample(Resample):
    def __init__(self, *args, nx=None, ny=None, mode="fixed"):
        if args:
            if any((nx, ny)):
                raise ValueError(
                    f"{self.__class__.__name__} can take positional arguments or "
                    "keyword arguments, but not a combination of both."
                )
            if len(args) == 1:
                self.nx = self.ny = args[0]
            elif len(args) == 2:
                self.nx, self.ny = args
            else:
                raise ValueError(
                    f"{self.__class__.__name__} can take at most 2 positional "
                    f"arguments; received {len(args)}"
                )
        else:
            self.nx = nx
            self.ny = ny

        self.shape = (self.nx, self.ny)

        if mode not in ["stride", "fixed"]:
            raise ValueError("Mode must be 'stride' or 'fixed'")
        self.mode = mode

    def _fixed_steps(self, x_values, y_values):
        x_step = 1
        if self.nx:
            if len(x_values.shape) == 1:
                x_step = len(x_values) // (self.nx - 1)
            else:
                x_step = x_values.shape[1] // (self.nx - 1)
            x_step = max(1, x_step)

        y_step = 1
        if self.ny:
            if len(y_values.shape) == 1:
                y_step = len(y_values) // (self.ny - 1)
            else:
                y_step = y_values.shape[0] // (self.ny - 1)
            y_step = max(1, y_step)

        return x_step, y_step

    def apply(self, x_values, y_values, *values, **kwargs):
        if self.mode == "stride":
            x_step = self.nx
            y_step = self.ny
        elif self.mode == "fixed":
            x_step, y_step = self._fixed_steps(x_values, y_values)

        if len(x_values.shape) == 1:
            x_values = x_values[::x_step]
        else:
            x_values = x_values[::y_step, ::x_step]

        if len(y_values.shape) == 1:
            y_values = y_values[::y_values]
        else:
            y_values = y_values[::y_step, ::x_step]

        values = (v[::y_step, ::x_step] for v in values)

        return [x_values, y_values, *values]

    def __repr__(self):
        return f"{self.__class__.__name__}(nx={self.nx}, ny={self.ny})"


class Regrid(Subsample):
    def apply(self, x_values, y_values, *values, source_crs, target_crs, extents):
        # Ensure CRS definitions
        source_crs = source_crs or ccrs.PlateCarree()
        target_crs = target_crs or ccrs.PlateCarree()

        xmin, xmax, ymin, ymax = extents
        target_x_linspace = np.linspace(xmin, xmax, self.nx)
        target_y_linspace = np.linspace(ymin, ymax, self.ny)
        target_x_grid, target_y_grid = np.meshgrid(target_x_linspace, target_y_linspace)

        # Transform source coordinates to target CRS
        transformed_points = target_crs.transform_points(
            source_crs, x_values.flatten(), y_values.flatten()
        )
        source_x, source_y = transformed_points[..., 0], transformed_points[..., 1]

        # Filter out NaNs after transformation
        mask = ~np.isnan(source_x) & ~np.isnan(source_y)
        source_x, source_y = source_x[mask], source_y[mask]
        valid_values = [val.flatten()[mask] for val in values]

        # Resample values onto the new grid
        resampled_values = []
        for val in valid_values:
            interpolated_data = griddata(
                (source_x, source_y),  # Valid source coordinates in target CRS
                val,  # Corresponding data
                (
                    target_x_grid.flatten(),
                    target_y_grid.flatten(),
                ),  # Target grid coordinates
                method="linear",
                fill_value=np.nan,  # Handle points outside convex hull
            )
            resampled_values.append(interpolated_data.reshape(target_y_grid.shape))

        return [target_x_grid, target_y_grid, *resampled_values]

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(nx={self.nx}, ny={self.ny}, mode='{self.mode}')"
        )


class Interpolate(Resample):
    """
    Resample data onto a new grid using interpolation.

    Parameters
    ----------
    target_shape : None | tuple[int, int] | int, optional
        The shape of the target grid. If an integer is provided, the target grid will be square.
    target_resolution : None | tuple[float, float] | float, optional
        The resolution of the target grid. If a float is provided, the target grid will be square.
    method : str, optional
        The interpolation method to use. Must be one of 'linear', 'nearest', or 'cubic'.
    distance_threshold : None | float | int | str, optional
        The maximum distance between the source and target points for interpolation to be used.
        If None, all points will be used.
    transform : bool, optional
        Whether to transform the source coordinates to the target CRS before resampling.
        Default is True.
    """

    def __init__(
        self,
        target_shape: None | tuple[int, int] | int = None,
        target_resolution: None | tuple[float, float] | float = None,
        method: str = "linear",
        distance_threshold: None | float | int | str = None,
        transform: bool = True,
    ):
        """
        Initialize the interpolation resampler.
        """
        if target_shape is not None and not isinstance(target_shape, (tuple, list)):
            target_shape = (target_shape, target_shape)

        if target_resolution is not None and not isinstance(
            target_resolution, (tuple, list)
        ):
            target_resolution = (target_resolution, target_resolution)

        self.target_shape = target_shape
        self.target_resolution = target_resolution
        self.method = method
        self.distance_threshold = distance_threshold
        self.transform = transform

    def apply(self, x, y, z, source_crs=None, target_crs=None):
        """
        Apply interpolation to resample data onto a new grid.

        Parameters
        ----------
        x : array-like
            Source x-coordinates.
        y : array-like
            Source y-coordinates.
        z : array-like
            Source values to be interpolated.
        source_crs : CRS, optional
            Coordinate reference system of the source data.
        target_crs : CRS, optional
            Coordinate reference system of the target grid.

        Returns
        -------
        array-like
            Interpolated values on the target grid.
        """
        if self.transform:
            source_crs = source_crs or ccrs.PlateCarree()
            target_crs = target_crs or ccrs.PlateCarree()
            transformed_points = target_crs.transform_points(
                source_crs, x.flatten(), y.flatten()
            )
            target_x = transformed_points[..., 0].reshape(x.shape)
            target_y = transformed_points[..., 1].reshape(y.shape)
        else:
            target_x, target_y = x, y

        return grids.interpolate_unstructured(
            target_x,
            target_y,
            z,
            target_shape=self.target_shape,
            target_resolution=self.target_resolution,
            method=self.method,
            distance_threshold=self.distance_threshold,
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(target_shape={self.target_shape}, "
            f"target_resolution={self.target_resolution}, method={self.method}, "
            f"distance_threshold={self.distance_threshold})"
        )

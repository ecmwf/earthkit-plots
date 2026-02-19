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

from earthkit.plots.resample._base import Resample


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
        from earthkit.plots.resample.grids import interpolate_unstructured

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

        return interpolate_unstructured(
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

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


from typing import Optional, Union, List
import numpy as np

from earthkit.plots import metadata
from earthkit.plots.styles import colors as ekp_colors


__all__ = ["Style"]

def compute_levels(
    data: np.ndarray,
    step: Optional[float] = None,
    reference: Optional[float] = None,
    divergence_point: Optional[float] = None,
) -> list[float]:
    """
    Compute contour levels from data using step/reference/divergence parameters.
    
    Args:
        data: Data array to compute levels for
        step: Step size between levels
        reference: Reference point for level alignment (levels will be multiples of step from this point)
        divergence_point: Center point for diverging scales (forces symmetric range)
    
    Returns:
        List of level values
    """
    if step is None:
        # No step specified, let matplotlib handle it
        return None
    
    # Get data range
    min_value = np.nanmin(data)
    max_value = np.nanmax(data)
    
    if np.isnan(min_value) or min_value == max_value:
        return None
    
    # Apply divergence point if specified (symmetric range)
    if divergence_point is not None:
        max_diff = max(
            abs(max_value - divergence_point),
            abs(divergence_point - min_value)
        )
        min_value = divergence_point - max_diff
        max_value = divergence_point + max_diff
    
    # Set reference point (default to step)
    if reference is None:
        reference = step
    
    # Align min_value to reference
    max_modifier = reference % step
    min_modifier = max_modifier if max_modifier == 0 else step - max_modifier
    min_value = min_value - (min_value % step) - min_modifier
    
    # Generate levels
    levels = np.arange(min_value, max_value + step, step)
    
    # Remove first level if it's below data minimum
    if len(levels) > 1 and levels[1] <= np.nanmin(data):
        levels = levels[1:]
    
    return levels.tolist()


class Style:
    
    def __init__(
        self,
        colors: Optional[Union[list, str]] = None,
        levels: Optional[Union[list, dict]] = None,
        units: Optional[str] = None,
        units_label: Optional[str] = None,
        scale_factor: Optional[float] = None,
        normalize: bool = True,
        anomaly: bool = False,
        **kwargs,
    ):
        self._colors = colors
        self._levels = levels
        self._units = units
        self._units_label = units_label
        self.scale_factor = scale_factor
        self.anomaly = anomaly
        self._normalize = normalize
        self._kwargs = kwargs

    def levels(self, data: np.ndarray) -> Optional[list[float]]:
        if isinstance(self._levels, dict):
            return compute_levels(
                data,
                step=self._levels.get("step"),
                reference=self._levels.get("reference"),
                divergence_point=self._levels.get("divergence_point"),
            )
        return self._levels
    
    @property
    def units(self):
        """Formatted units for use in figure text."""
        if self._units_label is not None:
            return self._units_label
        elif self._units is not None:
            return self._units

    def apply_scale_factor(self, values):
        """Apply the scale factor to some values."""
        if self.scale_factor is not None:
            values *= self.scale_factor
        return values

    def convert_units(self, values, source_units):
        """
        Convert some values from their source units to this `Style`'s units.

        Parameters
        ----------
        values : numpy.ndarray
            The values to convert from their source units to this `Style`'s
            units.
        source_units : str
            The source units of the given values.
        """
        if self._units is None or source_units is None:
            return values

        if self.anomaly and metadata.units.anomaly_equivalence(source_units):
            return values

        return metadata.units.convert(values, source_units, self._units)
    
    def to_matplotlib_kwargs(self, data: np.ndarray) -> dict:
        """
        Convert the Style to matplotlib keyword arguments suitable for plotting functions.

        Parameters
        ----------
        data : np.ndarray
            The data array to be plotted, used to compute levels if needed.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib plotting functions
            (pcolormesh, contourf, contour, etc.)
        """
        levels = self.levels(data)
        kwargs = self._kwargs.copy()

        if levels is not None:
            # When levels are specified, create colormap and normalization
            cmap, norm = ekp_colors.cmap_and_norm(
                self._colors,
                levels,
                normalize=self._normalize,
                extend=kwargs.get("extend", None),
                extend_levels=kwargs.get("extend_levels", True),
            )
            kwargs.update({"cmap": cmap, "norm": norm})
            # Include levels for contour-based plots
            kwargs["levels"] = levels
        else:
            # When no levels specified, just pass through the colormap/colors
            if self._colors is not None:
                if isinstance(self._colors, str):
                    # Named colormap
                    kwargs["cmap"] = self._colors
                elif isinstance(self._colors, list):
                    # List of colors - create a colormap from it
                    from matplotlib.colors import ListedColormap, LinearSegmentedColormap
                    # Use LinearSegmentedColormap for smooth gradients
                    kwargs["cmap"] = LinearSegmentedColormap.from_list(
                        name="custom",
                        colors=self._colors,
                        N=256
                    )
                else:
                    # Assume it's already a Colormap object
                    kwargs["cmap"] = self._colors

        return kwargs
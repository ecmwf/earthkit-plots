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


__all__ = [
    "Style",
    "CompositeStyle",
    "Contour",
    "Vector",
    "compute_levels",
    "get",
    "available",
    "match",
]

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
        legend_type: str = "auto",
        plot_type: Optional[str] = None,
        **kwargs,
    ):
        self._colors = colors
        self._levels = levels
        self._units = units
        self._units_label = units_label
        self.scale_factor = scale_factor
        self.anomaly = anomaly
        self._normalize = normalize
        self.legend_type = legend_type
        self.plot_type = plot_type  # Method name for quickplot (e.g., "contour", "pcolormesh")
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

    @classmethod
    def from_magics(cls, **magics_params):
        """
        Create a Style from Magics contouring parameters.

        This class method provides a convenient way to convert Magics plotting
        parameters to earthkit-plots Style objects.

        Parameters
        ----------
        **magics_params : dict
            Magics contouring parameters (see earthkit.plots.styles.magics.from_magics
            for full parameter documentation).

        Returns
        -------
        Style
            A Style object configured with the translated Magics parameters.

        Examples
        --------
        >>> # Convert Magics-style parameters
        >>> style = Style.from_magics(
        ...     contour_level_selection_type="interval",
        ...     contour_interval=2.0,
        ...     contour_shade="on",
        ...     contour_shade_palette_name="eccharts_rainbow_purple_red_25"
        ... )
        >>>
        >>> # Use in plotting
        >>> chart.contourf(data, style=style)

        See Also
        --------
        earthkit.plots.styles.magics.from_magics : Full documentation of Magics parameter translation
        """
        from earthkit.plots.styles.magics import from_magics
        return from_magics(**magics_params)

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
    
    def to_contourf_kwargs(self, data: np.ndarray) -> dict:
        """
        Convert the Style to matplotlib keyword arguments suitable for contourf.

        Parameters
        ----------
        data : np.ndarray
            The data array to be plotted, used to compute levels if needed.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib contourf.
        """
        return self.to_matplotlib_kwargs(data)
    
    def to_contour_kwargs(self, data: np.ndarray) -> dict:
        """
        Convert the Style to matplotlib keyword arguments suitable for contour.

        Parameters
        ----------
        data : np.ndarray
            The data array to be plotted, used to compute levels if needed.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib contour.
        """
        return self.to_matplotlib_kwargs(data)
    
    def to_pcolormesh_kwargs(self, data: np.ndarray) -> dict:
        """
        Convert the Style to matplotlib keyword arguments suitable for pcolormesh.

        Parameters
        ----------
        data : np.ndarray
            The data array to be plotted, used to compute levels if needed.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib pcolormesh.
        """
        # For pcolormesh with discrete levels, we need to use extend_levels=False
        # so that over/under colors are set via cmap.set_over/under instead of
        # including infinities in the BoundaryNorm (which causes colorbar issues)
        levels = self.levels(data)
        kwargs = self._kwargs.copy()

        if levels is not None:
            # Create colormap and normalization with extend_levels=False
            import earthkit.plots.styles.colors as ekp_colors
            cmap, norm = ekp_colors.cmap_and_norm(
                self._colors,
                levels,
                normalize=self._normalize,
                extend=kwargs.get("extend", None),
                extend_levels=False,  # Use set_over/set_under instead of inf boundaries
            )
            kwargs.update({"cmap": cmap, "norm": norm})
        else:
            # When no levels specified, just pass through the colormap/colors
            if self._colors is not None:
                if isinstance(self._colors, str):
                    # Named colormap
                    kwargs["cmap"] = self._colors
                elif isinstance(self._colors, list):
                    # List of colors - create a colormap from it
                    from matplotlib.colors import LinearSegmentedColormap
                    kwargs["cmap"] = LinearSegmentedColormap.from_list(
                        name="custom",
                        colors=self._colors,
                        N=256
                    )
                else:
                    # Assume it's already a Colormap object
                    kwargs["cmap"] = self._colors

        kwargs.pop("levels", None)  # pcolormesh does not use levels
        kwargs.pop("extend", None)  # extend is for colorbar, not pcolormesh
        kwargs.pop("extend_levels", None)  # internal parameter
        return kwargs
    
    def to_scatter_kwargs(self, data: np.ndarray) -> dict:
        """
        Convert the Style to matplotlib keyword arguments suitable for scatter.

        Parameters
        ----------
        data : np.ndarray
            The data array to be plotted, used to compute levels if needed.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib scatter.
        """
        # For scatter with discrete levels, we need to use extend_levels=False
        # so that over/under colors are set via cmap.set_over/under instead of
        # including infinities in the BoundaryNorm (which causes colorbar issues)
        levels = self.levels(data)
        kwargs = self._kwargs.copy()

        if levels is not None:
            # Create colormap and normalization with extend_levels=False
            import earthkit.plots.styles.colors as ekp_colors
            cmap, norm = ekp_colors.cmap_and_norm(
                self._colors,
                levels,
                normalize=self._normalize,
                extend=kwargs.get("extend", None),
                extend_levels=False,  # Use set_over/set_under instead of inf boundaries
            )
            kwargs.update({"cmap": cmap, "norm": norm})
        else:
            # When no levels specified, just pass through the colormap/colors
            if self._colors is not None:
                if isinstance(self._colors, str):
                    # Named colormap
                    kwargs["cmap"] = self._colors
                elif isinstance(self._colors, list):
                    # List of colors - create a colormap from it
                    from matplotlib.colors import LinearSegmentedColormap
                    kwargs["cmap"] = LinearSegmentedColormap.from_list(
                        name="custom",
                        colors=self._colors,
                        N=256
                    )
                else:
                    # Assume it's already a Colormap object
                    kwargs["cmap"] = self._colors

        kwargs.pop("levels", None)  # scatter does not use levels
        kwargs.pop("extend", None)  # extend is for colorbar, not scatter
        kwargs.pop("extend_levels", None)  # internal parameter
        return kwargs
    
    def to_grid_cells_kwargs(self, data: np.ndarray) -> dict:
        """
        Convert the Style to matplotlib keyword arguments suitable for grid_cells.

        Parameters
        ----------
        data : np.ndarray
            The data array to be plotted, used to compute levels if needed.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib grid_cells.
        """
        return self.to_pcolormesh_kwargs(data)

    def get_legend_key(self) -> tuple:
        """
        Get a hashable key representing this style's visual appearance for legend purposes.

        Used to determine if two layers should share the same legend/colorbar.
        Layers with the same legend_key will be grouped together.

        Returns
        -------
        tuple
            A hashable tuple containing the style characteristics that affect
            legend appearance: levels, colors, normalization, and extend settings.
        """
        # Convert levels to a hashable form
        if self._levels is None:
            levels_key = None
        elif isinstance(self._levels, dict):
            # For dynamic levels, use the parameters
            levels_key = tuple(sorted(self._levels.items()))
        elif isinstance(self._levels, (list, range)):
            # Convert list or range to tuple for consistent hashing
            levels_key = tuple(self._levels)
        else:
            # For other iterables or single values
            try:
                levels_key = tuple(self._levels)
            except TypeError:
                # Not iterable, use as-is
                levels_key = self._levels

        # Convert colors to a hashable form
        if self._colors is None:
            colors_key = None
        elif isinstance(self._colors, str):
            colors_key = self._colors
        elif isinstance(self._colors, list):
            colors_key = tuple(self._colors)
        else:
            # For colormap objects, use their name if available
            colors_key = getattr(self._colors, 'name', id(self._colors))

        # Get key kwargs that affect legend appearance
        extend = self._kwargs.get("extend", None)
        extend_levels = self._kwargs.get("extend_levels", True)

        return (levels_key, colors_key, self._normalize, extend, extend_levels)

    def legend(self, layer, ax=None, location='right', orientation=None,
               label="auto", **kwargs):
        """
        Create a legend for this style (colorbar for 2D plots, traditional legend for 1D plots).

        Parameters
        ----------
        layer : Layer
            The layer to create a legend for (provides mappable and data for labeling).
        ax : matplotlib.axes.Axes, optional
            The axes to attach the legend to. If None, uses layer.ax.
        location : str, optional
            Location for the colorbar ('right', 'left', 'top', 'bottom').
            Default is 'right'. For traditional legends, use standard matplotlib locations
            like 'upper right', 'lower left', etc.
        orientation : str, optional
            Orientation of the colorbar ('vertical' or 'horizontal').
            If None, inferred from location. Only applicable to colorbars.
        label : str, optional
            Label for the legend. Default is "auto" which generates a label from layer
            metadata. Can contain format placeholders (e.g., "{units}", "{long_name}", etc.)
            which will be replaced with layer metadata values. Use None for no label.
        **kwargs
            Additional keyword arguments passed to matplotlib's colorbar or legend.

        Returns
        -------
        matplotlib.colorbar.Colorbar or matplotlib.legend.Legend
            The created legend object.

        Examples
        --------
        >>> style.legend(layer, label="{long_name} ({units})")
        >>> style.legend(layer, label="{units}")
        """
        legend_type = self.legend_type
        if legend_type is None:
            return
        
        if legend_type == "auto":
            legend_type = self._infer_legend_type(layer)

        if legend_type == "colorbar":
            return self._create_colorbar(layer, ax, location, orientation, label, **kwargs)
        elif legend_type == "legend":
            return self._create_traditional_legend(layer, ax, location, label, **kwargs)
        else:
            raise ValueError(f"Unknown legend_type: {legend_type}")

    def _infer_legend_type(self, layer):
        """
        Infer the legend type based on style settings and layer data.

        Parameters
        ----------
        layer : Layer
            The layer to infer legend type for.

        Returns
        -------
        str
            Either "colorbar" or "legend".
        """
        if self.legend_type != "auto":
            # User explicitly specified legend type
            requested_type = self.legend_type

            # Validate compatibility
            if layer.dimension_set.z is None and requested_type == "colorbar":
                raise ValueError(
                    "Cannot create colorbar for 1D plot (no z dimension). "
                    "Use legend_type='legend' or 'auto' instead."
                )
            elif layer.dimension_set.z is not None and requested_type == "legend":
                raise ValueError(
                    "Cannot create traditional legend for 2D plot with z dimension. "
                    "Use legend_type='colorbar' or 'auto' instead."
                )

            return requested_type

        # Auto-inference based on z dimension
        if layer.dimension_set.z is None:
            return "legend"
        else:
            return "colorbar"

    def _create_colorbar(self, layer, ax, location, orientation, label, **kwargs):
        """Create a colorbar legend."""
        import matplotlib.pyplot as plt

        if ax is None:
            ax = layer.ax

        # Determine orientation from location if not specified
        if orientation is None:
            if location in ('right', 'left'):
                orientation = 'vertical'
            else:
                orientation = 'horizontal'

        # Get the mappable object (the plotted data with colormap)
        mappable = layer.mappable

        # Generate or format label
        if label == "auto":
            # Check if a label was set at plot time - if so, use it
            # Otherwise, generate a default label template
            if hasattr(layer, '_plot_label') and layer._plot_label and layer._plot_label != "_no_legend_":
                label = layer._plot_label
            else:
                # Generate a default label template
                label = self._generate_colorbar_label_template(layer)

        # Format the label using layer metadata (applies format_units, etc.)
        if label is not None and "{" in label:
            label = layer.format_string(label)

        # Set default parameters to make colorbar match axes size
        # Use fraction and aspect instead of shrink for better control
        if 'fraction' not in kwargs:
            kwargs['fraction'] = 0.046  # Standard matplotlib default
        if 'aspect' not in kwargs:
            # For vertical colorbars, aspect controls width relative to height
            # For horizontal, it controls height relative to width
            # Using 20 (matplotlib default) gives good proportions
            kwargs['aspect'] = 20
        if 'shrink' not in kwargs:
            # Shrink controls how much of the axes height/width to use
            kwargs['shrink'] = 1.0

        # Add extend parameter if it's in the style kwargs
        if 'extend' not in kwargs and 'extend' in self._kwargs:
            kwargs['extend'] = self._kwargs['extend']

        # Create colorbar
        # Use plt.colorbar for standard approach
        cbar = plt.colorbar(
            mappable,
            ax=ax,
            location=location,
            orientation=orientation,
            label=label,
            **kwargs
        )

        return cbar

    def _create_traditional_legend(self, layer, ax, location, label, **kwargs):
        """Create a traditional matplotlib legend for 1D plots."""
        import matplotlib.pyplot as plt

        if ax is None:
            ax = layer.ax

        # Generate or format label
        if label == "auto":
            # Check if a label was set at plot time - if so, use it
            # Otherwise, generate a default label from layer metadata
            if hasattr(layer, '_plot_label') and layer._plot_label and layer._plot_label != "_no_legend_":
                label = layer._plot_label
            else:
                # Generate a default label from layer metadata
                label = self._generate_legend_label(layer)

        # Format the label using layer metadata (applies format_units, etc.)
        if label is not None and "{" in label:
            label = layer.format_string(label)

        # Get the mappable object (line, scatter, etc.)
        mappable = layer.mappable

        # Add label to the mappable if not already set
        if hasattr(mappable, 'set_label'):
            mappable.set_label(label)

        # Create the legend
        # Use ax.legend() to collect all labeled artists on the axes
        legend = ax.legend(loc=location, **kwargs)

        return legend

    def _generate_legend_label(self, layer):
        """
        Generate a label for traditional legend from layer metadata.

        Parameters
        ----------
        layer : Layer
            The layer to generate a label for.

        Returns
        -------
        str or None
            The label string, or None if no label can be generated.
        """
        # For 1D plots, we want to show the variable name and units
        # Build a template with placeholders
        parts = []

        # Add variable name from y dimension (for line plots, y is typically the value)
        if layer.dimension_set.y is not None:
            var_name = layer.dimension_set.y.long_name or layer.dimension_set.y.name
            if var_name and var_name != "data":
                parts.append(var_name)

        # Check if we should include units
        # Priority: style units_label > style units > dimension units
        has_units = (
            self._units_label is not None
            or self._units is not None
            or (layer.dimension_set.y is not None and layer.dimension_set.y.units is not None)
        )

        if has_units:
            # Use {units} placeholder so LayerFormatter can apply format_units
            parts.append("({units})")

        return " ".join(parts) if parts else None

    def _generate_colorbar_label_template(self, layer):
        """
        Generate a label template for the colorbar that will be formatted by layer metadata.

        This creates a template string with placeholders (e.g., "{long_name} ({units})")
        that will be filled in by the LayerFormatter, which applies proper formatting
        rules like format_units.

        Parameters
        ----------
        layer : Layer
            The layer to generate a label template for.

        Returns
        -------
        str or None
            The label template with placeholders, or None if no label can be generated.
        """
        # Build a template with placeholders
        parts = []

        # Add variable name placeholder if we have a z dimension
        if layer.dimension_set.z is not None:
            var_name = layer.dimension_set.z.long_name or layer.dimension_set.z.name
            if var_name and var_name != "data":
                # Use the actual name directly (not a placeholder) since it's already known
                parts.append(var_name)

        # Check if we should include units
        # Priority: style units_label > style units > dimension units
        has_units = (
            self._units_label is not None
            or self._units is not None
            or (layer.dimension_set.z is not None and layer.dimension_set.z.units is not None)
        )

        if has_units:
            # Use {units} placeholder so LayerFormatter can apply format_units
            parts.append("({units})")

        return " ".join(parts) if parts else None


class Contour(Style):
    """Style subclass for contour plots."""
    pass


class Vector(Style):
    """Style subclass for vector plots (quiver, barbs)."""
    pass


class CompositeStyle:
    """
    A composite style that combines multiple styles for multi-layer plots.

    This is useful when quickplot needs to apply multiple styles to the same data.
    """

    def __init__(self, styles: List[Style]):
        self.styles = styles

    def __iter__(self):
        return iter(self.styles)


# ============================================================================
# Public API for style management
# ============================================================================

def get(style_name: str) -> Optional[Style]:
    """
    Get a named style by its identifier.

    Parameters
    ----------
    style_name : str
        The name of the style (e.g., "MEAN_SEA_LEVEL_PRESSURE_IN_HPA").

    Returns
    -------
    Style or None
        The requested style, or None if not found.

    Examples
    --------
    >>> from earthkit.plots import styles
    >>> style = styles.get("MEAN_SEA_LEVEL_PRESSURE_IN_HPA")
    >>> print(style.plot_type)
    contour
    """
    from earthkit.plots.styles.loader import get as loader_get
    return loader_get(style_name)


def available() -> List[str]:
    """
    Get a list of all available style names.

    Returns
    -------
    list of str
        Sorted list of all style names that can be used with styles.get().

    Examples
    --------
    >>> from earthkit.plots import styles
    >>> all_styles = styles.available()
    >>> print(f"Found {len(all_styles)} styles")
    >>> print(all_styles[:5])
    """
    from earthkit.plots.styles.loader import available as loader_available
    return loader_available()


def _extract_data_units(data) -> Optional[str]:
    """
    Extract units from data object.

    Parameters
    ----------
    data : object
        Data object to extract units from (DimensionSet, Field, DataArray, etc.)

    Returns
    -------
    str or None
        The units string if found, None otherwise.
    """
    # Check if it's a DimensionSet
    if hasattr(data, 'z') and data.z is not None and hasattr(data.z, 'units'):
        return data.z.units

    # Check for direct units attribute
    if hasattr(data, 'units') and data.units is not None:
        return data.units

    # Check for metadata access methods (earthkit-data)
    if hasattr(data, 'metadata'):
        try:
            units = data.metadata('units')
            if units is not None:
                return units
        except:
            pass

    # Check for attrs (xarray)
    if hasattr(data, 'attrs') and 'units' in data.attrs:
        return data.attrs['units']

    return None


def _units_compatible(data_units: str, style_units: str) -> bool:
    """
    Check if data units are compatible with style units.

    This performs a simple string comparison with some normalization.
    Future improvements could use pint or similar for more sophisticated
    unit conversion checking.

    Parameters
    ----------
    data_units : str
        Units from the data
    style_units : str
        Units from the style

    Returns
    -------
    bool
        True if units are considered compatible, False otherwise.
    """
    if data_units is None or style_units is None:
        return False

    # Normalize both strings for comparison
    data_units_norm = data_units.strip().lower()
    style_units_norm = style_units.strip().lower()

    # Direct match
    if data_units_norm == style_units_norm:
        return True

    # Common equivalences
    equivalences = [
        {'m3 s-1', 'm^3 s^-1', 'm**3 s**-1', 'm³ s⁻¹', 'm3/s'},
        {'k', 'kelvin'},
        {'c', 'celsius', 'degc', '°c'},
        {'pa', 'pascal'},
        {'hpa', 'hectopascal'},
        {'m', 'meter', 'metre'},
        {'kg', 'kilogram'},
        {'s', 'second'},
    ]

    for equiv_set in equivalences:
        if data_units_norm in equiv_set and style_units_norm in equiv_set:
            return True

    return False


def match(data, units: Optional[str] = None) -> List[str]:
    """
    Find and return all style names that match the given data.

    This function analyzes the data's metadata (paramId, shortName, standard_name, etc.)
    to identify the variable type, then returns all styles (not just optimal ones)
    for matching variables.

    Parameters
    ----------
    data : object
        Data object with metadata (earthkit-data Field, xarray DataArray, etc.)
    units : str, optional
        If provided, only return styles that match these units or have no units defined.
        This allows filtering styles when the user explicitly specifies units.

    Returns
    -------
    list of str
        List of style names that match this data based on metadata matching,
        or empty list if no matching styles are found. Optimal styles are placed
        first in the list, followed by other matching styles. The first style in
        the list is used as the default when style="auto".

    Examples
    --------
    >>> from earthkit.plots import styles
    >>> import earthkit.data as ekd
    >>> data = ekd.from_source("file", "river_discharge.grib")
    >>> style_names = styles.match(data)
    >>> print(style_names)
    ['RIVER_DISCHARGE_GLOBAL_IN_M3_S-1', 'RIVER_DISCHARGE_EUROPE_IN_M3_S-1']
    >>> # Use the first one (optimal) as default
    >>> style = styles.get(style_names[0])
    >>> # Filter by units
    >>> style_names = styles.match(data, units="m3 s-1")
    >>> print(style_names)
    ['RIVER_DISCHARGE_GLOBAL_IN_M3_S-1', 'RIVER_DISCHARGE_EUROPE_IN_M3_S-1']
    """
    from earthkit.plots.styles.matcher import match as matcher_match
    from earthkit.plots.schemas import schema
    identity_ids = matcher_match(data)

    if not identity_ids:
        return []

    # Get ALL styles for each matching identity
    from earthkit.plots.styles.loader import _style_library
    _style_library._load_all_styles()

    # Extract data units for matching
    data_units = _extract_data_units(data)
    use_preferred_units = schema.get("use_preferred_units")

    matched_styles = []
    optimal_styles = []
    unit_matched_optimal = []
    unit_matched_other = []

    for identity_id in identity_ids:
        # Find all styles that match this identity
        for style_name, style in _style_library._styles_cache.items():
            if hasattr(style, "_file_id") and style._file_id == identity_id:
                # If user specified units, filter styles
                if units is not None:
                    style_has_units = hasattr(style, "_units") and style._units is not None
                    # Only include styles that match the requested units or have no units
                    if style_has_units and not _units_compatible(units, style._units):
                        continue  # Skip this style

                is_optimal = hasattr(style, "_is_optimal") and style._is_optimal
                units_match = (data_units and hasattr(style, "_units") and
                              _units_compatible(data_units, style._units))

                # Categorize by optimal status and unit matching
                if is_optimal and units_match:
                    unit_matched_optimal.append(style_name)
                elif is_optimal:
                    optimal_styles.append(style_name)
                elif units_match:
                    unit_matched_other.append(style_name)
                else:
                    matched_styles.append(style_name)

    # Return styles in priority order based on use_preferred_units setting
    if use_preferred_units:
        # When use_preferred_units=True, prioritize optimal regardless of units
        return optimal_styles + unit_matched_optimal + matched_styles + unit_matched_other
    else:
        # When use_preferred_units=False, prioritize unit matches
        return unit_matched_optimal + unit_matched_other + optimal_styles + matched_styles
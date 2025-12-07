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
Translator for converting Magics plotting styles to earthkit-plots styles.

This module provides utilities to convert Magics parameter dictionaries
(commonly used in ECMWF's Magics plotting library) into earthkit-plots
Style objects.
"""

from typing import Optional, Dict, Any, Union, List
import warnings


# Magics named color to RGB mapping
# Based on Magics C++ color definitions
MAGICS_COLORS = {
    "automatic": (0.0, 0.0, 0.0),
    "none": None,  # Special case - transparent/no color
    "background": (1.0, 1.0, 1.0),
    "foreground": (0.0, 0.0, 0.0),
    "ecmwf_blue": (0.25, 0.43, 0.7),
    "red": (1.0, 0.0, 0.0),
    "green": (0.0, 1.0, 0.0),
    "blue": (0.0, 0.0, 1.0),
    "yellow": (1.0, 1.0, 0.0),
    "cyan": (0.0, 1.0, 1.0),
    "magenta": (1.0, 0.0, 1.0),
    "black": (0.0, 0.0, 0.0),
    "avocado": (0.4225, 0.6500, 0.1950),
    "beige": (0.8500, 0.7178, 0.4675),
    "brick": (0.6000, 0.0844, 0.0300),
    "brown": (0.4078, 0.0643, 0.0),
    "burgundy": (0.5000, 0.0, 0.1727),
    "charcoal": (0.2000, 0.2000, 0.2000),
    "chestnut": (0.3200, 0.0112, 0.0),
    "coral": (0.9000, 0.2895, 0.2250),
    "cream": (1.0, 0.8860, 0.6700),
    "evergreen": (0.0, 0.4500, 0.2945),
    "gold": (0.7500, 0.5751, 0.0750),
    "grey": (0.7000, 0.7000, 0.7000),
    "khaki": (0.5800, 0.4798, 0.2900),
    "kelly_green": (0.0, 0.5500, 0.1900),
    "lavender": (0.6170, 0.4070, 0.9400),
    "mustard": (0.6000, 0.3927, 0.0),
    "navy": (0.0, 0.0, 0.4000),
    "ochre": (0.6800, 0.4501, 0.0680),
    "olive": (0.3012, 0.3765, 0.0),
    "peach": (0.9400, 0.4739, 0.3788),
    "pink": (0.9000, 0.3600, 0.4116),
    "rose": (0.8000, 0.2400, 0.4335),
    "rust": (0.7000, 0.2010, 0.0),
    "sky": (0.4500, 0.6400, 1.0),
    "tan": (0.4000, 0.3309, 0.2000),
    "tangerine": (0.8784, 0.4226, 0.0),
    "turquoise": (0.1111, 0.7216, 0.6503),
    "violet": (0.4823, 0.0700, 0.7000),
    "reddish_purple": (1.0, 0.0, 0.8536),
    "purple_red": (1.0, 0.0, 0.5000),
    "purplish_red": (1.0, 0.0, 0.2730),
    "orangish_red": (1.0, 0.0381, 0.0),
    "red_orange": (1.0, 0.1464, 0.0),
    "reddish_orange": (1.0, 0.3087, 0.0),
    "orange": (1.0, 0.5000, 0.0),
    "yellowish_orange": (1.0, 0.6913, 0.0),
    "orange_yellow": (1.0, 0.8536, 0.0),
    "orangish_yellow": (1.0, 0.9619, 0.0),
    "greenish_yellow": (0.8536, 1.0, 0.0),
    "yellow_green": (0.5000, 1.0, 0.0),
    "yellowish_green": (0.1464, 1.0, 0.0),
    "bluish_green": (0.0, 1.0, 0.5000),
    "blue_green": (0.0, 1.0, 1.0),
    "greenish_blue": (0.0, 0.5000, 1.0),
    "purplish_blue": (0.1464, 0.0, 1.0),
    "blue_purple": (0.5000, 0.0, 1.0),
    "bluish_purple": (0.8536, 0.0, 1.0),
    "purple": (1.0, 0.0, 1.0),
    "white": (1.0, 1.0, 1.0),
    "undefined": None,  # Special case - undefined color
}


# Magics palette name to matplotlib colormap mapping
MAGICS_PALETTE_TO_MPL = {
    # ECMWF palettes
    "eccharts_rainbow_purple_red_25": "turbo",
    "eccharts_rainbow_blue_purple_25": "viridis",
    "eccharts_rainbow_blue_red_25": "RdBu_r",

    # Standard palettes
    "rainbow": "rainbow",
    "grey": "Greys",
    "blue": "Blues",
    "red": "Reds",
    "green": "Greens",
    "blue_red": "RdBu_r",
    "red_blue": "RdBu",

    # Add more mappings as needed
}


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple:
    """
    Convert HSL color to RGB.

    Parameters
    ----------
    h : float
        Hue in degrees [0, 360]
    s : float
        Saturation [0, 1]
    l : float
        Lightness [0, 1]

    Returns
    -------
    tuple
        RGB tuple (r, g, b) with values in range [0, 1]
    """
    # Normalize hue to [0, 1]
    h = h / 360.0

    # Convert HSL to RGB using standard algorithm
    if s == 0:
        # Achromatic (gray)
        return (l, l, l)

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return (r, g, b)


def magics_color(color_name: str) -> Optional[Union[str, tuple]]:
    """
    Convert a Magics named color to matplotlib-compatible RGB or color name.

    Parameters
    ----------
    color_name : str
        Magics color name (e.g., "ecmwf_blue", "charcoal", "red").
        Also supports RGB and HSL formats:
        - "rgb(r,g,b)" where values are in [0, 1]
        - "hsl(h,s,l)" where h is in degrees [0, 360] and s,l are in [0, 1]

    Returns
    -------
    tuple or str or None
        - RGB tuple (r, g, b) with values in range [0, 1] for Magics-specific colors
        - Color name string for standard colors that matplotlib recognizes
        - None for "none" or "undefined" (transparent/no color)

    Examples
    --------
    >>> from earthkit.plots.styles import magics
    >>>
    >>> # ECMWF specific color
    >>> magics.magics_color("ecmwf_blue")
    (0.25, 0.43, 0.7)
    >>>
    >>> # Standard color (returned as string for matplotlib)
    >>> magics.magics_color("red")
    'red'
    >>>
    >>> # Magics-specific named color
    >>> magics.magics_color("charcoal")
    (0.2, 0.2, 0.2)
    >>>
    >>> # RGB format
    >>> magics.magics_color("rgb(0.3,0.3,0.3)")
    (0.3, 0.3, 0.3)
    >>>
    >>> # HSL format
    >>> magics.magics_color("hsl(29,0.12,0.92)")
    (0.9312, 0.9088, 0.8864)
    >>>
    >>> # No color / transparent
    >>> magics.magics_color("none")
    None

    Notes
    -----
    Standard color names (red, green, blue, yellow, cyan, magenta, black, white,
    grey) are returned as strings since matplotlib already recognizes them.
    Magics-specific colors are returned as RGB tuples.
    """
    if not isinstance(color_name, str):
        # If it's already a tuple/list (RGB), return as-is
        return color_name

    elif color_name.upper().startswith("RGB("):
        # Handle explicit RGB format "rgb(r,g,b)"
        rgb_values = color_name[4:-1].split(",")
        try:
            r, g, b = [float(v.strip()) for v in rgb_values]
            return (r, g, b)
        except (ValueError, IndexError):
            # Invalid RGB format - return None
            return None

    elif color_name.upper().startswith("HSL("):
        # Handle HSL format "hsl(h,s,l)" or "HSL(h,s,l)"
        hsl_values = color_name[4:-1].split(",")
        try:
            h, s, l = [float(v.strip()) for v in hsl_values]
            return _hsl_to_rgb(h, s, l)
        except (ValueError, IndexError):
            # Invalid HSL format - return None
            return None

    color_lower = color_name.lower()

    # Check if it's a Magics named color
    if color_lower in MAGICS_COLORS:
        rgb = MAGICS_COLORS[color_lower]
        if rgb is None:
            return None

        # For standard color names, return as string (matplotlib recognizes them)
        standard_colors = {"red", "green", "blue", "yellow", "cyan", "magenta",
                          "black", "white", "grey"}
        if color_lower in standard_colors:
            return color_lower

        # For Magics-specific colors, return RGB tuple
        return rgb

    # Not a Magics color - return as-is (might be matplotlib color name or hex)
    return color_name


def from_magics(**magics_params) -> "Style":
    """
    Convert Magics contouring parameters to an earthkit-plots Style object.

    This function translates parameter dictionaries from ECMWF's Magics plotting
    library into earthkit-plots Style objects, enabling reuse of existing Magics
    configurations.

    Parameters
    ----------
    **magics_params : dict
        Magics contouring parameters. Common parameters include:

        Level Selection:
            - contour_level_selection_type: "interval" or "level_list"
            - contour_interval: Spacing between contour lines (float)
            - contour_level_list: Explicit list of contour levels
            - contour_min_level: Minimum contour level
            - contour_max_level: Maximum contour level
            - contour_reference_level: Reference level for interval calculation

        Shading:
            - contour_shade: Enable shading ("on"/"off")
            - contour_shade_method: "area_fill" or other methods
            - contour_shade_colour_method: "palette" or "gradients"
            - contour_shade_palette_name: Name of color palette
            - contour_shade_min_level: Minimum level for shading
            - contour_shade_max_level: Maximum level for shading
            - contour_shade_min_level_colour: Color for below minimum
            - contour_shade_max_level_colour: Color for above maximum

        Colors:
            - contour_gradients_colour_list: List of colors for gradients
            - contour_gradients_step_list: Steps for gradient distribution
            - contour_line_colour: Color for contour lines
            - contour_line_colour_rainbow: Apply rainbow colors to lines

        Line Properties:
            - contour: Enable contour lines ("on"/"off")
            - contour_line_thickness: Line width
            - contour_line_style: "solid", "dash", etc.
            - contour_highlight: Highlight specific contours
            - contour_highlight_frequency: Frequency of highlighted contours
            - contour_highlight_thickness: Thickness of highlighted contours

        Labels:
            - contour_label: Enable labels ("on"/"off")
            - contour_label_height: Label text size
            - contour_label_colour: Label color
            - contour_label_frequency: Label spacing

        Legend:
            - legend: Enable legend ("on"/"off")

    Returns
    -------
    Style
        An earthkit-plots Style object configured with the translated parameters.

    Examples
    --------
    >>> from earthkit.plots.styles import magics
    >>>
    >>> # Simple interval-based contouring
    >>> style = magics.from_magics(
    ...     contour_level_selection_type="interval",
    ...     contour_interval=2.0,
    ...     contour_shade="on",
    ...     contour_shade_colour_method="palette",
    ...     contour_shade_palette_name="eccharts_rainbow_purple_red_25"
    ... )
    >>>
    >>> # Explicit level list with gradient colors
    >>> style = magics.from_magics(
    ...     contour_level_selection_type="level_list",
    ...     contour_level_list=[-15, -10, -5, 0, 5, 10, 15],
    ...     contour_shade="on",
    ...     contour_shade_colour_method="gradients",
    ...     contour_gradients_colour_list=['blue', 'white', 'red'],
    ...     contour_gradients_step_list=[50, 1, 50]
    ... )

    Notes
    -----
    - Magics "on"/"off" strings are converted to True/False
    - Palette names are mapped to matplotlib colormaps where possible
    - Some advanced Magics features may not have direct equivalents
    """
    from earthkit.plots.styles import Style

    # Initialize earthkit-plots parameters
    ek_params = {}

    # =========================================================================
    # Determine plot type (contour vs contourf)
    # =========================================================================

    contour_enabled = _magics_bool(magics_params.get("contour", "on"))
    shade_enabled = _magics_bool(magics_params.get("contour_shade", "off"))

    if shade_enabled:
        ek_params["plot_type"] = "contourf"
    elif contour_enabled:
        ek_params["plot_type"] = "contour"
    else:
        ek_params["plot_type"] = None

    # =========================================================================
    # Process contour levels
    # =========================================================================

    levels = _convert_levels(magics_params)
    if levels is not None:
        ek_params["levels"] = levels

    # =========================================================================
    # Process colors and colormaps
    # =========================================================================

    colors = _convert_colors(magics_params, shade_enabled)
    if colors is not None:
        ek_params["colors"] = colors

    # =========================================================================
    # Process extend parameter
    # =========================================================================

    extend = _convert_extend(magics_params)
    if extend is not None:
        ek_params["extend"] = extend

    # =========================================================================
    # Process line properties (for contour lines)
    # =========================================================================

    line_props = _convert_line_properties(magics_params)
    ek_params.update(line_props)

    # =========================================================================
    # Process labels
    # =========================================================================

    label_enabled = _magics_bool(magics_params.get("contour_label", "off"))
    if label_enabled:
        ek_params["labels"] = True

    # =========================================================================
    # Process legend
    # =========================================================================

    legend_enabled = _magics_bool(magics_params.get("legend", "on"))
    if not legend_enabled:
        ek_params["legend_type"] = None

    # =========================================================================
    # Create and return Style
    # =========================================================================

    return Style(**ek_params)


def _magics_bool(value: Union[str, bool]) -> bool:
    """Convert Magics on/off strings to Python booleans."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("on", "true", "yes", "1")
    return bool(value)


def _convert_levels(magics_params: Dict[str, Any]) -> Optional[Union[List[float], Dict[str, Any]]]:
    """
    Convert Magics level parameters to earthkit-plots levels.

    Handles both explicit level lists and interval-based level generation.
    """
    import numpy as np
    level_selection_type = magics_params.get("contour_level_selection_type", "interval")

    if level_selection_type == "level_list":
        # Explicit level list
        level_list = magics_params.get("contour_level_list")
        if level_list is not None:
            if isinstance(level_list, str):
                return [float(level) for level in level_list.split("/")]
            return list(level_list)

    elif level_selection_type == "interval":
        # Interval-based levels - use dict format for dynamic computation
        interval = magics_params.get("contour_interval")
        reference = magics_params.get("contour_reference_level")
        min_level = magics_params.get("contour_shade_min_level")
        max_level = magics_params.get("contour_shade_max_level")

        if interval is not None:
            if min_level is not None and max_level is not None:
                return np.arange(min_level, max_level + interval, interval).tolist()
            
            # Use earthkit's dict-based level computation
            levels_dict = {"step": interval}

            if reference is not None:
                levels_dict["reference"] = reference

            # Note: min/max levels in Magics are more about filtering than generation
            # They would need to be applied during level computation
            if min_level is not None or max_level is not None:
                warnings.warn(
                    "Magics min_level/max_level parameters are not directly supported. "
                    "Consider using explicit level_list instead."
                )

            return levels_dict

    return None


def _load_magics_palettes():
    """
    Load the Magics palettes from the JSON data file.

    Returns
    -------
    dict
        Dictionary mapping palette names to palette data (colors and metadata).
    """
    import json
    from pathlib import Path

    # Get the path to the data file (in repository root data/colors/)
    # Walk up from src/earthkit/plots/styles/magics.py to repository root
    # __file__ is at: src/earthkit/plots/styles/magics.py
    # Need to go up 5 levels: styles -> plots -> earthkit -> src -> repo_root
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    palette_file = repo_root / "data" / "colors" / "palettes.json"

    if not palette_file.exists():
        warnings.warn(
            f"Magics palettes file not found: {palette_file}. "
            "Palette name lookups will fall back to matplotlib colormap names."
        )
        return {}

    try:
        with open(palette_file) as f:
            return json.load(f)
    except Exception as e:
        warnings.warn(f"Failed to load Magics palettes: {e}")
        return {}


# Cache the palettes on first load
_MAGICS_PALETTES_CACHE = None


def _get_magics_palettes():
    """Get Magics palettes, loading them if not already cached."""
    global _MAGICS_PALETTES_CACHE
    if _MAGICS_PALETTES_CACHE is None:
        _MAGICS_PALETTES_CACHE = _load_magics_palettes()
    return _MAGICS_PALETTES_CACHE


def _convert_colors(magics_params: Dict[str, Any], shade_enabled: bool) -> Optional[Union[str, List[str]]]:
    """
    Convert Magics color parameters to earthkit-plots colors.

    Handles palettes, gradients, and rainbow line coloring.
    """
    if shade_enabled:
        # Shaded contours - get colormap
        colour_method = magics_params.get("contour_shade_colour_method", "palette")

        if colour_method == "palette":
            # Use a named palette
            palette_name = magics_params.get("contour_shade_palette_name")
            if palette_name:
                # First, check if it's in our Magics palettes JSON
                palettes = _get_magics_palettes()
                if palette_name in palettes:
                    # Return the color list from the palette
                    return palettes[palette_name]["colors"]

                # Fall back to matplotlib colormap name mapping
                mpl_cmap = MAGICS_PALETTE_TO_MPL.get(palette_name, palette_name)
                return mpl_cmap

        elif colour_method == "gradients":
            # Use gradient colors
            colour_list = magics_params.get("contour_gradients_colour_list")
            if colour_list:
                return [magics_color(c) for c in colour_list]

        elif colour_method == "list":
            # Direct color list (less common)
            colour_list = magics_params.get("contour_shade_colour_list")
            if isinstance(colour_list, str):
                colour_list = colour_list.split("/")
            if colour_list:
                return [magics_color(c) for c in colour_list]

    else:
        # Contour lines - get line color
        if _magics_bool(magics_params.get("contour_line_colour_rainbow", "off")):
            # Rainbow coloring - use a colormap
            return "rainbow"

        line_colour = magics_params.get("contour_line_colour")
        if line_colour:
            return line_colour

    return None


def _convert_extend(magics_params: Dict[str, Any]) -> Optional[str]:
    """
    Determine the extend parameter from Magics shading parameters.

    Checks if min/max level colors are defined to infer extend behavior.
    """
    has_min_colour = "contour_shade_min_level_colour" in magics_params
    has_max_colour = "contour_shade_max_level_colour" in magics_params

    if has_min_colour and has_max_colour:
        return "both"
    elif has_max_colour:
        return "max"
    elif has_min_colour:
        return "min"

    return None


def _convert_line_properties(magics_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Magics line properties to matplotlib kwargs.

    Handles line thickness, style, and highlight settings.
    """
    props = {}

    # Line thickness
    thickness = magics_params.get("contour_line_thickness")
    if thickness is not None:
        props["linewidths"] = thickness

    # Line style
    line_style = magics_params.get("contour_line_style", "solid")
    if line_style and line_style != "solid":
        # Map Magics styles to matplotlib
        style_map = {
            "dash": "dashed",
            "dot": "dotted",
            "chain_dash": "dashdot",
        }
        props["linestyles"] = style_map.get(line_style, line_style)

    # Highlight contours (use variable linewidths)
    if _magics_bool(magics_params.get("contour_highlight", "off")):
        highlight_freq = magics_params.get("contour_highlight_frequency", 5)
        highlight_thickness = magics_params.get("contour_highlight_thickness", 3)
        base_thickness = thickness or 1

        # Create pattern: [thin, thin, thin, ..., thick]
        widths = [base_thickness] * (highlight_freq - 1) + [highlight_thickness]
        props["linewidths"] = widths

    return props

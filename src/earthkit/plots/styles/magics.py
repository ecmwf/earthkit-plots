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
Style objects, and to batch-generate earthkit-plots YAML style files from
the Magics ECMWF styles directory.
"""

import warnings
from typing import Any, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Magics named color to RGB mapping (values in [0, 1])
# Based on Magics C++ color definitions
# ---------------------------------------------------------------------------

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
    "charcol": (0.2000, 0.2000, 0.2000),
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


# ---------------------------------------------------------------------------
# Magics palette name → matplotlib colormap mapping
# ---------------------------------------------------------------------------

MAGICS_PALETTE_TO_MPL = {
    # ECMWF palettes
    "eccharts_rainbow_purple_red_25": "turbo",
    "eccharts_rainbow_blue_purple_25": "viridis",
    "eccharts_rainbow_blue_red_25": "RdBu_r",
    "eccharts_white_red_7": "Reds",
    # Standard palettes
    "rainbow": "rainbow",
    "grey": "Greys",
    "blue": "Blues",
    "red": "Reds",
    "green": "Greens",
    "blue_red": "RdBu_r",
    "red_blue": "RdBu",
}


# ---------------------------------------------------------------------------
# Magics prefered_units → earthkit-plots / pint unit string mapping
# ---------------------------------------------------------------------------

MAGICS_UNITS_TO_EK = {
    "C": "celsius",
    "K": "K",
    "F": "fahrenheit",
    "hPa": "hPa",
    "Pa": "Pa",
    "m": "m",
    "mm": "mm",
    "cm": "cm",
    "dam": "dam",
    "km": "km",
    "m/s": "m s-1",
    "m s-1": "m s-1",
    "kg/m2": "kg m-2",
    "kg m-2": "kg m-2",
    "kg m**-2 h**-1": "kg m-2 h-1",
    "J/kg": "J kg-1",
    "m3/s": "m3 s-1",
    "%": "percent",
    "g/kg": "g kg-1",
    "pv units": "PVU",
    "ppbv": "ppbv",
    "Dob": "DU",  # Dobson units
    "10**5/sec": "1e5 s-1",
}


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

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
        RGB tuple with values in [0, 1]
    """
    h = h / 360.0
    if s == 0:
        return (l, l, l)

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return (
        hue_to_rgb(p, q, h + 1 / 3),
        hue_to_rgb(p, q, h),
        hue_to_rgb(p, q, h - 1 / 3),
    )


def magics_color(color_name: str) -> Optional[Union[str, tuple]]:
    """
    Convert a Magics color specification to a matplotlib-compatible value.

    Parameters
    ----------
    color_name : str
        Magics color name or format string. Supported formats:

        - Named Magics colors: ``"ecmwf_blue"``, ``"charcoal"``, ``"red"``, etc.
        - ``"rgb(r,g,b)"`` — integer values 0–255
        - ``"rgba(r,g,b,a)"`` — r/g/b are 0–255 integers, a is 0–1 float
        - ``"hsl(h,s,l)"`` — h in degrees [0, 360], s and l in [0, 1]
        - Any string matplotlib already understands (hex, CSS names, etc.)

    Returns
    -------
    tuple or str or None
        RGB(A) tuple with values in [0, 1], a color name string, or None for
        transparent/undefined colors.

    Examples
    --------
    >>> magics_color("ecmwf_blue")
    (0.25, 0.43, 0.7)
    >>> magics_color("rgb(128,0,255)")
    (0.5019..., 0.0, 1.0)
    >>> magics_color("rgba(255,0,0,0.5)")
    (1.0, 0.0, 0.0, 0.5)
    >>> magics_color("hsl(29,0.12,0.92)")
    (0.9312..., 0.9088..., 0.8864...)
    >>> magics_color("none")
    None
    """
    if not isinstance(color_name, str):
        return color_name

    upper = color_name.upper()

    if upper.startswith("RGBA("):
        parts = color_name[5:-1].split(",")
        try:
            r, g, b, a = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
            # Normalise r/g/b: if any channel > 1 they are 0-255 integers
            if r > 1.0 or g > 1.0 or b > 1.0:
                r, g, b = r / 255.0, g / 255.0, b / 255.0
            return (r, g, b, a)
        except (ValueError, IndexError):
            return None

    elif upper.startswith("RGB("):
        parts = color_name[4:-1].split(",")
        try:
            vals = [float(p) for p in parts]
            if len(vals) == 4:
                # Some Magics rgb() calls carry a 4th alpha channel
                r, g, b, a = vals
                if r > 1.0 or g > 1.0 or b > 1.0:
                    r, g, b = r / 255.0, g / 255.0, b / 255.0
                return (r, g, b, a)
            r, g, b = vals[0], vals[1], vals[2]
            # Normalise: if any channel > 1 they are 0-255 integers
            if r > 1.0 or g > 1.0 or b > 1.0:
                r, g, b = r / 255.0, g / 255.0, b / 255.0
            return (r, g, b)
        except (ValueError, IndexError):
            return None

    elif upper.startswith("HSL("):
        parts = color_name[4:-1].split(",")
        try:
            h, s, l = float(parts[0]), float(parts[1]), float(parts[2])
            return _hsl_to_rgb(h, s, l)
        except (ValueError, IndexError):
            return None

    color_lower = color_name.lower()
    if color_lower in MAGICS_COLORS:
        rgb = MAGICS_COLORS[color_lower]
        if rgb is None:
            return None
        # Return standard names as strings so matplotlib uses them directly
        standard_colors = {"red", "green", "blue", "yellow", "cyan", "magenta",
                           "black", "white", "grey"}
        if color_lower in standard_colors:
            return color_lower
        return rgb

    # Pass through as-is (hex strings, other matplotlib names, etc.)
    return color_name


def parse_colour_list(colour_list_str: str) -> List:
    """
    Parse a Magics ``/``-separated colour list string into a list of colours.

    Each element is resolved through :func:`magics_color`, so named Magics
    colours, ``rgb()``, ``rgba()``, and ``hsl()`` strings are all handled.

    Parameters
    ----------
    colour_list_str : str
        A ``/``-separated string of Magics colour specifications, e.g.
        ``"rgb(0,0,128)/blue_purple/greenish_blue/white/red"``.

    Returns
    -------
    list
        List of matplotlib-compatible colour values (RGB tuples, strings, etc.).
    """
    return [magics_color(c.strip()) for c in colour_list_str.split("/")]


def to_hex(color) -> str:
    """
    Convert any matplotlib-compatible colour to a hex string.

    Transparent (``None``) is returned as ``"#00000000"``.

    Parameters
    ----------
    color : tuple, str, or None
        A colour value as returned by :func:`magics_color`.

    Returns
    -------
    str
        Hex colour string, e.g. ``"#ff8000"`` or ``"#ff000080"``.
    """
    import matplotlib.colors as mcolors

    if color is None:
        return "#00000000"
    try:
        return mcolors.to_hex(color, keep_alpha=True)
    except (ValueError, TypeError):
        return "#000000ff"


# ---------------------------------------------------------------------------
# Internal conversion helpers
# ---------------------------------------------------------------------------

def _magics_bool(value: Union[str, bool]) -> bool:
    """Convert Magics on/off strings to Python booleans."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("on", "true", "yes", "1")
    return bool(value)


def _convert_levels(
    magics_params: Dict[str, Any],
) -> Optional[Union[List[float], Dict[str, Any]]]:
    """
    Convert Magics level parameters to earthkit-plots levels.

    Handles both explicit level lists and interval-based level generation.
    For interval styles, both the shade-specific bounds
    (``contour_shade_min/max_level``) and the general contour bounds
    (``contour_min/max_level``) are checked.
    """
    import numpy as np

    level_selection_type = magics_params.get("contour_level_selection_type", "interval")

    if level_selection_type in ("level_list", "list"):
        level_list = magics_params.get("contour_level_list")
        if level_list is not None:
            if isinstance(level_list, str):
                result = []
                for token in level_list.split("/"):
                    token = token.strip()
                    try:
                        result.append(float(token))
                    except ValueError:
                        pass  # skip "none" and other non-numeric tokens
                return result if result else None
            return list(level_list)

    elif level_selection_type == "interval":
        interval = magics_params.get("contour_interval")
        reference = magics_params.get("contour_reference_level")

        # Check shade-specific bounds first, fall back to general contour bounds
        min_level = magics_params.get("contour_shade_min_level",
                                      magics_params.get("contour_min_level"))
        max_level = magics_params.get("contour_shade_max_level",
                                      magics_params.get("contour_max_level"))

        if interval is not None:
            interval = float(interval)
            if min_level is not None and max_level is not None:
                # Generate explicit list so the YAML is fully self-contained
                levels = np.arange(float(min_level),
                                   float(max_level) + interval,
                                   interval).tolist()
                # Trim any overshoot caused by floating-point arange
                levels = [lv for lv in levels if lv <= float(max_level) + interval * 0.01]
                return levels

            # No bounds — use a dynamic step-based Levels config
            levels_dict: Dict[str, Any] = {"step": interval}
            if reference is not None:
                levels_dict["reference"] = float(reference)
            return levels_dict

    return None


def _convert_extend(
    magics_params: Dict[str, Any],
    shade_enabled: bool = True,
    colour_method: Optional[str] = None,
) -> str:
    """
    Infer the ``extend`` parameter from Magics shading parameters.

    Priority:
    1. Explicit min/max level colour keys → "both" / "min" / "max"
       (skipped for ``calculate`` method where these keys define gradient endpoints)
    2. Presence of min/max level bounds → same logic
    3. Shaded style with no bounds → default to "both" (Magics implicitly extends)
    4. Contour-only style → "neither"
    """
    # For ``calculate`` styles, min/max level colour keys define the colour
    # gradient endpoints, not extend arrows — don't treat them as extend indicators.
    if colour_method != "calculate":
        has_min_colour = "contour_shade_min_level_colour" in magics_params
        has_max_colour = "contour_shade_max_level_colour" in magics_params

        if has_min_colour or has_max_colour:
            if has_min_colour and has_max_colour:
                return "both"
            return "min" if has_min_colour else "max"

    if not shade_enabled:
        return "neither"

    # For ``calculate`` styles the gradient is bounded between the explicit
    # min/max level colours — there are no open-ended extensions.
    if colour_method == "calculate":
        return "neither"

    has_min = (
        "contour_shade_min_level" in magics_params
        or "contour_min_level" in magics_params
    )
    has_max = (
        "contour_shade_max_level" in magics_params
        or "contour_max_level" in magics_params
    )

    if has_min and has_max:
        return "both"
    if has_min:
        return "min"
    if has_max:
        return "max"

    # Shaded with no explicit bounds — Magics extends implicitly
    return "both"


def _calculate_colours(magics_params: Dict[str, Any], n: int = 256) -> List[str]:
    """
    Replicate Magics' ``contour_shade_colour_method='calculate'`` algorithm.

    Magics converts the min and max colours to HSL, then linearly interpolates
    hue, saturation, and lightness across ``n`` steps.  The direction parameter
    controls which way round the hue wheel the interpolation travels:

    - ``"anti_clockwise"`` (default): hue increases (e.g. red→green→blue)
    - ``"clockwise"``: hue decreases (e.g. red→magenta→blue)

    Returns a list of hex colour strings suitable for use as an earthkit-plots
    ``colors`` value.
    """
    import colorsys

    min_colour = magics_params.get("contour_shade_min_level_colour", "red")
    max_colour = magics_params.get("contour_shade_max_level_colour", "blue")
    direction = magics_params.get("contour_shade_colour_direction", "anti_clockwise")

    # Convert named/rgb colours to RGB floats then to HLS (colorsys uses HLS not HSL)
    min_rgb = magics_color(min_colour) if isinstance(min_colour, str) else min_colour
    max_rgb = magics_color(max_colour) if isinstance(max_colour, str) else max_colour

    # magics_color may return a named string; resolve to RGB tuple
    import matplotlib.colors as mcolors
    if isinstance(min_rgb, str):
        min_rgb = mcolors.to_rgb(min_rgb)
    if isinstance(max_rgb, str):
        max_rgb = mcolors.to_rgb(max_rgb)

    # colorsys.rgb_to_hls returns (h, l, s) — note the order
    min_h, min_l, min_s = colorsys.rgb_to_hls(*min_rgb[:3])
    max_h, max_l, max_s = colorsys.rgb_to_hls(*max_rgb[:3])

    # Convert hue to degrees for the direction logic (matches Magics' 0–360 range)
    min_h_deg = min_h * 360.0
    max_h_deg = max_h * 360.0

    if direction == "anti_clockwise":
        # Ensure we go forward (increasing hue); wrap max if needed
        if max_h_deg < min_h_deg:
            max_h_deg += 360.0
    else:  # clockwise
        # Ensure we go backward (decreasing hue); wrap min if needed
        if min_h_deg < max_h_deg:
            min_h_deg += 360.0

    colours = []
    for i in range(n):
        t = i / (n - 1)
        h = (min_h_deg + t * (max_h_deg - min_h_deg)) % 360.0 / 360.0
        l = min_l + t * (max_l - min_l)
        s = min_s + t * (max_s - min_s)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        colours.append(mcolors.to_hex((r, g, b)))

    return colours


def _normalise_colour(c) -> str:
    """Return a canonical hex string for any colour value, for dedup comparison."""
    import matplotlib.colors as mcolors
    try:
        return mcolors.to_hex(c, keep_alpha=True)
    except (ValueError, TypeError):
        return str(c).lower().strip()


def _strip_sentinel_levels(
    levels: List, colours: Optional[List] = None
) -> tuple:
    """
    Detect and strip sentinel "catch-all" levels at the ends of a level list.

    In Magics, explicit level lists often include extreme values at one or both
    ends (e.g. ``-200, -100, ..., 100, 200`` for a divergence field centred on
    ``[-15, 15]``) that act as open-ended catch-all buckets.  These manifest as
    extend arrows in the rendered plot.

    Detection: a gap between adjacent levels that is **≥ 5× the median of the
    inner gaps** is treated as a sentinel boundary.  The outermost level on that
    side is removed, the corresponding colour band (if supplied) is also
    removed, and ``extend`` is set accordingly.

    Parameters
    ----------
    levels : list
        Sorted level boundaries.
    colours : list or None
        Colour list associated with the levels.  When supplied it is trimmed in
        sync with the level list.

    Returns
    -------
    (levels, colours, extend) : tuple
        Stripped level list, adjusted colours (or the original if ``None``),
        and the ``extend`` string (``"neither"``, ``"min"``, ``"max"``, or
        ``"both"``).
    """
    if not isinstance(levels, list) or len(levels) < 4:
        return levels, colours, "neither"

    import statistics

    diffs = [levels[i + 1] - levels[i] for i in range(len(levels) - 1)]
    inner = diffs[1:-1]
    if not inner:
        return levels, colours, "neither"

    median = statistics.median(inner)
    if median <= 0:
        return levels, colours, "neither"

    # A gap ≥ 5× the median inner gap is treated as a sentinel.
    threshold = 5.0
    has_min = diffs[0] / median >= threshold
    has_max = diffs[-1] / median >= threshold

    if not has_min and not has_max:
        return levels, colours, "neither"

    # Strip the sentinel levels (and the matching colour bands).
    strip_start = 1 if has_min else 0
    strip_end = len(levels) - 1 if has_max else len(levels)
    levels = levels[strip_start:strip_end]

    if colours is not None:
        # Colours may be aligned as (n_levels - 1) bands or n_levels values.
        # Trim the same way _strip_extend_colours does: remove the outermost
        # colour band on each stripped side.
        if has_min:
            colours = colours[1:]
        if has_max:
            colours = colours[:-1]

    if has_min and has_max:
        return levels, colours, "both"
    return levels, colours, "min" if has_min else "max"


def _strip_extend_colours(
    colours: List, levels: Optional[List]
) -> tuple:
    """
    Detect and strip duplicate colours at the start/end of a colour list.

    In Magics, when a style extends beyond the plotted range the extend colour
    is repeated at the beginning and/or end of the colour list.  earthkit-plots
    represents this with ``extend='min'``, ``'max'``, or ``'both'`` plus a
    shorter colour list that covers only the plotted levels.

    Parameters
    ----------
    colours : list
        Raw colour list (one colour per band, length = n_levels - 1 or n_levels + 1).
    levels : list or None
        Level boundaries.  If provided, will be trimmed to match the stripped
        colour list (one fewer entry than colours).

    Returns
    -------
    (colours, levels, extend) : tuple
        Stripped colour list, adjusted levels, and the ``extend`` string.
    """
    if not colours or len(colours) < 2:
        return colours, levels, "neither"

    hexes = [_normalise_colour(c) for c in colours]

    # Count total leading duplicates (including the first element itself)
    n_start = 1
    first = hexes[0]
    for h in hexes[1:]:
        if h == first:
            n_start += 1
        else:
            break
    # Only treat as extend colours if there are at least 2 identical at the edge
    if n_start < 2:
        n_start = 0

    # Count total trailing duplicates (including the last element itself)
    n_end = 1
    last = hexes[-1]
    for h in reversed(hexes[:-1]):
        if h == last:
            n_end += 1
        else:
            break
    if n_end < 2:
        n_end = 0

    # Don't strip if no duplicates found or the whole list is a single colour
    if n_start == 0 and n_end == 0:
        return colours, levels, "neither"
    if n_start + n_end >= len(colours):
        return colours, levels, "neither"

    extend = "neither"
    if n_start > 0 and n_end > 0:
        extend = "both"
    elif n_start > 0:
        extend = "min"
    elif n_end > 0:
        extend = "max"

    # Strip all duplicate extend colours, but keep one copy of each as the
    # first/last entry of the inner colour list.  cmap_and_norm with extend=
    # 'both'/'min'/'max' will automatically use the first/last colours of the
    # list as the under/over (arrow) colours.
    # So: strip (n_start - 1) from the start and (n_end - 1) from the end.
    n_strip_start = n_start - 1
    n_strip_end = n_end - 1
    stripped = colours[n_strip_start: len(colours) - n_strip_end if n_strip_end > 0 else None]

    # Trim levels to match.  After stripping, len(stripped) inner colour bands
    # need len(stripped) + 1 level boundaries.
    # Two cases depending on how Magics counted levels vs colours:
    #   (a) len(levels) == len(colours) + 1  →  already band boundaries; trim same amount
    #   (b) len(levels) == len(colours)       →  one level per colour; trim then close
    if levels is not None:
        if len(levels) == len(colours) + 1:
            levels = levels[n_strip_start: len(levels) - n_strip_end if n_strip_end > 0 else None]
        elif len(levels) == len(colours):
            levels = levels[n_strip_start: len(levels) - n_strip_end if n_strip_end > 0 else None]
            # len(levels) == len(stripped) — add one closing boundary
            if levels and stripped:
                step = levels[1] - levels[0] if len(levels) > 1 else 1
                levels = levels + [levels[-1] + step]

    return stripped, levels, extend


def _convert_colors(
    magics_params: Dict[str, Any], shade_enabled: bool
) -> Optional[Union[str, List]]:
    """
    Convert Magics colour parameters to an earthkit-plots ``colors`` value.
    """
    if shade_enabled:
        shade_method = magics_params.get("contour_shade_method", "area_fill")
        if shade_method in ("dot", "hatch"):
            warnings.warn(
                f"contour_shade_method='{shade_method}' has no earthkit-plots equivalent; "
                "shading will be omitted."
            )
            return None

        colour_method = magics_params.get("contour_shade_colour_method")

        # Infer missing colour_method from whichever colour keys are present.
        if colour_method is None:
            if magics_params.get("contour_shade_colour_list"):
                colour_method = "list"
            elif (
                magics_params.get("contour_shade_min_level_colour")
                or magics_params.get("contour_shade_max_level_colour")
                or magics_params.get("contour_shade_colour_direction")
            ):
                colour_method = "calculate"
            else:
                return None

        if colour_method == "list":
            colour_list_str = magics_params.get("contour_shade_colour_list", "")
            if colour_list_str:
                return parse_colour_list(colour_list_str)

        elif colour_method == "gradients":
            colour_list_str = magics_params.get("contour_gradients_colour_list", "")
            if colour_list_str:
                return parse_colour_list(colour_list_str)

        elif colour_method == "palette":
            palette_name = magics_params.get("contour_shade_palette_name")
            if palette_name:
                palettes = _get_magics_palettes()
                if palette_name in palettes:
                    return palettes[palette_name]["colors"]
                mpl_cmap = MAGICS_PALETTE_TO_MPL.get(palette_name)
                if mpl_cmap:
                    return mpl_cmap
                warnings.warn(
                    f"Magics palette '{palette_name}' has no known matplotlib equivalent; "
                    "the default colormap will be used."
                )
            return None

        elif colour_method == "calculate":
            return _calculate_colours(magics_params)

    else:
        # Contour lines
        if _magics_bool(magics_params.get("contour_line_colour_rainbow", "off")):
            return "rainbow"
        line_colour = magics_params.get("contour_line_colour")
        if line_colour:
            return magics_color(line_colour)

    return None


def _convert_line_properties(magics_params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Magics line properties to matplotlib kwargs."""
    props: Dict[str, Any] = {}

    thickness = magics_params.get("contour_line_thickness")
    if thickness is not None:
        props["linewidths"] = thickness / 2

    style_map = {
        "dash": "dashed",
        "dot": "dotted",
        "chain_dash": "dashdot",
    }
    line_style = magics_params.get("contour_line_style", "solid")
    mpl_line_style = style_map.get(line_style, line_style) if line_style else "solid"

    # Highlight is active when contour_highlight is "on", OR when highlight
    # frequency/thickness/colour keys are present (Magics omits the flag when
    # the feature is implicitly enabled via the other keys).
    highlight_explicit = _magics_bool(magics_params.get("contour_highlight", "off"))
    highlight_implicit = (
        "contour_highlight_frequency" in magics_params
        or "contour_highlight_thickness" in magics_params
        or "contour_highlight_colour" in magics_params
    )
    if highlight_explicit or highlight_implicit:
        highlight_freq = magics_params.get("contour_highlight_frequency", 5)
        highlight_thickness = magics_params.get("contour_highlight_thickness", 3)
        base_thickness = thickness or 1
        # Highlight lines are always solid; base lines use the specified style.
        # Divide by 2 to convert Magics thickness units to matplotlib linewidths.
        props["linewidths"] = [base_thickness / 2] * (highlight_freq - 1) + [highlight_thickness / 2]
        props["linestyles"] = [mpl_line_style] * (highlight_freq - 1) + ["solid"]
    elif mpl_line_style != "solid":
        props["linestyles"] = mpl_line_style

    return props


# ---------------------------------------------------------------------------
# Magics palettes cache
# ---------------------------------------------------------------------------

_MAGICS_PALETTES_CACHE = None


def _load_magics_palettes() -> dict:
    """Load Magics palettes from the bundled JSON data file, if present."""
    import json
    from pathlib import Path

    repo_root = Path(__file__).parent.parent.parent.parent.parent
    palette_file = repo_root / "data" / "colors" / "palettes.json"

    if not palette_file.exists():
        warnings.warn(
            f"Magics palettes file not found: {palette_file}. "
            "Palette name lookups will fall back to MAGICS_PALETTE_TO_MPL."
        )
        return {}
    try:
        with open(palette_file) as f:
            return json.load(f)
    except Exception as exc:
        warnings.warn(f"Failed to load Magics palettes: {exc}")
        return {}


def _get_magics_palettes() -> dict:
    """Return cached Magics palettes, loading them on first call."""
    global _MAGICS_PALETTES_CACHE
    if _MAGICS_PALETTES_CACHE is None:
        _MAGICS_PALETTES_CACHE = _load_magics_palettes()
    return _MAGICS_PALETTES_CACHE


# ---------------------------------------------------------------------------
# Public runtime API: from_magics()
# ---------------------------------------------------------------------------

def from_magics(**magics_params) -> "Style":
    """
    Convert Magics contouring parameters to an earthkit-plots Style object.

    Parameters
    ----------
    **magics_params
        Magics contouring parameters.  Common keys:

        - ``contour_level_selection_type`` – ``"interval"`` or ``"level_list"``
        - ``contour_interval`` – spacing between contour levels
        - ``contour_level_list`` – explicit ``/``-separated level list
        - ``contour_shade`` – ``"on"`` / ``"off"``
        - ``contour_shade_colour_method`` – ``"list"``, ``"gradients"``,
          ``"palette"``
        - ``contour_shade_colour_list`` – ``/``-separated colour string
        - ``contour_line_colour`` – line colour for unshaded contours
        - ``contour_line_style`` – ``"solid"``, ``"dash"``, ``"dot"``

    Returns
    -------
    earthkit.plots.styles.Style

    Examples
    --------
    >>> from earthkit.plots.styles import magics
    >>> style = magics.from_magics(
    ...     contour_level_selection_type="interval",
    ...     contour_interval=4,
    ...     contour_shade="on",
    ...     contour_shade_colour_method="list",
    ...     contour_shade_colour_list="rgb(0,0,128)/white/rgb(128,0,0)",
    ...     contour_shade_min_level=-20,
    ...     contour_shade_max_level=20,
    ... )
    """
    from earthkit.plots.styles import Style

    ek_params: Dict[str, Any] = {}

    shade_enabled = _magics_bool(magics_params.get("contour_shade", "off"))
    contour_enabled = _magics_bool(magics_params.get("contour", "on"))

    if shade_enabled:
        ek_params["preferred_method"] = "contourf"
    elif contour_enabled:
        ek_params["preferred_method"] = "contour"

    levels = _convert_levels(magics_params)
    if levels is not None:
        ek_params["levels"] = levels

    colors = _convert_colors(magics_params, shade_enabled)
    if colors is not None:
        ek_params["colors"] = colors

    colour_method = magics_params.get("contour_shade_colour_method")
    # Infer calculate method the same way _convert_colors does
    if colour_method is None:
        if not magics_params.get("contour_shade_colour_list") and (
            magics_params.get("contour_shade_min_level_colour")
            or magics_params.get("contour_shade_max_level_colour")
            or magics_params.get("contour_shade_colour_direction")
        ):
            colour_method = "calculate"
    extend = _convert_extend(magics_params, shade_enabled, colour_method=colour_method)
    ek_params["extend"] = extend

    ek_params.update(_convert_line_properties(magics_params))

    if _magics_bool(magics_params.get("contour_label", "off")):
        ek_params["labels"] = True

    if not _magics_bool(magics_params.get("legend", "on")):
        ek_params["legend_style"] = None

    return Style(**ek_params)


# ---------------------------------------------------------------------------
# YAML generation helpers
# ---------------------------------------------------------------------------

def _style_key(layer_id: str, magics_style_name: str) -> str:
    """
    Generate the all-caps YAML style key from a layer id and Magics style name.

    e.g. ``"2t"`` + ``"sh_all_fM48t56i4"`` → ``"2T_SH_ALL_FM48T56I4"``
    """
    return f"{layer_id}_{magics_style_name}".upper()


def _style_slug(layer_id: str, magics_style_name: str) -> str:
    """
    Generate a user-facing hyphenated slug for use as the style ``name`` field.

    Uses the original Magics style name (lowercased, underscores converted to
    hyphens) so that the name is recognisable to users familiar with Magics.

    e.g. ``"2t"`` + ``"sh_all_fM48t56i4"`` → ``"sh-all-fm48t56i4"``
    """
    raw = magics_style_name.lower()
    for ch in " _/\\:*?\"<>|(){}[]":
        raw = raw.replace(ch, "-")
    # Collapse repeated hyphens
    while "--" in raw:
        raw = raw.replace("--", "-")
    return raw.strip("-")


def to_yaml_dict(
    layer_id: str,
    magics_style_name: str,
    magics_style_params: Dict[str, Any],
    units: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert a single Magics style dict to an earthkit-plots YAML style entry.

    Parameters
    ----------
    layer_id : str
        The ``eccharts_layer`` value (e.g. ``"2t"``).
    magics_style_name : str
        The key in ``styles.json`` (e.g. ``"sh_all_fM48t56i4"``).
    magics_style_params : dict
        The style parameter dict from ``styles.json``.
    units : str, optional
        earthkit-plots unit string (already converted via ``MAGICS_UNITS_TO_EK``).

    Returns
    -------
    dict
        A dict suitable for embedding under the ``styles:`` key in an
        earthkit-plots auto-styles YAML file.
    """
    shade_enabled = _magics_bool(magics_style_params.get("contour_shade", "off"))
    contour_enabled = _magics_bool(magics_style_params.get("contour", "on"))
    shade_method = magics_style_params.get("contour_shade_method", "area_fill")

    # Determine style type
    if shade_enabled and shade_method not in ("dot", "hatch"):
        style_type = "Style"
    else:
        style_type = "Contour"

    entry: Dict[str, Any] = {
        "name": _style_slug(layer_id, magics_style_name),
        "type": style_type,
    }

    # Colors — always serialise to hex strings so the YAML is safe_load compatible.
    # For shaded styles the colour list goes into "colors" (fill palette).
    # For contour-line-only styles the colour goes into "linecolors" so that
    # Contour.__init__ uses it for line colouring rather than fill colouring.
    colors = _convert_colors(magics_style_params, shade_enabled)
    levels = _convert_levels(magics_style_params)

    # For explicit list-based shaded styles, detect duplicate colours at the ends
    # — these are Magics' extend colours.  Strip them and derive extend from the
    # pattern rather than from _convert_extend (which over-eagerly sets "both").
    # Skip this for calculate/palette/gradient methods whose colour lists are
    # generated programmatically and may have incidental near-duplicate edge colours.
    colour_method = magics_style_params.get("contour_shade_colour_method")
    # Infer calculate method the same way _convert_colors does
    if colour_method is None:
        if not magics_style_params.get("contour_shade_colour_list") and (
            magics_style_params.get("contour_shade_min_level_colour")
            or magics_style_params.get("contour_shade_max_level_colour")
            or magics_style_params.get("contour_shade_colour_direction")
        ):
            colour_method = "calculate"
    is_explicit_list = colour_method in ("list", None) and bool(
        magics_style_params.get("contour_shade_colour_list")
    )
    extend = None
    if shade_enabled and isinstance(colors, list) and is_explicit_list:
        hex_colors = [to_hex(c) for c in colors]
        hex_colors, levels, extend = _strip_extend_colours(hex_colors, levels)
        colors = hex_colors  # already hex strings, skip re-conversion below

    # Extend: use the value derived from colour deduplication if available,
    # otherwise fall back to _convert_extend heuristics, then to level-spacing
    # sentinel detection (large outlier gaps at ends → extend + strip that level).
    if extend is None:
        extend = _convert_extend(
            magics_style_params, shade_enabled, colour_method=colour_method
        )
    if extend == "neither" and isinstance(levels, list):
        # Pass colours so sentinel bands are stripped in sync with the levels.
        sentinel_colours = colors if isinstance(colors, list) else None
        levels, sentinel_colours, extend = _strip_sentinel_levels(levels, sentinel_colours)
        if sentinel_colours is not None:
            colors = sentinel_colours

    # Serialise colors (after any sentinel stripping that may have shortened the list).
    if colors is not None:
        color_key = "colors" if shade_enabled else "linecolors"
        if isinstance(colors, list):
            # May already be hex strings (from _strip_extend_colours) or raw values
            entry[color_key] = [c if isinstance(c, str) and c.startswith("#") else to_hex(c) for c in colors]
        elif isinstance(colors, tuple):
            entry[color_key] = to_hex(colors)
        else:
            # Already a string (colormap name, named colour, or hex)
            entry[color_key] = colors

    if levels is not None:
        entry["levels"] = levels

    if extend and extend != "neither":
        entry["extend"] = extend

    # Units
    if units:
        entry["units"] = units

    # Line properties (contour-only styles)
    if not shade_enabled and contour_enabled:
        line_props = _convert_line_properties(magics_style_params)
        entry.update(line_props)

    return entry


def convert_parameter_file(
    param_file_path: str,
    styles_dict: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Convert one Magics parameter JSON file to an earthkit-plots style descriptor.

    Parameters
    ----------
    param_file_path : str
        Path to a Magics parameter JSON file (e.g. ``2t.json``).
    styles_dict : dict
        The fully loaded ``styles.json`` dict.

    Returns
    -------
    dict or None
        A dict with keys ``"id"``, ``"criteria"``, ``"styles"``, ``"optimal"``,
        ``"units"`` ready to be written as earthkit-plots YAML files, or
        ``None`` if the file should be skipped (no ``eccharts_layer``).
    """
    import json

    with open(param_file_path) as f:
        entries = json.load(f)

    # A parameter file may contain multiple entries; process each independently
    results = []
    for entry in entries:
        layer_id = entry.get("eccharts_layer")
        if not layer_id:
            # Scaling files (e.g. scaling_celsius.json) — skip
            return None

        # eccharts_layer may be a list of layer names sharing the same styles;
        # use the first element as the canonical id for file naming
        if isinstance(layer_id, list):
            layer_id = layer_id[0]

        magics_units = entry.get("prefered_units")
        ek_units = MAGICS_UNITS_TO_EK.get(magics_units) if magics_units else None
        if magics_units and ek_units is None:
            warnings.warn(
                f"[{layer_id}] Unknown Magics units '{magics_units}'; "
                "units will be omitted from the converted style."
            )

        criteria = entry.get("match", [])
        style_names = entry.get("styles", [])

        converted_styles: Dict[str, Dict[str, Any]] = {}
        optimal_key = None

        for magics_style_name in style_names:
            magics_style_params = styles_dict.get(magics_style_name)
            if magics_style_params is None:
                warnings.warn(
                    f"[{layer_id}] Style '{magics_style_name}' not found in styles.json; "
                    "skipping."
                )
                continue

            yaml_key = _style_key(layer_id, magics_style_name)
            try:
                style_entry = to_yaml_dict(layer_id, magics_style_name, magics_style_params, ek_units)
            except Exception as exc:
                warnings.warn(
                    f"[{layer_id}] Failed to convert style '{magics_style_name}': {exc}; skipping."
                )
                continue
            converted_styles[yaml_key] = style_entry

            if optimal_key is None:
                optimal_key = yaml_key

        if not converted_styles:
            continue

        results.append({
            "id": layer_id,
            "units": ek_units,
            "criteria": criteria,
            "styles": converted_styles,
            "optimal": optimal_key,
        })

    return results if results else None


def generate_yaml_files(magics_ecmwf_dir: str, output_dir: str) -> None:
    """
    Convert all Magics ECMWF parameter JSON files to earthkit-plots YAML files.

    Writes one ``auto-styles/<id>.yml`` and one ``identities/<id>.yml`` per
    Magics parameter file that contains an ``eccharts_layer`` field.

    Parameters
    ----------
    magics_ecmwf_dir : str
        Path to the Magics ECMWF styles directory, e.g.
        ``/path/to/magics/share/magics/styles/ecmwf/``.
    output_dir : str
        Path to the earthkit-plots ``data/styles/`` directory, e.g.
        ``src/earthkit/plots/data/styles/``.

    Examples
    --------
    >>> from earthkit.plots.styles.magics import generate_yaml_files
    >>> generate_yaml_files(
    ...     magics_ecmwf_dir="/path/to/magics/share/magics/styles/ecmwf",
    ...     output_dir="src/earthkit/plots/data/styles",
    ... )
    """
    import glob
    import json
    import os

    import yaml

    magics_ecmwf_dir = os.path.abspath(magics_ecmwf_dir)
    output_dir = os.path.abspath(output_dir)
    auto_styles_dir = os.path.join(output_dir, "auto-styles")
    identities_dir = os.path.join(output_dir, "identities")
    os.makedirs(auto_styles_dir, exist_ok=True)
    os.makedirs(identities_dir, exist_ok=True)

    # Load styles.json once
    styles_json_path = os.path.join(magics_ecmwf_dir, "styles.json")
    with open(styles_json_path) as f:
        styles_dict = json.load(f)

    param_files = sorted(
        fp for fp in glob.glob(os.path.join(magics_ecmwf_dir, "*.json"))
        if not fp.endswith("styles.json")
        and not os.path.basename(fp).startswith("cds")
    )

    written = 0
    skipped = 0

    for param_file in param_files:
        results = convert_parameter_file(param_file, styles_dict)
        if not results:
            skipped += 1
            continue

        for result in results:
            layer_id = result["id"]

            # ---- auto-styles YAML ----------------------------------------
            auto_style_doc = {
                "id": layer_id,
                "optimal": result["optimal"],
                "styles": result["styles"],
            }
            auto_style_path = os.path.join(auto_styles_dir, f"{layer_id}.yml")
            with open(auto_style_path, "w") as f:
                yaml.dump(
                    auto_style_doc,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # ---- identity YAML -------------------------------------------
            identity_doc = {
                "id": layer_id,
                "criteria": result["criteria"],
            }
            identity_path = os.path.join(identities_dir, f"{layer_id}.yml")
            with open(identity_path, "w") as f:
                yaml.dump(
                    identity_doc,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            written += 1

    print(
        f"[magics] Wrote {written} style pair(s) to {output_dir}; "
        f"skipped {skipped} file(s) with no eccharts_layer."
    )

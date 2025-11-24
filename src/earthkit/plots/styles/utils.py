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
Utility functions for style handling.
"""

from typing import Union, Optional, Any


def resolve_style(
    style: Union[str, "Style", None],
    data: Optional[Any] = None,
    auto_style: bool = False,
    units: Optional[str] = None,
) -> Optional["Style"]:
    """
    Resolve a style parameter to a Style object.

    This function handles multiple input types:
    - Style object: returned as-is
    - "auto": triggers automatic style matching based on data metadata (uses first match)
    - Other string: looks up the named style in the style library
    - None: returns None (unless auto_style=True, which uses first match)

    Parameters
    ----------
    style : str, Style, or None
        The style to resolve. Can be:
        - A Style object (returned as-is)
        - "auto" (triggers automatic matching)
        - A style name like "MEAN_SEA_LEVEL_PRESSURE_IN_HPA"
        - None
    data : Any, optional
        Data object to use for automatic style matching.
        Only used when style="auto" or auto_style=True.
    auto_style : bool, default=False
        If True and style is None, attempt automatic style matching.
    units : str, optional
        If provided and style="auto", only match styles with compatible units
        or styles that have no units defined.

    Returns
    -------
    Style or None
        The resolved Style object, or None if no style could be resolved.

    Raises
    ------
    ValueError
        If a named style string is provided but not found in the style library.
    ValueError
        If style="auto" but no data is provided for matching.

    Examples
    --------
    >>> from earthkit.plots.styles import Style
    >>> from earthkit.plots.styles.utils import resolve_style
    >>>
    >>> # Pass through a Style object
    >>> style_obj = Style(colors='red')
    >>> resolve_style(style_obj) is style_obj
    True
    >>>
    >>> # Look up a named style
    >>> style = resolve_style("MEAN_SEA_LEVEL_PRESSURE_IN_HPA")
    >>> style.plot_type
    'contour'
    >>>
    >>> # Automatic matching
    >>> style = resolve_style("auto", data=my_data)
    >>>
    >>> # Automatic matching with units filter
    >>> style = resolve_style("auto", data=my_data, units="m3 s-1")
    >>>
    >>> # No style
    >>> resolve_style(None) is None
    True
    """
    from earthkit.plots.styles import Style

    # If it's already a Style object, return it
    if isinstance(style, Style):
        return style

    # If None, check auto_style flag
    if style is None:
        if auto_style and data is not None:
            # Attempt automatic style matching
            from earthkit.plots.styles import match, get
            style_names = match(data, units=units)
            if style_names:
                # Use the first matching style
                return get(style_names[0])
        return None

    # If it's a string, resolve it
    if isinstance(style, str):
        # Handle "auto" explicitly
        if style == "auto":
            if data is None:
                raise ValueError(
                    "Cannot use style='auto' without providing data for matching. "
                    "Either pass data or use a named style."
                )
            from earthkit.plots.styles import match, get
            style_names = match(data, units=units)
            if style_names:
                # Use the first matching style
                return get(style_names[0])
            # If no match found, return None (could also raise an error)
            return None

        # Otherwise, treat as a named style
        from earthkit.plots.styles import get
        style_obj = get(style)
        if style_obj is None:
            from earthkit.plots.styles import available
            raise ValueError(
                f"Style '{style}' not found. "
                f"Available styles can be listed with: styles.available()"
            )
        return style_obj

    # Unknown type
    raise TypeError(
        f"Style must be a Style object, string, or None. Got: {type(style)}"
    )

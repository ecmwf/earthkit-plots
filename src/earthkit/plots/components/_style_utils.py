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
Style configuration and data-processing utilities for the plotting pipeline.

These helpers sit between the raw data (Source) and the matplotlib call.
They are deliberately free of subplot/axes state so they can be tested in
isolation without a display.
"""

import warnings
from typing import Any

import numpy as np

from earthkit.plots.styles import (
    _STYLE_KWARGS,
    DEFAULT_STYLE,
    Contour,
    Quiver,
    Style,
    auto,
)


def _prepare_style_and_units(
    style: Style | str | None,
    units: str | None,
    auto_style: bool,
) -> tuple[str | None, Style | str | None]:
    """
    Normalise the ``style`` and ``units`` arguments before the pipeline runs.

    Three responsibilities:

    1. Emit a deprecation warning when the legacy ``auto_style`` kwarg is used.
    2. Resolve a named-style string (anything other than ``"auto"``) to a
       :class:`~earthkit.plots.styles.Style` object so its ``_units`` are
       readable in the next step.
    3. Back-fill ``units`` from the style's own ``_units`` when the caller
       did not supply units explicitly.

    Named-style resolution *must* happen here — before ``get_source()`` — so
    that the target units from the style are available for unit conversion
    inside the Source constructor.

    Parameters
    ----------
    style:
        Raw value from the caller: a Style object, ``"auto"``, a named-style
        string, or ``None``.
    units:
        Target units supplied by the caller (may be ``None``).
    auto_style:
        Deprecated flag; ``True`` is equivalent to ``style="auto"``.

    Returns
    -------
    (units, style)
        Possibly updated pair ready for the rest of the pipeline.
    """
    if auto_style:
        warnings.warn(
            "The 'auto_style' parameter is deprecated and will be removed in a "
            "future version. Please use style='auto' instead.",
            DeprecationWarning,
            stacklevel=4,
        )

    # Resolve named-style strings early so we can read their _units below.
    if isinstance(style, str) and style != "auto":
        style = auto.load_style(style)

    if units is None and style is not None and style != "auto":
        if hasattr(style, "_units") and style._units is not None:
            units = style._units

    return units, style


def configure_style(
    method_name: str,
    style: Style | str | None,
    source: Any,
    units: str | None,
    auto_style: bool,
    kwargs: dict[str, Any],
) -> Style:
    """
    Resolve the final :class:`~earthkit.plots.styles.Style` for a plot call.

    Side-effect: any key in *kwargs* that belongs to ``_STYLE_KWARGS``
    (e.g. ``levels``, ``colors``, ``extend``) is **popped** from the dict so
    that only matplotlib-native keys remain after this call returns.  Callers
    that need to preserve their kwargs should pass a copy (``{**kwargs}``).

    Parameters
    ----------
    method_name:
        Name of the plotting method (``"contourf"``, ``"pcolormesh"``, …).
    style:
        An existing Style, ``"auto"``, or ``None``.  Named-style strings must
        already be resolved to Style objects by ``_prepare_style_and_units``
        before this is called.
    source:
        The data source; used by ``guess_style`` when ``auto_style`` is True.
    units:
        Target units; used when constructing a fresh Style from scratch.
    auto_style:
        Whether to call ``guess_style`` for automatic style selection.
    kwargs:
        Live kwargs dict from the caller — modified in place.

    Returns
    -------
    Style
        A fully configured style object.
    """
    # Treat style="auto" as the canonical spelling of auto_style=True.
    # Named-style strings are already resolved before this function is called.
    if style == "auto":
        auto_style = True
        style = None

    # cmap= is a user-friendly alias for colors=
    if "cmap" in kwargs and "colors" in kwargs:
        raise ValueError("Cannot specify both 'cmap' and 'colors'. They are aliases for the same parameter.")
    if "cmap" in kwargs:
        kwargs["colors"] = kwargs.pop("cmap")

    # Pull style-specific keys out of kwargs so only matplotlib keys remain.
    style_kwargs = {k: kwargs.pop(k) for k in _STYLE_KWARGS if k in kwargs}

    # Existing style + override kwargs → copy with overrides applied.
    if style is not None and style_kwargs:
        return style.with_overrides(**style_kwargs)

    # Existing style, no overrides → return as-is.
    if style is not None:
        return style

    # Determine style class from method name.
    if method_name.startswith("contour"):
        style_class = Contour
    elif method_name in ("quiver", "barbs"):
        style_class = Quiver
    else:
        style_class = Style

    # Some methods suppress the auto-legend by default; callers can still
    # override by passing legend_style= explicitly.
    _NO_DEFAULT_LEGEND = {"stripes"}
    if method_name in _NO_DEFAULT_LEGEND:
        style_kwargs.setdefault("legend_style", None)

    if not auto_style:
        if style_kwargs or units:
            return style_class(**{**style_kwargs, "units": units})
        if style_class is not Style:
            return style_class()
        return DEFAULT_STYLE

    # Auto-style path: guess from source metadata, then apply any overrides.
    guessed = auto.guess_style(source, units=units or source.units)
    if style_kwargs and guessed is not None:
        guessed = guessed.with_overrides(**style_kwargs)
    return guessed


def apply_scale_factor(
    style: Style,
    source: Any,
    z: str | np.ndarray | list[float] | None,
) -> np.ndarray | None:
    """
    Apply the style's scale factor to the z values from *source*.

    Unit conversion is handled upstream by the Source constructor; this
    function only applies the multiplicative/additive scale factor stored on
    the Style object (e.g. Pa → hPa via a factor of 0.01).

    Parameters
    ----------
    style:
        Style whose ``apply_scale_factor`` method will be called.
    source:
        Data source whose ``z.values`` are used when *z* is ``None``.
    z:
        Original z specification passed by the caller.  Used only as a
        None-sentinel; the actual values come from ``source.z.values``.

    Returns
    -------
    np.ndarray or None
        Scaled z values, or ``None`` when no z data is available.
    """
    if source._data is None and z is None:
        return None
    if source.z is None:
        return None
    return style.apply_scale_factor(source.z.values)


def apply_sampling(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray | None,
    every: int | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Thin out coordinate and data arrays by taking every *every*-th element.

    Useful for reducing resolution on large datasets before plotting.
    When *every* is ``None`` the inputs are returned unchanged.

    Parameters
    ----------
    x_values, y_values:
        Coordinate arrays.
    z_values:
        Data array, or ``None`` for coordinate-only plots.
    every:
        Stride; ``None`` means no sampling.

    Returns
    -------
    (x_values, y_values, z_values)
        Strided arrays (or the original objects when *every* is ``None``).
    """
    if every is None:
        return x_values, y_values, z_values

    x_values = x_values[::every]
    y_values = y_values[::every]
    if z_values is not None:
        z_values = z_values[::every, ::every]

    return x_values, y_values, z_values

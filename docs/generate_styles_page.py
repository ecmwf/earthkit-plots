#!/usr/bin/env python3
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
Generate the styles gallery RST page and colorbar preview images.

This script is called automatically by conf.py at the start of every Sphinx
documentation build, so the gallery always reflects the current set of styles
in ``src/earthkit/plots/data/styles/auto-styles/``.
"""

import glob
import os
import sys
import warnings

import matplotlib
import yaml

matplotlib.use("Agg")

# Ensure the package source is importable when this script is run directly
_here = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_here, "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


def _styles_data_dir():
    """Return the path to the auto-styles directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(
        here, "..", "src", "earthkit", "plots", "data", "styles", "auto-styles"
    )


def _images_dir(docs_dir):
    """Return (and create) the directory where colorbar images are written."""
    out = os.path.join(docs_dir, "_static", "styles")
    os.makedirs(out, exist_ok=True)
    return out


def _load_all_styles():
    """
    Parse every YAML file in auto-styles and return a list of dicts::

        {
            "file_id": str,      # the style-file identity (id: field)
            "name": str,         # user-facing style name (name: field), or internal key
            "optimal": bool,     # whether this is the default variant
            "style_dict": dict,  # the raw style config
        }

    Styles without a ``name`` field are skipped.
    """
    entries = []
    seen_names = set()
    for fpath in sorted(glob.glob(os.path.join(_styles_data_dir(), "*.yml"))):
        with open(fpath) as f:
            config = yaml.safe_load(f)
        file_id = config.get("id", os.path.splitext(os.path.basename(fpath))[0])
        optimal = config.get("optimal")
        for key, style_dict in config.get("styles", {}).items():
            name = style_dict.get("name")
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            entries.append(
                {
                    "file_id": file_id,
                    "name": name,
                    "optimal": key == optimal,
                    "style_dict": dict(style_dict),
                }
            )
    return entries


def _make_style_object(style_dict):
    """Instantiate a Style (or subclass) from a raw YAML dict."""
    from earthkit.plots import styles

    d = dict(style_dict)
    style_type = d.pop("type", "Style")
    if "levels" in d:
        import earthkit.plots.styles.levels as lvl_mod

        d["levels"] = lvl_mod.Levels.from_config(d["levels"])
    cls = getattr(styles, style_type, styles.Style)
    # Quiver / Vector styles don't produce useful colorbars — skip
    if issubclass(cls, styles.Vector):
        return None
    return cls(**d)


def _units_display(style):
    """
    Return a formatted units string for the colorbar label, or None.

    Uses the same ``format_units`` helper that earthkit-plots uses for axis
    labels so the output (e.g. ``$m \\cdot s^{-1}$``) matches what users see
    in actual plots.
    """
    from earthkit.plots.metadata.units import format_units

    raw = style.units  # honours _units_label override, else falls back to _units
    if not raw:
        return None
    try:
        return format_units(raw)
    except Exception:
        return str(raw)


def _save_colorbar(style, filepath):
    """
    Save a standalone horizontal colorbar image for *style* to *filepath*.

    Builds the colorbar directly from the Style's cmap/norm without needing
    to plot any actual data.  The background is transparent; units (if any)
    are shown as a label below the colorbar using the same LaTeX formatting
    that earthkit-plots applies to plot axes.
    """
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mpl_kwargs = style.to_matplotlib_kwargs(data=None)

    cmap = mpl_kwargs.get("cmap")
    norm = mpl_kwargs.get("norm")

    if cmap is None:
        cmap = cm.get_cmap("viridis")
    if norm is None:
        norm = mcolors.Normalize(vmin=0, vmax=1)

    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    units_label = _units_display(style)

    # Make the figure taller when we need room for a units label
    fig_height = 0.375 if units_label else 0.25
    fig, ax = plt.subplots(figsize=(9.6, fig_height))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    extend = style._legend_kwargs.get("extend", "neither")

    cbar_kwargs = dict(
        orientation="horizontal",
        cax=ax,
        extend=extend,
        format=lambda x, _: f"{x:g}",
    )

    if isinstance(norm, mcolors.BoundaryNorm):
        # norm.boundaries may include ±inf from 'extend'; use finite bounds only
        finite_boundaries = [b for b in norm.boundaries if not (b == float("inf") or b == float("-inf"))]
        ticks = style._legend_kwargs.get("ticks")
        if ticks is None and len(finite_boundaries) <= 20:
            ticks = finite_boundaries
        if ticks is not None:
            cbar_kwargs["ticks"] = ticks
        # Rebuild norm without infinite boundaries so colorbar renders correctly
        norm = mcolors.BoundaryNorm(finite_boundaries, ncolors=mpl_kwargs["cmap"].N, extend=extend)
        sm = cm.ScalarMappable(cmap=mpl_kwargs["cmap"], norm=norm)
        sm.set_array([])

    cbar = fig.colorbar(sm, **cbar_kwargs)
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(size=0)

    if units_label:
        cbar.set_label(units_label, labelpad=4)

    plt.savefig(filepath, dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)


def _style_slug(name):
    """Return a filesystem-safe slug from a style name."""
    slug = name.lower()
    for ch in " /\\:*?\"<>|(){}[]":
        slug = slug.replace(ch, "_")
    return slug


def _units_label(style_dict):
    units = style_dict.get("units")
    return f" ({units})" if units else ""


def generate(docs_dir=None):
    """
    Generate colorbar images and the RST styles gallery page.

    Parameters
    ----------
    docs_dir : str, optional
        Path to the ``docs/`` directory.  Defaults to the directory that
        contains this script.
    """
    if docs_dir is None:
        docs_dir = os.path.dirname(os.path.abspath(__file__))

    images_dir = _images_dir(docs_dir)
    entries = _load_all_styles()

    # Group entries by file_id so we can render one section per variable
    sections: dict[str, list] = {}
    for e in entries:
        sections.setdefault(e["file_id"], []).append(e)

    rst_lines = [
        ".. _styles-gallery:",
        "",
        "Styles gallery",
        "==============",
        "",
        "This page lists all built-in styles shipped with **earthkit-plots**.",
        "Each entry shows the style name and a preview of the colorbar.",
        "Click the copy button next to any name to copy it for use in your code::",
        "",
        "    chart.contourf(data, style=\"temperature-2m-turbo-celsius\")",
        "",
        ".. note::",
        "",
        "   This page is auto-generated during the documentation build.",
        "   Any new styles added to ``data/styles/auto-styles/`` will appear",
        "   here automatically.",
        "",
        ".. raw:: html",
        "",
        "   <style>",
        "   .ek-style-entry {",
        "     display: flex;",
        "     align-items: center;",
        "     justify-content: space-between;",
        "     margin-bottom: 1.2em;",
        "   }",
        "   .ek-style-left { display: flex; align-items: center; gap: 6px; }",
        "   .ek-style-name {",
        "     font-family: monospace;",
        "     font-size: 0.95em;",
        "     background: #f5f5f5;",
        "     border: 1px solid #ddd;",
        "     border-radius: 3px;",
        "     padding: 2px 6px;",
        "   }",
        "   .ek-copy-btn {",
        "     display: inline-flex;",
        "     align-items: center;",
        "     gap: 5px;",
        "     padding: 3px 10px;",
        "     font-size: 0.8em;",
        "     cursor: pointer;",
        "     border: 1px solid #aaa;",
        "     border-radius: 3px;",
        "     background: #fff;",
        "     white-space: nowrap;",
        "     flex-shrink: 0;",
        "   }",
        "   .ek-copy-btn:hover { background: #e8e8e8; }",
        "   .ek-copy-btn svg { width: 14px; height: 14px; vertical-align: middle; }",
        "   </style>",
        "   <script>",
        "   var EK_COPY_SVG = '<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path stroke=\"none\" d=\"M0 0h24v24H0z\" fill=\"none\"/><path d=\"M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z\" /><path d=\"M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1\" /></svg>';",
        "   var EK_CHECK_SVG = '<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path stroke=\"none\" d=\"M0 0h24v24H0z\" fill=\"none\"/><path d=\"M5 12l5 5l10 -10\" /></svg>';",
        "   function ekCopy(btn, text) {",
        "     navigator.clipboard.writeText(text).then(function() {",
        "       btn.innerHTML = EK_CHECK_SVG + ' Style name copied';",
        "       setTimeout(function() {",
        "         btn.innerHTML = EK_COPY_SVG + ' Copy this style name';",
        "       }, 1500);",
        "     });",
        "   }",
        "   </script>",
        "",
    ]

    for file_id, style_entries in sections.items():
        section_title = file_id.replace("-", " ").capitalize()
        rst_lines += [
            section_title,
            "-" * len(section_title),
            "",
        ]

        for e in style_entries:
            name = e["name"]
            style_dict = e["style_dict"]
            slug = _style_slug(name)
            img_filename = f"{slug}.png"
            img_path = os.path.join(images_dir, img_filename)
            img_rst_path = f"_static/styles/{img_filename}"

            optimal_marker = ""
            copy_svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"'
                ' fill="none" stroke="currentColor" stroke-width="2"'
                ' stroke-linecap="round" stroke-linejoin="round">'
                '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
                '<path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1'
                ' 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1'
                ' -2.667 -2.667z" />'
                '<path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2'
                ' -2h10c.75 0 1.158 .385 1.5 1" /></svg>'
            )
            name_html = (
                f'<div class="ek-style-entry">'
                f'<div class="ek-style-left">'
                f'<code class="ek-style-name">{name}</code>'
                f'{optimal_marker}'
                f'</div>'
                f'<button class="ek-copy-btn" onclick="ekCopy(this, \'{name}\')">'
                f'{copy_svg} Copy this style name'
                f'</button>'
                f'</div>'
            )

            style_obj = _make_style_object(style_dict)

            if style_obj is None:
                # Vector/Quiver — no colorbar to show
                rst_lines += [
                    ".. raw:: html",
                    "",
                    f"   {name_html}",
                    "",
                    "*(No colorbar — vector style)*",
                    "",
                ]
                continue

            try:
                _save_colorbar(style_obj, img_path)
                rst_lines += [
                    ".. raw:: html",
                    "",
                    f"   {name_html}",
                    "",
                    f".. image:: {img_rst_path}",
                    "   :alt: colorbar preview",
                    "",
                ]
            except ValueError as exc:
                if "dynamic levels" in str(exc):
                    rst_lines += [
                        ".. raw:: html",
                        "",
                        f"   {name_html}",
                        "",
                        "*(Contour style — levels are determined from data at plot time)*",
                        "",
                    ]
                else:
                    rst_lines += [
                        ".. raw:: html",
                        "",
                        f"   {name_html}",
                        "",
                        f"*(Colorbar preview unavailable: {exc})*",
                        "",
                    ]
            except Exception as exc:
                rst_lines += [
                    ".. raw:: html",
                    "",
                    f"   {name_html}",
                    "",
                    f"*(Colorbar preview unavailable: {exc})*",
                    "",
                ]

    rst_content = "\n".join(rst_lines) + "\n"

    out_rst = os.path.join(docs_dir, "styles-gallery.rst")
    with open(out_rst, "w") as f:
        f.write(rst_content)

    print(f"[styles gallery] wrote {out_rst}")
    print(f"[styles gallery] wrote {len(entries)} colorbar images to {images_dir}")


if __name__ == "__main__":
    generate()

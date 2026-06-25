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
_src = os.path.join(_here, "..", "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


def _styles_data_dir():
    """Return the path to the auto-styles directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "..", "src", "earthkit", "plots", "data", "styles", "auto-styles")


def _images_dir(docs_dir):
    """Return (and create) the directory where colorbar images are written."""
    out = os.path.join(docs_dir, "_static", "styles")
    os.makedirs(out, exist_ok=True)
    return out


def _identities_data_dir():
    """Return the path to the identities directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "..", "src", "earthkit", "plots", "data", "styles", "identities")


def _section_title(file_id):
    """
    Return a human-readable title for a styles section.

    Looks up the first non-empty ``long_name`` value across all criteria in the
    paired identity file.  Falls back to title-casing the ``file_id`` with
    underscores/hyphens replaced by spaces when no ``long_name`` is found.
    """
    identity_path = os.path.join(_identities_data_dir(), f"{file_id}.yml")
    if os.path.isfile(identity_path):
        with open(identity_path) as f:
            config = yaml.safe_load(f)
        for criterion in config.get("criteria", []):
            if not isinstance(criterion, dict):
                continue
            val = criterion.get("long_name")
            if not val:
                continue
            # val may be a single string or a list — take the first non-empty entry
            if isinstance(val, list):
                val = next((v for v in val if v), None)
            if val:
                return str(val)
    # Fallback: humanise the file_id
    return file_id.replace("_", " ").replace("-", " ").title()


def _load_identity_search_terms(file_id):
    """
    Read the identity YAML for *file_id* and extract all searchable terms:
    shortName, long_name, standard_name, paramId values from all criteria
    entries.  Returns a set of lowercase strings.
    """
    identity_path = os.path.join(_identities_data_dir(), f"{file_id}.yml")
    if not os.path.isfile(identity_path):
        return set()
    with open(identity_path) as f:
        config = yaml.safe_load(f)
    terms = set()
    for criterion in config.get("criteria", []):
        if not isinstance(criterion, dict):
            continue
        for key in ("shortName", "long_name", "standard_name", "paramId"):
            val = criterion.get(key)
            if val is None:
                continue
            if isinstance(val, list):
                for v in val:
                    terms.add(str(v).lower())
            else:
                terms.add(str(val).lower())
    return terms


def _load_all_styles():
    """
    Parse every YAML file in auto-styles and return a list of dicts::

        {
            "file_id": str,      # the style-file identity (id: field)
            "name": str,         # user-facing style name (name: field), or internal key
            "optimal": bool,     # whether this is the default variant
            "style_dict": dict,  # the raw style config
            "search_terms": set, # searchable terms from the paired identity file
        }

    Styles without a ``name`` field are skipped.
    """
    entries = []
    seen_names = set()
    # Cache identity terms per file_id to avoid re-reading the same file for
    # every style variant in a section.
    identity_cache = {}
    for fpath in sorted(glob.glob(os.path.join(_styles_data_dir(), "*.yml"))):
        with open(fpath) as f:
            config = yaml.safe_load(f)
        file_id = config.get("id", os.path.splitext(os.path.basename(fpath))[0])
        optimal = config.get("optimal")
        if file_id not in identity_cache:
            identity_cache[file_id] = _load_identity_search_terms(file_id)
        search_terms = identity_cache[file_id]
        for key, style_dict in config.get("styles", {}).items():
            name = style_dict.get("name")
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            entries.append({
                "file_id": file_id,
                "name": name,
                "optimal": key == optimal,
                "style_dict": dict(style_dict),
                "search_terms": search_terms,
            })
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
    return cls(**d)


def _units_display(style):
    r"""
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


def _save_contour_sample(style, filepath):
    """
    Save a compact 2-line sample image for a Contour style.

    Shows a base line (with the style's linestyle/linewidth) and a highlight
    line (solid, thicker) so the pattern is clear without needing real data.
    """
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt

    linewidths = style._kwargs.get("linewidths", 0.75)
    linestyles = style._kwargs.get("linestyles", "solid")

    # Extract base and highlight properties from list or scalar
    if isinstance(linewidths, list) and len(linewidths) >= 2:
        base_lw, highlight_lw = linewidths[0], linewidths[-1]
    elif isinstance(linewidths, list):
        base_lw = highlight_lw = linewidths[0]
    else:
        base_lw = highlight_lw = linewidths

    if isinstance(linestyles, list) and len(linestyles) >= 2:
        base_ls, highlight_ls = linestyles[0], linestyles[-1]
    elif isinstance(linestyles, list):
        base_ls = highlight_ls = linestyles[0]
    else:
        base_ls, highlight_ls = linestyles, "solid"

    # Resolve line colour — colors may be a hex string, named colour, or cmap
    linecolors = style._colors
    try:
        color = mcolors.to_rgba(linecolors)
    except (ValueError, TypeError):
        color = "black"

    units_label = _units_display(style)
    fig_height = 0.375 if units_label else 0.25
    fig, ax = plt.subplots(figsize=(9.6, fig_height))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Base line at y=0.75, highlight line at y=0.25
    ax.axhline(0.75, color=color, linewidth=base_lw, linestyle=base_ls)
    ax.axhline(0.25, color=color, linewidth=highlight_lw, linestyle=highlight_ls)

    if units_label:
        ax.text(
            1.01,
            0.5,
            units_label,
            transform=ax.transAxes,
            va="center",
            ha="left",
            fontsize=8,
        )

    plt.savefig(filepath, dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)


def _save_vector_sample(style, filepath):
    """
    Save a sample image for a Vector/Quiver style.

    If the style has colours (magnitude-mapped), renders a colorbar.
    Otherwise renders a row of sample arrows in the style's colour.
    """
    from earthkit.plots.schemas import schema

    # A vector style has explicit colours only when the YAML set a "colors" key,
    # i.e. _colors differs from the schema default sentinel.
    has_colors = style._colors is not None and style._colors != schema.default_cmap
    if has_colors:
        _save_colorbar(style, filepath)
        return

    import matplotlib.pyplot as plt

    color = style._kwargs.get("color", style._kwargs.get("colors", "black"))
    units_label = _units_display(style)
    fig_height = 0.375 if units_label else 0.25
    fig, ax = plt.subplots(figsize=(9.6, fig_height))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Draw a row of evenly spaced arrows across the figure
    n_arrows = 12
    for i in range(n_arrows):
        x = (i + 0.5) / n_arrows
        ax.annotate(
            "",
            xy=(x + 0.03, 0.5),
            xytext=(x, 0.5),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0),
        )

    if units_label:
        ax.text(
            1.01,
            0.5,
            units_label,
            transform=ax.transAxes,
            va="center",
            ha="left",
            fontsize=8,
        )

    plt.savefig(filepath, dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)


def _make_preview_levels(style, n=10):
    """
    Return a list of ~*n* evenly-spaced synthetic levels suitable for previewing
    a dynamic-level style (one whose levels depend on data at plot time).

    The step size comes from the style's ``Levels._step``.  The range is centred
    on 0 (or on ``_reference`` when set) so the colorbar looks representative
    without committing to any real data range.

    Returns ``None`` if the style does not use dynamic step-based levels.
    """
    from earthkit.plots.styles import levels as _levels_mod

    lv = getattr(style, "_levels", None)
    if lv is None or not isinstance(lv, _levels_mod.Levels):
        return None
    if lv._levels is not None or lv._step is None:
        return None

    step = float(lv._step)
    ref = float(lv._reference) if lv._reference is not None else 0.0
    # Centre ~n levels on ref: half below, half above
    half = n // 2
    start = ref - half * step
    stop = ref + half * step + step * 0.5  # small overshoot so arange includes end
    import numpy as np

    levels = np.arange(start, stop, step).tolist()
    # Keep exactly n levels if arange gave slightly more/less due to float rounding
    if len(levels) > n + 1:
        levels = levels[: n + 1]
    return levels


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

    extend = style.extend or "neither"

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
    for ch in ' /\\:*?"<>|(){}[]':
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
        '    chart.contourf(data, style="temperature-2m-turbo-celsius")',
        "",
        ".. note::",
        "",
        "   Many styles have units in their colorbar labels (e.g. °C, m/s).",
        "   These styles will attempt to automatically convert the units of",
        "   your data to match the style's units.",
        "",
        ".. raw:: html",
        "",
        "   <style>",
        "   .ek-search-wrap {",
        "     margin-bottom: 1.5em;",
        "   }",
        "   #ek-search {",
        "     width: 100%;",
        "     max-width: 480px;",
        "     padding: 6px 10px;",
        "     font-size: 0.95em;",
        "     border: 1px solid #ccc;",
        "     border-radius: 4px;",
        "     box-sizing: border-box;",
        "   }",
        "   #ek-search-count {",
        "     margin-top: 4px;",
        "     font-size: 0.85em;",
        "     color: #666;",
        "   }",
        "   .ek-section { }",
        "   .ek-section-heading { }",
        "   .ek-style-block { }",
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
        '   <div class="ek-search-wrap">',
        '     <input id="ek-search" type="search" placeholder="Search by style name, parameter name, short name, standard name…" oninput="ekFilter()">',
        '     <div id="ek-search-count"></div>',
        "   </div>",
        "   <script>",
        '   var EK_COPY_SVG = \'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg>\';',
        '   var EK_CHECK_SVG = \'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 12l5 5l10 -10" /></svg>\';',
        "   function ekCopy(btn, text) {",
        "     navigator.clipboard.writeText(text).then(function() {",
        "       btn.innerHTML = EK_CHECK_SVG + ' Style name copied';",
        "       setTimeout(function() {",
        "         btn.innerHTML = EK_COPY_SVG + ' Copy this style name';",
        "       }, 1500);",
        "     });",
        "   }",
        "   function ekFilter() {",
        "     var q = document.getElementById('ek-search').value.toLowerCase().trim();",
        "     var blocks = document.querySelectorAll('.ek-style-block');",
        "     var sections = document.querySelectorAll('.ek-section');",
        "     var total = 0, shown = 0;",
        "     blocks.forEach(function(block) {",
        "       total++;",
        "       var terms = (block.dataset.search || '').toLowerCase();",
        "       var match = !q || terms.indexOf(q) !== -1;",
        "       block.style.display = match ? '' : 'none';",
        "       if (match) shown++;",
        "     });",
        "     sections.forEach(function(sec) {",
        "       var visible = Array.from(sec.querySelectorAll('.ek-style-block')).some(function(b) {",
        "         return b.style.display !== 'none';",
        "       });",
        "       sec.style.display = visible ? '' : 'none';",
        "     });",
        "     var countEl = document.getElementById('ek-search-count');",
        "     if (q) {",
        "       countEl.textContent = shown + ' of ' + total + ' styles match';",
        "     } else {",
        "       countEl.textContent = '';",
        "     }",
        "   }",
        "   </script>",
        "",
    ]

    from earthkit.plots import styles as _styles
    from earthkit.plots.styles import levels as _levels_mod

    copy_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1'
        " 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1"
        ' -2.667 -2.667z" />'
        '<path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2'
        ' -2h10c.75 0 1.158 .385 1.5 1" /></svg>'
    )

    for file_id, style_entries in sections.items():
        section_title = _section_title(file_id)

        rst_lines += [
            ".. raw:: html",
            "",
            '   <div class="ek-section">',
            f'   <h2 class="ek-section-heading">{section_title}</h2>',
            "",
        ]

        for e in style_entries:
            name = e["name"]
            style_dict = e["style_dict"]
            search_terms = e.get("search_terms", set())
            slug = _style_slug(name)
            img_filename = f"{slug}.png"
            img_path = os.path.join(images_dir, img_filename)
            img_rst_path = f"_static/styles/{img_filename}"

            # data-search: style name + file_id + all identity terms (space-separated)
            all_terms = {name, file_id} | search_terms
            data_search = " ".join(sorted(all_terms))

            name_html = (
                f'<div class="ek-style-entry">'
                f'<div class="ek-style-left">'
                f'<code class="ek-style-name">{name}</code>'
                f"</div>"
                f'<button class="ek-copy-btn" onclick="ekCopy(this, \'{name}\')">'
                f"{copy_svg} Copy this style name"
                f"</button>"
                f"</div>"
            )
            block_open = f'<div class="ek-style-block" data-search="{data_search}">{name_html}'
            block_close = "</div>"

            style_obj = _make_style_object(style_dict)
            is_contour = isinstance(style_obj, _styles.Contour)
            is_vector = isinstance(style_obj, _styles.Vector)
            preview_levels = _make_preview_levels(style_obj)
            is_dynamic = preview_levels is not None

            try:
                if is_contour:
                    _save_contour_sample(style_obj, img_path)
                elif is_vector:
                    _save_vector_sample(style_obj, img_path)
                else:
                    if is_dynamic:
                        orig_levels = style_obj._levels
                        style_obj._levels = _levels_mod.Levels(levels=preview_levels)
                    try:
                        _save_colorbar(style_obj, img_path)
                    finally:
                        if is_dynamic:
                            style_obj._levels = orig_levels

                alt = (
                    "contour line sample" if is_contour else "vector style sample" if is_vector else "colorbar preview"
                )
                rst_lines += [
                    ".. raw:: html",
                    "",
                    f"   {block_open}",
                    "",
                    f".. image:: {img_rst_path}",
                    f"   :alt: {alt}",
                    "",
                ]
                if is_dynamic:
                    rst_lines += [
                        "*(Levels are determined from data at plot time)*",
                        "",
                    ]
                rst_lines += [".. raw:: html", "", f"   {block_close}", ""]

            except ValueError as exc:
                msg = (
                    "*(Levels are determined from data at plot time)*"
                    if "dynamic levels" in str(exc)
                    else f"*(Preview unavailable: {exc})*"
                )
                rst_lines += [
                    ".. raw:: html",
                    "",
                    f"   {block_open}",
                    "",
                    msg,
                    "",
                    ".. raw:: html",
                    "",
                    f"   {block_close}",
                    "",
                ]
            except Exception as exc:
                rst_lines += [
                    ".. raw:: html",
                    "",
                    f"   {block_open}",
                    "",
                    f"*(Preview unavailable: {exc})*",
                    "",
                    ".. raw:: html",
                    "",
                    f"   {block_close}",
                    "",
                ]

        rst_lines += [".. raw:: html", "", "   </div>", ""]

    rst_content = "\n".join(rst_lines) + "\n"

    out_rst = os.path.join(docs_dir, "styles-gallery.rst")
    with open(out_rst, "w") as f:
        f.write(rst_content)

    print(f"[styles gallery] wrote {out_rst}")
    print(f"[styles gallery] wrote {len(entries)} colorbar images to {images_dir}")


if __name__ == "__main__":
    generate()

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
Generate the named-domains gallery RST page and map preview images.

Called automatically by conf.py at the start of every Sphinx build.
Images are cached: an existing PNG is only re-rendered when the earthkit-plots
version string changes (written to a sentinel file beside the images).

The output is a single RST page with:
  - a "category" <select> (Countries / Built-in regions)
  - a "name" <select> that repopulates when the category changes
  - a <img> tag whose src is swapped by inline JS
  - one pre-rendered PNG per domain in docs/_static/domains/
"""

import os
import sys
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Make the package importable when run directly from docs/
_here = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_here, "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _images_dir(docs_dir):
    out = os.path.join(docs_dir, "_static", "domains")
    os.makedirs(out, exist_ok=True)
    return out


def _sentinel_path(images_dir):
    return os.path.join(images_dir, ".cache-version")


def _current_version():
    try:
        from earthkit.plots import __version__
        return __version__
    except Exception:
        return "unknown"


def _cache_is_valid(images_dir):
    sentinel = _sentinel_path(images_dir)
    if not os.path.exists(sentinel):
        return False
    with open(sentinel) as f:
        return f.read().strip() == _current_version()


def _write_sentinel(images_dir):
    with open(_sentinel_path(images_dir), "w") as f:
        f.write(_current_version())


def _slug(name):
    """Return a filesystem-safe filename stem."""
    s = name.lower()
    for ch in ' /\\:*?"<>|(){}[]\',.':
        s = s.replace(ch, "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def _list_countries():
    """
    Return a sorted list of country name strings from the Natural Earth
    admin_0_countries 110m shapefile.
    """
    import cartopy.io.shapereader as shpreader

    shpfilename = shpreader.natural_earth(
        resolution="110m", category="cultural", name="admin_0_countries"
    )
    reader = shpreader.Reader(shpfilename)
    names = []
    for record in reader.records():
        name = record.attributes.get("NAME_LONG") or ""
        name = name.replace("\x00", "").strip()
        if name:
            names.append(name)
    return sorted(set(names))


def _list_builtin_regions(countries):
    """
    Return a sorted list of domain names from domains.yml that are NOT
    also Natural Earth country names.
    """
    import yaml

    domains_yml = os.path.join(_src, "earthkit", "plots", "data", "geo", "domains.yml")
    with open(domains_yml) as f:
        data = yaml.safe_load(f)

    country_names_lower = {c.lower() for c in countries}
    regions = []
    for name in data.get("domains", {}):
        if name.lower() not in country_names_lower:
            regions.append(name)
    return sorted(regions)


def _render_domain(name, filepath):
    """
    Render a map for *name* and save it to *filepath*.
    Returns True on success, or an error string on failure.
    """
    import earthkit.plots as ekp

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            chart = ekp.Map(domain=name)
            chart.standard_layers()
            chart.title(f"{name}  |  {{crs}}")
            fig = chart.fig
            fig.savefig(filepath, dpi=90, bbox_inches="tight")
            plt.close(fig)
            return True
        except Exception as exc:
            plt.close("all")
            return str(exc)


# ---------------------------------------------------------------------------
# RST / HTML generation
# ---------------------------------------------------------------------------

_RST_HEADER = """\
.. _domains-gallery:

Named domains
=============

Any of the names below can be passed as the ``domain`` argument to any
earthkit-plots map function.

Use the dropdowns below to preview the map extent and default projection
chosen automatically for each domain, along with the code snippet to reproduce it.

.. raw:: html

"""

# {category_options}  — <option> tags for the category selector
# {countries_options} — <option> tags for the countries sub-selector
# {regions_options}   — <option> tags for the built-in regions sub-selector
_HTML_TEMPLATE = """\
   <style>
   #ek-domain-wrap {{ margin-bottom: 1.5em; }}
   .ek-domain-row {{
     display: flex; gap: 0.75em; align-items: center;
     flex-wrap: wrap; margin-bottom: 0.6em;
   }}
   .ek-domain-label {{
     font-size: 0.9em; color: #555; white-space: nowrap;
   }}
   .ek-domain-sel {{
     padding: 6px 10px; font-size: 0.95em;
     border: 1px solid #ccc; border-radius: 4px;
     min-width: 200px;
   }}
   #ek-domain-img-wrap {{ margin-top: 1em; }}
   #ek-domain-img {{
     max-width: 100%; border: 1px solid #ddd; border-radius: 4px;
   }}
   #ek-domain-error {{
     color: #a00; font-size: 0.9em; margin-top: 0.5em; display: none;
   }}
   #ek-domain-code-wrap {{
     position: relative; margin-top: 1.2em;
   }}
   #ek-domain-code {{
     background: #2b2b2b; border: 1px solid #444; color: #d4d4d4;
     border-radius: 4px; padding: 0.8em 1em; font-family: monospace;
     font-size: 1.1em; white-space: pre; margin: 0;
   }}
   #ek-domain-code .ek-str {{ color: #e06c75; }}
   #ek-domain-code .ek-eq  {{ color: #c792ea; }}
   #ek-domain-copy {{
     position: absolute; top: 0.5em; right: 0.5em;
     width: 1.1em; height: 1.1em; cursor: pointer; opacity: 0.4;
     background: none; border: none; padding: 0; filter: invert(1);
   }}
   #ek-domain-copy:hover {{ opacity: 0.9; }}
   </style>
   <div id="ek-domain-wrap">
     <div class="ek-domain-row">
       <span class="ek-domain-label">Category:</span>
       <select id="ek-cat-select" class="ek-domain-sel" onchange="ekCatSwap(this)">
         <option value="countries">Countries</option>
         <option value="regions">Other regions</option>
       </select>
     </div>
     <div class="ek-domain-row">
       <span class="ek-domain-label">Domain:</span>
       <select id="ek-domain-select" class="ek-domain-sel" onchange="ekDomainSwap(this)">
       </select>
     </div>
     <div id="ek-domain-img-wrap">
       <img id="ek-domain-img" src="" alt="">
       <div id="ek-domain-error"></div>
     </div>
     <div id="ek-domain-code-wrap">
       <pre id="ek-domain-code"></pre>
       <img id="ek-domain-copy" src="_static/copy.svg" alt="Copy" title="Copy" onclick="ekCopyCode()">
     </div>
   </div>
   <script>
   var EK_DOMAIN_BASE = '_static/domains/';
   var EK_LISTS = {{
     countries: [
{countries_options}
     ],
     regions: [
{regions_options}
     ]
   }};
   function ekPopulate(category) {{
     var sel = document.getElementById('ek-domain-select');
     sel.innerHTML = '';
     EK_LISTS[category].forEach(function(item) {{
       var opt = document.createElement('option');
       opt.value = item.name;
       opt.dataset.slug = item.slug;
       opt.textContent = item.name;
       sel.appendChild(opt);
     }});
   }}
   function ekDomainSwap(sel) {{
     if (!sel || !sel.options.length) return;
     var slug = sel.options[sel.selectedIndex].dataset.slug;
     var name = sel.value;
     var img = document.getElementById('ek-domain-img');
     var err = document.getElementById('ek-domain-error');
     var code = document.getElementById('ek-domain-code');
     img.src = EK_DOMAIN_BASE + slug + '.png';
     img.alt = name;
     err.style.display = 'none';
     img.onerror = function() {{
       err.textContent = 'Map preview unavailable for: ' + name;
       err.style.display = '';
     }};
     var s = '<span class="ek-str">';
     var e = '</span>';
     var q = '<span class="ek-eq">=</span>';
     var esc = name.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
     code.innerHTML = 'import earthkit.plots as ekp\\n\\nchart ' + q + ' ekp.Map(domain' + q + s + '"' + esc + '"' + e + ')\\nchart.standard_layers()\\nchart.title(' + s + '"{{domain}} | {{crs}}"' + e + ')\\nchart.show()';
   }}
   function ekCopyCode() {{
     var text = document.getElementById('ek-domain-code').textContent;
     navigator.clipboard.writeText(text).then(function() {{
       var btn = document.getElementById('ek-domain-copy');
       btn.src = '_static/check.svg';
       btn.alt = 'Copied';
       setTimeout(function() {{ btn.src = '_static/copy.svg'; btn.alt = 'Copy'; }}, 1500);
     }});
   }}
   function ekCatSwap(catSel) {{
     ekPopulate(catSel.value);
     ekDomainSwap(document.getElementById('ek-domain-select'));
   }}
   // Initialise on page load.
   (function() {{
     ekPopulate('countries');
     ekDomainSwap(document.getElementById('ek-domain-select'));
   }})();
   </script>

"""


def _js_list(names):
    """Render a list of names as JS object literals for EK_LISTS."""
    lines = []
    for name in names:
        lines.append(f'      {{name: "{name}", slug: "{_slug(name)}"}}')
    return ",\n".join(lines)


def _build_rst(countries, regions):
    html = _HTML_TEMPLATE.format(
        countries_options=_js_list(countries),
        regions_options=_js_list(regions),
    )
    return _RST_HEADER + html


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate(docs_dir=None):
    """
    Generate domain map images and the RST domains gallery page.

    Parameters
    ----------
    docs_dir : str, optional
        Path to the ``docs/`` directory.  Defaults to the directory that
        contains this script.
    """
    if docs_dir is None:
        docs_dir = os.path.dirname(os.path.abspath(__file__))

    images_dir = _images_dir(docs_dir)
    cache_valid = _cache_is_valid(images_dir)

    countries = _list_countries()
    regions = _list_builtin_regions(countries)
    all_domains = countries + regions

    print(f"[domains gallery] {len(countries)} countries, {len(regions)} built-in regions")

    rendered = 0
    skipped = 0
    failed = []

    for name in all_domains:
        filepath = os.path.join(images_dir, f"{_slug(name)}.png")

        if cache_valid and os.path.exists(filepath):
            skipped += 1
            continue

        result = _render_domain(name, filepath)
        if result is True:
            rendered += 1
        else:
            failed.append((name, result))

    if rendered > 0 or not cache_valid:
        _write_sentinel(images_dir)

    print(f"[domains gallery] rendered {rendered}, skipped {skipped} (cached), failed {len(failed)}")
    if failed:
        for name, err in failed:
            print(f"[domains gallery]   FAILED: {name!r}: {err}")

    rst_path = os.path.join(docs_dir, "domains-gallery.rst")
    with open(rst_path, "w") as f:
        f.write(_build_rst(countries, regions))

    print(f"[domains gallery] wrote {rst_path}")


if __name__ == "__main__":
    generate()

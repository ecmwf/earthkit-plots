# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import datetime

on_rtd = os.environ.get("READTHEDOCS") == "True"

# earthkit-data defaults to cache-policy "off", so every notebook re-downloads
# its data on every run, which is the dominant cost of the docs build. Enable a
# persistent "user" cache in a fixed directory and export it via the
# EARTHKIT_DATA_* environment variables (which take precedence over settings),
# so it is inherited by the notebook kernels nbsphinx spawns. Notebooks sharing
# the same url/cds product then download it only once per build (and across
# builds where the cache directory is preserved).
os.environ.setdefault("EARTHKIT_DATA_CACHE_POLICY", "user")
os.environ.setdefault(
    "EARTHKIT_DATA_USER_CACHE_DIRECTORY",
    os.path.join(os.path.expanduser("~"), ".cache", "earthkit-data-docs"),
)

# Anchor paths to this file's directory (the Sphinx source dir,
# ``docs/source``) rather than the current working directory, so the build is
# robust to where sphinx-build is invoked from.
_conf_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _conf_dir)

import generate_domains_page  # noqa: E402
import generate_styles_page  # noqa: E402

if on_rtd:
    version = os.environ.get("READTHEDOCS_VERSION", "latest")
    release = version
else:
    version = "dev"
    release = "dev"

rtd_version = version if version != "latest" else "develop"
rtd_version_type = os.environ.get("READTHEDOCS_VERSION_TYPE", "branch")

if rtd_version_type in ("branch", "tag"):
    source_branch = rtd_version
else:
    source_branch = "main"


# Branch for upstream earthkit repo (used for fetching earthkit-packages.yml)
# Tags will use main
if rtd_version_type in ("tag"):
    ek_branch = "main"
# Pull requests and unknmown versions will use develop
# Not sure how you get unknown, but its a valid value of rtd_version_type
elif rtd_version_type in ("external", "unknown"):
    ek_branch = "develop"
else:
    ek_branch = rtd_version

# -- Styles gallery generation -----------------------------------------------


# Defined unconditionally (not just when the galleries below run), because the
# notebook exclude_patterns logic further down also relies on it.
_docs_dir = os.path.dirname(os.path.abspath(__file__))
generate_styles_page.generate(docs_dir=_docs_dir)
generate_domains_page.generate(docs_dir=_docs_dir)

# -- Project information -----------------------------------------------------

sys.path.insert(0, os.path.join(_conf_dir, "..", "..", "src"))

project = "earthkit-plots"
copyright = f"{datetime.datetime.now().year}, European Centre for Medium-Range Weather Forecasts (ECMWF)"
author = "European Centre for Medium-Range Weather Forecasts (ECMWF)"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Automatically extracts documentation from your Python docstrings
    "sphinx.ext.autodoc",
    # Supports Google-style and NumPy-style docstrings
    "sphinx.ext.napoleon",
    # Renders LaTeX math in HTML using MathJax
    "sphinx.ext.mathjax",
    # Option to click viewcode
    "sphinx.ext.viewcode",
    # Links to the documentation of other projects via cross-references
    "sphinx.ext.intersphinx",
    # Generates summary tables for modules/classes/functions, and (with
    # autosummary_generate = True and the :toctree: option) a separate stub
    # page per class/function -- the numpy-style API layout.
    "sphinx.ext.autosummary",
    # Allows citing BibTeX bibliographic entries in reStructuredText
    "sphinxcontrib.bibtex",
    # Tests snippets in documentation by running embedded Python examples
    # "sphinx.ext.doctest",
    # Checks documentation coverage of the codebase
    # "sphinx.ext.coverage",
    # Adds .nojekyll file and helps configure docs for GitHub Pages hosting
    # "sphinx.ext.githubpages",
    # Adds "Edit on GitHub" links to documentation pages
    # "edit_on_github",
    # Adds "Edit on GitHub" links to documentation pages
    # "sphinx_github_style",
    # Option to link to code
    # "sphinx.ext.linkcode",
    # Automatically includes type hints from function signatures into the documentation
    # "sphinx_autodoc_typehints",
    # Integrates Jupyter Notebooks into Sphinx
    "nbsphinx",
    # Simplifies linking to external resources with short aliases
    "sphinx.ext.extlinks",
    # Enables responsive grid layouts and card components (homepage grid cards)
    "sphinx_design",
]

# Generate a stub .rst file for every object listed in an autosummary
# directive that uses the :toctree: option. This is what gives each class and
# function its own dedicated documentation page (as in the numpy docs), rather
# than dumping a whole module onto a single page.
autosummary_generate = True

# Document class members on the class's own page (matches the numpy layout).
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}

# Notebook outputs are committed to version control (the nbstripout pre-commit
# hook has been removed), so do not execute notebooks at build time -- render
# their stored outputs instead. This keeps the docs build fast and independent
# of network data sources. Re-run the notebooks locally and commit their
# outputs whenever the examples change.
nbsphinx_execute = "never"

# Execute every notebook with the python3 kernel regardless of the kernel name
# baked into its metadata. Notebooks are often saved with a local environment's
# kernel name (e.g. "develop"), which does not exist on ReadTheDocs and causes
# nbsphinx to fail with NoSuchKernel.
nbsphinx_kernel_name = "python3"

# GitHub links configuration
extlinks = {
    "pr": ("https://github.com/ecmwf/earthkit-plots/pull/%s", "PR #%s"),
    "issue": ("https://github.com/ecmwf/earthkit-plots/issues/%s", "Issue #%s"),
}

nbsphinx_thumbnails = {
    "examples/examples/introduction/01-introduction": "_static/thumbnails/01-introduction.png",
    "examples/examples/introduction/02-input-output-formats": "_static/thumbnails/02-input-output-formats.png",
    "examples/examples/introduction/03-api-layers": "_static/thumbnails/03-api-layers.png",
    "examples/examples/introduction/04-layouts": "_static/thumbnails/04-layouts.png",
    "examples/examples/introduction/05-styles": "_static/thumbnails/05-styles.png",
    "examples/examples/introduction/06-metadata-formatting": "_static/thumbnails/06-metadata-formatting.png",
    "examples/examples/introduction/07-domains": "_static/thumbnails/07-domains.png",
    "examples/examples/introduction/08-unit-conversion": "_static/thumbnails/08-unit-conversion.png",
    "examples/examples/source-types/source-grib": "_static/thumbnails/source-grib.png",
    "examples/examples/source-types/source-netcdf": "_static/thumbnails/source-netcdf.png",
    "examples/examples/source-types/source-numpy": "_static/thumbnails/source-numpy.png",
    "examples/examples/source-types/source-xarray": "_static/thumbnails/source-xarray.png",
    "examples/examples/string-formatting-units": "_static/string-formatting-units.png",
    "examples/examples/vectors/vectors-basic-barbs": "_static/thumbnails/vectors-basic-barbs.png",
    "examples/examples/vectors/vectors-basic-quiver": "_static/thumbnails/vectors-basic-quiver.png",
    "examples/examples/vectors/vectors-streamplot": "_static/thumbnails/vectors-streamplot.png",
    "examples/examples/vectors/vectors-subsampling": "_static/thumbnails/vectors-subsampling.png",
    "examples/examples/vectors/vectors-regridding": "_static/thumbnails/vectors-regridding.png",
    "examples/examples/vectors/vectors-styles": "_static/thumbnails/vectors-styles.png",
    "examples/examples/grid-types/grid-types-healpix": "_static/thumbnails/grid-types-healpix.png",
    "examples/examples/grid-types/grid-types-reduced-gg": "_static/thumbnails/grid-types-reduced-gg.png",
    "examples/examples/grid-types/grid-types-regular-ll": "_static/thumbnails/grid-types-regular-ll.png",
    "examples/examples/grid-types/grid-types-orca": "_static/thumbnails/grid-types-orca.png",
    "examples/examples/contour/contour-introduction": "_static/thumbnails/contour-introduction.png",
    "examples/examples/contour/contour-styles": "_static/thumbnails/contour-styles.png",
    "examples/examples/contour/contour-linestyles": "_static/thumbnails/contour-linestyles.png",
    "examples/examples/contour/contour-spaghetti": "_static/thumbnails/contour-spaghetti.png",
    "examples/examples/contourf/contourf-introduction": "_static/thumbnails/contourf-introduction.png",
    "examples/examples/contourf/contourf-styles": "_static/thumbnails/contourf-styles.png",
    "examples/examples/contourf/contourf-contour-overlay": "_static/thumbnails/contourf-contour-overlay.png",
    "examples/examples/misc/rgb-composite": "_static/thumbnails/rgb-composite.png",
    "examples/examples/misc/choropleth": "_static/thumbnails/choropleth.png",
    "examples/examples/points-and-cells/point-cloud": "_static/thumbnails/point-cloud.png",
    "examples/examples/points-and-cells/grid-points": "_static/thumbnails/grid-points.png",
    "examples/examples/points-and-cells/grid-cells": "_static/thumbnails/grid-cells.png",
    "examples/examples/points-and-cells/scatter": "_static/thumbnails/scatter.png",
    "examples/examples/resampling/resampling-bilinear": "_static/thumbnails/resampling-bilinear.png",
    "examples/examples/resampling/resampling-nearest-neighbour": "_static/thumbnails/resampling-nearest-neighbour.png",
    "examples/examples/resampling/resampling-regrid": "_static/thumbnails/resampling-regrid.png",
    "examples/examples/resampling/resampling-subsample": "_static/thumbnails/resampling-subsample.png",
    "examples/examples/time-series/timeseries-introduction": "_static/thumbnails/timeseries-introduction.png",
    "examples/examples/time-series/timeseries-climate-stripes": "_static/thumbnails/timeseries-climate-stripes.png",
    "examples/examples/time-series/timeseries-multibox": "_static/thumbnails/timeseries-multibox.png",
}

# intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "cartopy": ("https://cartopy.readthedocs.io/stable/", None),
    "earthkit": ("https://earthkit.readthedocs.io/en/latest/", None),
    "earthkit-data": ("https://earthkit-data.readthedocs.io/en/latest/", None),
    "earthkit-geo": ("https://earthkit-geo.readthedocs.io/en/latest/", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/_*.ipynb"]

# Only the notebooks covered by the notebook test suite (see `make
# notebook-tests`) are executed at build time. Those tests run notebooks nested
# at least two directories deep under examples/ and gallery/, so the build
# excludes the un-tested notebooks living directly in the top level of docs/,
# examples/examples/ and examples/gallery/. The hand-written gallery index
# pages (examples.ipynb, gallery.ipynb) are markdown-only and are kept, as they
# form the toctree entry points for the example and gallery sections.
import glob  # noqa: E402

_KEEP_NOTEBOOKS = {"examples.ipynb", "gallery.ipynb"}
for _pattern in (
    "*.ipynb",
    "examples/examples/*.ipynb",
    "examples/gallery/*.ipynb",
):
    for _path in glob.glob(os.path.join(_docs_dir, _pattern)):
        if os.path.basename(_path) in _KEEP_NOTEBOOKS:
            continue
        exclude_patterns.append(os.path.relpath(_path, _docs_dir))


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


html_theme = "furo"

html_static_path = ["_static"]

html_favicon = "./_static/earthkit-plots-notext.svg"

html_css_files = [
    "custom.css",
]

html_js_files = [
    "earthkit-packages.js",  # generated from earthkit-packages.yml at build time
    "custom.js",
]

bibtex_bibfiles = ["references.bib"]

html_theme_options = {
    "light_css_variables": {
        "color-sidebar-background": "#131320",
        # "color-background-primary": "", # leave as default to avoid overriding the light theme background
        "color-sidebar-link-text": "#ffffff",
        "color-sidebar-brand-text": "#ffffff",
        "color-sidebar-caption-text": "#ffffff",
        "color-brand-primary": "#FCE54B",
        "color-brand-content": "#5f8dd3",
        "color-sidebar-item-background--hover": "#001F3F",
        "color-sidebar-item-expander-background--hover": "#001F3F",
    },
    "dark_css_variables": {
        "color-sidebar-background": "#131320",
        "color-background-primary": "#131320",
        "color-sidebar-link-text": "#ffffff",
        "color-sidebar-brand-text": "#ffffff",
        "color-sidebar-caption-text": "#ffffff",
        "color-brand-primary": "#FCE54B",
        "color-brand-content": "#5f8dd3",
        "color-sidebar-item-background--hover": "#001F3F",
        "color-sidebar-item-expander-background--hover": "#001F3F",
    },
    "light_logo": "earthkit-plots-dark.svg",
    "dark_logo": "earthkit-plots-dark.svg",
    "source_repository": "https://github.com/ecmwf/earthkit-plots/",
    "source_branch": source_branch,
    "source_directory": "docs/source",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/ecmwf/earthkit-plots",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}


_EARTHKIT_PACKAGES_URL = (
    "https://raw.githubusercontent.com/ecmwf/earthkit/refs/heads/develop/docs/earthkit-packages.yml"
)

def _write_earthkit_packages_js(app):
    """Fetch earthkit-packages.yml from remote and write a JS data file into the output _static dir.

    Falls back to the local copy if the remote fetch fails.
    """
    try:
        with urllib.request.urlopen(_EARTHKIT_PACKAGES_URL, timeout=10) as response:
            config = yaml.safe_load(response.read())
    except Exception:
        config_path = os.path.join(os.path.dirname(__file__), "earthkit-packages.yml")
        with open(config_path, encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
    packages = config.get("packages", [])
    static_dir = os.path.join(app.outdir, "_static")
    os.makedirs(static_dir, exist_ok=True)
    js_path = os.path.join(static_dir, "earthkit-packages.js")
    with open(js_path, "w", encoding="utf-8") as fh:
        fh.write(f"window.earthkitPackages = {json.dumps(packages)};\n")


# The high-level API namespaces (ekp.geo, ekp.timeseries, ekp.climatology) are
# singleton instances of private classes (_GeoNamespace, ...). We document them
# via ``.. autoclass:: _GeoNamespace`` so their methods are auto-discovered (no
# hand-maintained method list), but the user-facing name is the *instance*, e.g.
# ``ekp.geo``. The two hooks below rewrite the rendered class signature so the
# private class name is replaced with the public ``earthkit.plots.geo`` name and
# the spurious ``class`` prefix / empty ``()`` argument list are dropped.
_NAMESPACE_CLASS_TO_PUBLIC = {
    "_GeoNamespace": "earthkit.plots.geo",
    "_TimeSeriesNamespace": "earthkit.plots.timeseries",
    "_ClimatologyNamespace": "earthkit.plots.climatology",
}


def _blank_namespace_signature(app, what, name, obj, options, signature, return_annotation):
    """Drop the ``(...)`` argument list from the namespace class signatures."""
    if what == "class" and name.rsplit(".", 1)[-1] in _NAMESPACE_CLASS_TO_PUBLIC:
        return ("", None)
    return None


def _rename_namespace_signatures(app, doctree, docname):
    """Rewrite the rendered namespace class name to its public ``ekp.*`` form."""
    from docutils import nodes
    from sphinx import addnodes

    for sig in doctree.findall(addnodes.desc_signature):
        ids = sig.get("ids", [])
        cls = next(
            (
                _NAMESPACE_CLASS_TO_PUBLIC[i.rsplit(".", 1)[-1]]
                for i in ids
                if i.rsplit(".", 1)[-1] in _NAMESPACE_CLASS_TO_PUBLIC
            ),
            None,
        )
        if cls is None:
            continue
        # Drop the leading "class " annotation (desc_annotation) and the module
        # prefix (desc_addname), then set the name to the public dotted path.
        for child in list(sig.children):
            if isinstance(child, (addnodes.desc_annotation, addnodes.desc_addname)):
                sig.remove(child)
        for name_node in sig.findall(addnodes.desc_name):
            name_node.children = [nodes.Text(cls)]
            break


def setup(app):
    from earthkit_packages import _write_earthkit_packages_js
    app.connect("builder-inited", lambda app: _write_earthkit_packages_js(app, ek_branch))
    app.connect("autodoc-process-signature", _blank_namespace_signature)
    app.connect("doctree-resolved", _rename_namespace_signatures)

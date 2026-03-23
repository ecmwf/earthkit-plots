# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

on_rtd = os.environ.get("READTHEDOCS") == "True"
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("."))

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
# -- Styles gallery generation -----------------------------------------------


_docs_dir = os.path.dirname(os.path.abspath(__file__))
generate_styles_page.generate(docs_dir=_docs_dir)

# -- Project information -----------------------------------------------------

sys.path.insert(0, os.path.abspath("../../src"))

project = "earthkit-plots"
copyright = "2025, European Centre for Medium-Range Weather Forecasts (ECMWF)"
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
    # Generates summary tables for modules/classes/functions
    # "sphinx.ext.autosummary",
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
]

# GitHub links configuration
extlinks = {
    "pr": ("https://github.com/ecmwf/earthkit-plots/pull/%s", "PR #%s"),
    "issue": ("https://github.com/ecmwf/earthkit-plots/issues/%s", "Issue #%s"),
}

nbsphinx_thumbnails = {
    "examples/examples/introduction/01-introduction": "_static/thumbnails/01-introduction.png",
    "examples/examples/introduction/02-api-layers": "_static/thumbnails/02-api-layers.png",
    "examples/examples/introduction/06-domains": "_static/thumbnails/06-domains.png",
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
    "examples/examples/contour/contour-introduction": "_static/thumbnails/contour-introduction.png",
    "examples/examples/contour/contour-styles": "_static/thumbnails/contour-styles.png",
    "examples/examples/contour/contour-linestyles": "_static/thumbnails/contour-linestyles.png",
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
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


html_theme = "furo"

html_static_path = ["_static"]

html_css_files = [
    "custom.css",
]

bibtex_bibfiles = ["references.bib"]

html_theme_options = {
    "light_mode_only": True,
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

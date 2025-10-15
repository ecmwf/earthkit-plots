# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Import and path setup ---------------------------------------------------

import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("../"))

from earthkit.plots.version import __version__  # noqa: E402

# -- Project information -----------------------------------------------------


project = "earthkit-plots"
copyright = f"2022-{datetime.datetime.now().strftime('%Y')}, European Centre for Medium Range Weather Forecasts"
author = "European Centre for Medium Range Weather Forecasts"
version = __version__
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "autoapi.extension",
]

# autodoc configuration
autodoc_typehints = "none"

# autoapi configuration
autoapi_dirs = ["../src/earthkit/"]
autoapi_ignore = [
    "*/version.py",
    "sphinxext/*",
    "*/data/*",
    "*/healpix.py",
    "*/reduced_gg.py",
]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
    "inherited-members",
]
autoapi_root = "_api"
autoapi_member_order = "alphabetical"
autoapi_add_toctree_entry = False

# GitHub links configuration
extlinks = {
    "pr": ("https://github.com/ecmwf/earthkit-plots/pull/%s", "PR #%s"),
    "issue": ("https://github.com/ecmwf/earthkit-plots/issues/%s", "Issue #%s"),
}

# GitHub links configuration
extlinks = {
    "pr": ("https://github.com/ecmwf/earthkit-plots/pull/%s", "PR #%s"),
    "issue": ("https://github.com/ecmwf/earthkit-plots/issues/%s", "Issue #%s"),
}

nbsphinx_thumbnails = {
    "examples/examples/string-formatting-units": "_static/string-formatting-units.png",
}

# napoleon configuration
# napoleon_google_docstring = False
# napoleon_numpy_docstring = True
# napoleon_preprocess_types = True

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
    "earthkit-regrid": ("https://earthkit-regrid.readthedocs.io/en/latest/", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_logo = "https://raw.githubusercontent.com/ecmwf/logos/refs/heads/main/logos/earthkit/earthkit-plots-dark.svg"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

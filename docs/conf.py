# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Import and path setup ---------------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "earthkit-plots"
copyright = "2023, European Centre for Medium Range Weather Forecasts"
author = "European Centre for Medium Range Weather Forecasts"
version = "0.0.0"  # earthkit.plots.__version__
release = "0.0.0"  # earthkit.plots.__version__

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
autoapi_add_toctree_entry = True

nbsphinx_thumbnails = {
    "examples/examples/string-formatting-units": "_static/string-formatting-units.png",
}

# napoleon configuration
# napoleon_google_docstring = False
# napoleon_numpy_docstring = True
# napoleon_preprocess_types = True

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

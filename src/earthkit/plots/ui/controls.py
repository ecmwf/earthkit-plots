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

"""Widget factories for the Explorer control panel.

Each public function returns an ``ipywidgets`` widget (or container) and a
``value`` property that the Explorer can read to get the current selection.
Country and projection lists are loaded lazily on first use so importing this
module does not trigger any I/O.
"""

import functools

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader


# --- Projection catalogue ---------------------------------------------------

# Projections offered in the CRS dropdown, grouped by rough category.
# Each entry is (display_label, cartopy_class, default_kwargs).
PROJECTIONS = [
    ("Auto",                       None,                     {}),
    ("Plate Carrée",               ccrs.PlateCarree,         {}),
    ("Mercator",                   ccrs.Mercator,            {}),
    ("Miller Cylindrical",         ccrs.Miller,              {}),
    ("Lambert Cylindrical",        ccrs.LambertCylindrical,  {}),
    ("Mollweide",                  ccrs.Mollweide,           {}),
    ("Robinson",                   ccrs.Robinson,            {}),
    ("Sinusoidal",                 ccrs.Sinusoidal,          {}),
    ("Albers Equal Area",          ccrs.AlbersEqualArea,     {}),
    ("Lambert Conformal Conic",    ccrs.LambertConformal,    {}),
    ("Azimuthal Equidistant",      ccrs.AzimuthalEquidistant, {}),
    ("Stereographic",              ccrs.Stereographic,       {}),
    ("North Polar Stereographic",  ccrs.NorthPolarStereo,    {}),
    ("South Polar Stereographic",  ccrs.SouthPolarStereo,    {}),
    ("Orthographic",               ccrs.Orthographic,        {}),
    ("Nearside Perspective",       ccrs.NearsidePerspective, {}),
    ("Transverse Mercator",        ccrs.TransverseMercator,  {}),
    ("OSGB",                       ccrs.OSGB,                {}),
    ("EuroPP",                     ccrs.EuroPP,              {}),
]

# Map from display label → (class, kwargs) for fast lookup.
PROJECTION_MAP = {label: (cls, kw) for label, cls, kw in PROJECTIONS}

PROJECTION_LABELS = [label for label, _, _ in PROJECTIONS]


# --- Domain catalogue -------------------------------------------------------

# Preset named domains (Global + continental regions from the domain lookup).
_PRESET_DOMAINS = None


def preset_domains():
    """Return the sorted list of preset domain names (Global + continents).

    Loaded lazily from the earthkit-plots ancillary domain lookup.

    Returns
    -------
    list of str
    """
    global _PRESET_DOMAINS
    if _PRESET_DOMAINS is None:
        from earthkit.plots.ancillary import load
        data = load("domains", data_type="geo")
        _PRESET_DOMAINS = sorted(data["domains"].keys())
    return _PRESET_DOMAINS


# Natural Earth country list, grouped by continent.
_COUNTRIES_BY_CONTINENT = None


@functools.lru_cache(maxsize=1)
def countries_by_continent():
    """Return ``{continent: [country_name, ...]}`` from Natural Earth 110m data.

    Loaded once and cached.  Countries are sorted alphabetically within each
    continent; continents are sorted alphabetically.

    Returns
    -------
    dict of str → list of str
    """
    shpfile = shpreader.natural_earth(
        resolution="110m", category="cultural", name="admin_0_countries"
    )
    reader = shpreader.Reader(shpfile)

    grouped = {}
    for record in reader.records():
        name = record.attributes.get("NAME_LONG", "") or ""
        name = name.replace("\x00", "").strip()
        continent = record.attributes.get("CONTINENT", "") or "Other"
        continent = continent.replace("\x00", "").strip()
        if name:
            grouped.setdefault(continent, []).append(name)

    return {k: sorted(v) for k, v in sorted(grouped.items())}


# Human-readable continent names shown in the Domain Type dropdown.
# "Seven seas" is renamed to something friendlier; Antarctica is kept.
def continent_display_name(raw):
    """Return a user-facing label for a Natural Earth continent string.

    Parameters
    ----------
    raw : str
        The raw ``CONTINENT`` attribute value from Natural Earth.

    Returns
    -------
    str
    """
    return {
        "Seven seas (open ocean)": "Open Ocean",
    }.get(raw, raw)


# --- Widget builders --------------------------------------------------------

def domain_selector(initial_type="Global", initial_domain="Global", widgets=None):
    """Return a ``(type_dropdown, domain_dropdown, get_domain)`` triple.

    The two dropdowns are linked: changing the type repopulates the domain
    list.  ``get_domain()`` returns the currently selected domain name as a
    string suitable for passing to ``Map(domain=...)``.

    Parameters
    ----------
    initial_type : str, optional
        Starting value for the Domain Type dropdown.
    initial_domain : str, optional
        Starting value for the Domain dropdown.
    widgets : module, optional
        The ``ipywidgets`` module.  Imported internally if not supplied.

    Returns
    -------
    tuple of (widget, widget, callable)
    """
    if widgets is None:
        import ipywidgets as widgets

    _continents = list(countries_by_continent().keys())
    _continent_labels = [continent_display_name(c) for c in _continents]

    type_options = ["Global", "Continent/Region", "Country"]
    type_w = widgets.Dropdown(
        options=type_options,
        value=initial_type,
        description="Domain type:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="auto"),
    )

    def _domain_options_for(domain_type):
        if domain_type == "Global":
            return ["Global"]
        if domain_type == "Continent/Region":
            # Preset named domains minus "Global" (already in its own category).
            return [d for d in preset_domains() if d != "Global"]
        # Country: all countries grouped under their continent label.
        options = []
        for raw_continent in sorted(countries_by_continent()):
            label = continent_display_name(raw_continent)
            for country in countries_by_continent()[raw_continent]:
                options.append(country)
        return options

    initial_options = _domain_options_for(initial_type)
    initial_value = initial_domain if initial_domain in initial_options else initial_options[0]

    domain_w = widgets.Dropdown(
        options=initial_options,
        value=initial_value,
        description="Domain:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="auto"),
    )

    def on_type_change(change):
        new_options = _domain_options_for(change["new"])
        domain_w.options = new_options
        domain_w.value = new_options[0]

    type_w.observe(on_type_change, names="value")

    def get_domain():
        val = domain_w.value
        return None if val == "Global" else val

    return type_w, domain_w, get_domain


def projection_selector(initial="Auto", widgets=None):
    """Return a ``(dropdown, get_crs)`` pair.

    ``get_crs()`` returns a cartopy CRS instance, or ``None`` for "Auto".

    Parameters
    ----------
    initial : str, optional
        Starting label (must be in ``PROJECTION_LABELS``).
    widgets : module, optional
        The ``ipywidgets`` module.  Imported internally if not supplied.

    Returns
    -------
    tuple of (widget, callable)
    """
    if widgets is None:
        import ipywidgets as widgets

    w = widgets.Dropdown(
        options=PROJECTION_LABELS,
        value=initial if initial in PROJECTION_LABELS else "Auto",
        description="Projection:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="auto"),
    )

    def get_crs():
        cls, kwargs = PROJECTION_MAP[w.value]
        return None if cls is None else cls(**kwargs)

    return w, get_crs

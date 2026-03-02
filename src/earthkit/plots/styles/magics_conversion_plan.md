# Plan: Expanding `styles/magics.py` to cover all Magics ECMWF styles

## Context

This plan is for an agent working in the `earthkit-plots` repository at
`src/earthkit/plots/styles/magics.py`. The goal is to expand this module so
that the ~196 Magics parameter JSON files and their ~576 named styles (found at
`/Users/mavj/magics/share/magics/styles/ecmwf/`) can all be converted to
earthkit-plots `Style` objects and, where appropriate, written out as
earthkit-plots YAML files.

---

## Magics data structure — what you are reading

### Parameter files (`2t.json`, `msl.json`, etc.)

Each file is a JSON **list** of one or more entries. Each entry has:

```json
{
  "eccharts_layer": "2t",
  "prefered_units": "C",
  "styles": ["sh_all_fM48t56i4", "ct_red_i2_dash", ...],
  "match": [
    {"paramId": "167", "shortName": "2t"},
    {"long_name": "2 metre temperature"},
    {"standard_name": "air_temperature"}
  ]
}
```

- `eccharts_layer` — the short layer ID (used as `id` in earthkit-plots YAML)
- `prefered_units` — Magics unit string for this parameter (e.g. `"C"`, `"hPa"`)
- `styles` — ordered list of style names to look up in `styles.json`
- `match` — list of metadata criterion dicts (maps directly to earthkit-plots
  identity `criteria`)

The `match` criteria use these keys: `paramId`, `shortName`, `centre`,
`originatingCentre`, `long_name`, `standard_name`, `level`, `levelist`,
`levtype`, `type`, `param`, `channel`, `functionCode`.

There are also **scaling files** (e.g. `scaling_celsius.json`) that have
no `eccharts_layer` or `styles`, only `prefered_units` + `match`. These define
unit preferences for additional paramIds and should be used to supplement the
identity files.

### `styles.json`

A flat dict of `{ style_name: style_dict }` with ~576 entries. Each style dict
is a flat set of Magics contouring parameters. The key patterns are:

**1. Shaded fill — explicit colour list (`contour_shade_colour_method: "list"`)**
This is by far the most common (~388 of 576):
```json
{
  "contour_shade": "on",
  "contour_shade_colour_method": "list",
  "contour_shade_colour_list": "rgb(0,0,0.5)/blue_purple/greenish_blue/...",
  "contour_shade_method": "area_fill",
  "contour_level_selection_type": "interval",
  "contour_interval": 4,
  "contour_shade_min_level": -48,
  "contour_shade_max_level": 56
}
```
Colour list is `/`-separated. Each colour is one of:
- `rgb(r,g,b)` where values are **0–255 integers** (note: **not** 0–1 floats
  as the current `magics_color` function assumes for `rgb()`!)
- `rgba(r,g,b,a)` with similar 0–255 integers + alpha 0–1
- `hsl(h,s,l)` where h is degrees (0–360), s and l are 0–1
- Magics named colours like `blue_purple`, `greenish_blue`, `red`, etc.

**⚠ IMPORTANT BUG**: The current `magics_color` function parses `rgb()` values
as 0–1 floats, but Magics colour lists use **0–255 integers** for rgb/rgba.
Fix this: divide r, g, b by 255 when parsing `rgb(...)` and `rgba(...)`.

**2. Contour lines only (no shade)**  (~99 styles):
```json
{
  "contour_level_selection_type": "interval",
  "contour_interval": 2,
  "contour_line_colour": "red",
  "contour_line_style": "dash",
  "contour_label": "on"
}
```
These should produce earthkit-plots `Contour` style objects (not `Style`).

**3. Gradients (1 style — `www_2t`)**:
```json
{
  "contour_shade_colour_method": "gradients",
  "contour_gradients_colour_list": "rgb(5,64,106)/white/rgb(134,25,20)",
  "contour_gradients_step_list": "15/15",
  "contour_gradients_technique": "hsl",
  "contour_gradients_waypoint_list": "-60./0/60.",
  "contour_level_list": "-80/-70/..."
}
```

**4. Palette (1 style)**:
```json
{
  "contour_shade_colour_method": "palette",
  "contour_shade_palette_name": "eccharts_white_red_7"
}
```

**5. Calculate (~8 styles)**: dynamic colour assignment — no static colour list.
These cannot be fully converted and should emit a warning, outputting a style
with no colours (earthkit-plots will use its default).

**6. Missing colour method (~36 styles)**: `contour_shade` is set but no
`contour_shade_colour_method`. Treat as `list` if `contour_shade_colour_list`
is present.

**Level selection types**:
- `"level_list"`: `contour_level_list` is a `/`-separated string of floats
- `"interval"`: use `contour_interval`, `contour_shade_min_level`,
  `contour_shade_max_level`. When both min and max are present, generate an
  explicit list via `np.arange(min, max + interval, interval)`.

---

## earthkit-plots style format — what you are writing

### `Style` constructor parameters (key ones):

```python
Style(
    colors=...,       # str (colormap name), list of RGB tuples/hex/named colors
    levels=...,       # list, range(), or Levels object
    gradients=None,   # list of ints: colors between each pair of levels
    extend="neither", # "neither"/"min"/"max"/"both"
    units=None,       # str unit string (e.g. "celsius", "hPa", "m s-1")
    units_label=None, # display override for units
    preferred_method="contourf",
)
```

`levels` in YAML can be:
- A Python-style `range(start, stop, step)` string → parsed by `Levels.from_config`
- A plain list `[-40, -38, ..., 40]`
- A dict `{"step": 4}` for dynamic/data-driven levels

### YAML auto-style file format (`auto-styles/<id>.yml`):

```yaml
id: near-surface-air-temperature
optimal: TEMPERATURE_AT_2M_IN_CELSIUS

styles:
  TEMPERATURE_AT_2M_IN_CELSIUS:
    name: temperature-2m-turbo-celsius
    type: Style
    colors: turbo
    extend: both
    levels: range(-40, 41, 2)
    units: celsius

  TEMPERATURE_AT_2M_IN_KELVIN:
    name: temperature-2m-turbo-kelvin
    type: Style
    colors: turbo
    extend: both
    levels: range(230, 311, 2)
    units: K
```

`type` must be `"Style"` or `"Contour"` (the class names in `styles/__init__.py`).

For colour lists the YAML `colors:` field accepts a list of hex strings or
RGB tuples. Use hex strings (`"#rrggbb"`) for cleanliness.

### YAML identity file format (`identities/<id>.yml`):

```yaml
id: near-surface-air-temperature

criteria:
- {paramId: 167, shortName: 2t}
- {standard_name: air_temperature}
- {long_name: 2 metre temperature}
```

Each criterion dict is one entry from the Magics `match` list. The keys map
directly — `paramId`, `shortName`, `centre`, `long_name`, `standard_name`,
`levtype`, `level`, etc.

---

## What needs to be implemented / fixed in `magics.py`

### 1. Fix the `rgb()`/`rgba()` colour parser

Current code treats `rgb()` values as 0–1 floats. Magics uses **0–255 integers**.

```python
# In magics_color(), fix the RGB branch:
elif color_name.upper().startswith("RGB("):
    rgb_values = color_name[4:-1].split(",")
    r, g, b = [float(v.strip()) for v in rgb_values]
    return (r / 255.0, g / 255.0, b / 255.0)  # divide by 255

# Add RGBA support:
elif color_name.upper().startswith("RGBA("):
    parts = color_name[5:-1].split(",")
    r, g, b, a = float(parts[0])/255, float(parts[1])/255, float(parts[2])/255, float(parts[3])
    return (r, g, b, a)
```

### 2. Add `parse_colour_list(colour_list_str)` helper

Parse a `/`-separated Magics colour list string into a list of matplotlib colours:

```python
def parse_colour_list(colour_list_str: str) -> list:
    """Parse a Magics '/' separated colour list string."""
    return [magics_color(c.strip()) for c in colour_list_str.split("/")]
```

This is already partially done in `_convert_colors` but should be a
standalone helper since it's used in multiple paths.

### 3. Fix `_convert_levels` for interval+min+max case

When `contour_level_selection_type == "interval"` and both
`contour_shade_min_level` and `contour_shade_max_level` are present,
generate an explicit level list (already done correctly in the existing code).
Also handle `contour_min_level`/`contour_max_level` (used in contour-only
styles, e.g. `ct_red_i2_dash`) as fallback bounds.

### 4. Determine `extend` correctly

The current `_convert_extend` only checks for `contour_shade_min/max_level_colour`.
A better heuristic: if `contour_shade_min_level` (or `contour_min_level`) is
present and `contour_shade_max_level` (or `contour_max_level`) is present,
infer `extend="both"`. If only one side is bounded, infer `"min"` or `"max"`.
When neither bound is specified, default to `"both"` for shaded styles (since
Magics implicitly extends).

### 5. Add `to_yaml_dict(style_name, magics_params, units=None)` function

Returns a dict suitable for embedding in the `styles:` block of an
auto-styles YAML:

```python
def to_yaml_dict(style_key: str, magics_params: dict, units: str = None) -> dict:
    """
    Convert a single Magics style dict to an earthkit-plots YAML style entry dict.
    Returns a dict with keys: name, type, colors, levels, extend, units, etc.
    """
```

This is the main building block for the YAML generator below.

### 6. Add `convert_parameter_file(param_file_path, styles_dict)` function

Reads one Magics parameter JSON file and returns the data needed to write
both an auto-styles YAML and an identity YAML:

```python
def convert_parameter_file(param_file_path: str, styles_dict: dict) -> dict:
    """
    Convert one Magics parameter JSON file.

    Returns a dict with:
      {
        "id": str,                   # eccharts_layer value
        "prefered_units": str,       # Magics preferred units string
        "criteria": list[dict],      # from 'match' list
        "styles": list[dict],        # list of to_yaml_dict() results
        "optimal": str,              # key of the first/default style
      }
    """
```

`styles_dict` is the already-loaded `styles.json` dict.

### 7. Add `generate_yaml_files(magics_ecmwf_dir, output_dir)` function

The top-level batch converter:

```python
def generate_yaml_files(magics_ecmwf_dir: str, output_dir: str) -> None:
    """
    Convert all Magics ECMWF parameter JSON files to earthkit-plots YAML files.

    Writes:
      <output_dir>/auto-styles/<id>.yml
      <output_dir>/identities/<id>.yml

    Parameters
    ----------
    magics_ecmwf_dir : str
        Path to /path/to/magics/share/magics/styles/ecmwf/
    output_dir : str
        Path to the earthkit-plots data/styles/ directory, i.e.
        src/earthkit/plots/data/styles/
    """
```

Steps inside:
1. Load `styles.json` once.
2. Glob all `*.json` files except `styles.json`.
3. Skip files without an `eccharts_layer` field (scaling files like
   `scaling_celsius.json` define unit preferences but not styles — skip for now
   or handle separately).
4. For each param file, call `convert_parameter_file()`.
5. Write the auto-styles YAML and identity YAML using `yaml.dump()`.
6. Print a summary of what was written vs. skipped.

---

## Unit string mapping

Magics `prefered_units` strings need mapping to earthkit-plots / pint-compatible
unit strings. Add a dict:

```python
MAGICS_UNITS_TO_EK = {
    "C": "celsius",
    "K": "K",
    "F": "fahrenheit",
    "hPa": "hPa",
    "Pa": "Pa",
    "m": "m",
    "mm": "mm",
    "cm": "cm",
    "dam": "dam",
    "km": "km",
    "m/s": "m s-1",
    "m s-1": "m s-1",
    "kg/m2": "kg m-2",
    "kg m-2": "kg m-2",
    "J/kg": "J kg-1",
    "m3/s": "m3 s-1",
    "%": "percent",
    # add more as encountered
}
```

---

## Style key naming convention

When generating YAML style keys (the all-caps identifiers like
`TEMPERATURE_AT_2M_IN_CELSIUS`) from Magics style names, use:

```
{eccharts_layer.upper()}_{style_name.upper()}
```

e.g. `2t` + `sh_all_fM48t56i4` → `2T_SH_ALL_FM48T56I4`

For the `name:` field (the user-facing style name), generate a slug from the
eccharts_layer and key parts of the style name:

```
{eccharts_layer}-{short_descriptor}
```

where `short_descriptor` is derived from the style dict's
`contour_legend_text` or `contour_title` field (lowercased, spaces→hyphens,
stripped of parentheses). If neither is present, fall back to the style key
slug.

---

## Colour output format

Convert all Magics colours to hex strings for the YAML `colors:` list.
Matplotlib's `to_hex()` handles RGB tuples neatly:

```python
import matplotlib.colors as mcolors

def to_hex(color) -> str:
    if color is None:
        return "#00000000"  # transparent
    return mcolors.to_hex(color, keep_alpha=True)
```

---

## What to skip / warn about

- Styles with `contour_shade_colour_method: "calculate"` — emit a warning,
  write a minimal style entry with no `colors:` key.
- Styles with `contour_shade_method: "dot"` or `"hatch"` — no equivalent in
  earthkit-plots; warn and skip the shading, write a contour-only style.
- Param files with no `eccharts_layer` (scaling files) — skip silently or
  handle in a separate pass.
- Palette names other than `eccharts_white_red_7` — attempt
  `MAGICS_PALETTE_TO_MPL` lookup; warn if not found.

---

## Summary of files to modify

- **`src/earthkit/plots/styles/magics.py`** — all changes go here:
  - Fix `rgb()`/`rgba()` parsing (0–255 integers)
  - Add `parse_colour_list()`
  - Fix `_convert_levels()` for contour min/max fields
  - Improve `_convert_extend()`
  - Add `MAGICS_UNITS_TO_EK` mapping dict
  - Add `to_yaml_dict()`
  - Add `convert_parameter_file()`
  - Add `generate_yaml_files()`
  - Add `to_hex()` helper

No other files need to change for the conversion tool itself. The output YAML
files are written into `src/earthkit/plots/data/styles/auto-styles/` and
`src/earthkit/plots/data/styles/identities/`, which are already part of the
earthkit-plots plugin system and will be picked up automatically.

---

## Quick test

After implementing, a sanity check:

```python
from earthkit.plots.styles.magics import generate_yaml_files
generate_yaml_files(
    magics_ecmwf_dir="/Users/mavj/magics/share/magics/styles/ecmwf",
    output_dir="src/earthkit/plots/data/styles",
)
```

Then verify:
```python
import earthkit.plots
print(earthkit.plots.list_styles())  # should include many new names
style = earthkit.plots.load_style("2t-sh-all-fm48t56i4")  # or whatever name is generated
```

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


def list_to_human(iterable, conjunction="and", oxford_comma=False):
    """
    Convert an iterable to a human-readable string.

    Parameters
    ----------
    iterable : list or tuple
        The list of strings to convert to a single natural language string.
    conjunction : str, optional
        The conjunction with which to join the last two elements of the list,
        for example "and" (default).
    oxford_comma : bool, optional
        If `True`, an "Oxford comma" will be added before the conjunction when
        there are three or more elements in the list. Default is `False`.

    Returns
    -------
    str

    Example
    -------
    >>> list_to_human(["sausage", "egg", "chips"])
    'sausage, egg and chips'
    """
    list_of_strs = [str(item) for item in iterable]

    if len(list_of_strs) > 2:
        list_of_strs = [", ".join(list_of_strs[:-1]), list_of_strs[-1]]
        if oxford_comma:
            list_of_strs[0] += ","

    return f" {conjunction} ".join(list_of_strs)


def split_camel_case(string):
    """
    Split a CamelCase string into its constituent words.

    Parameters
    ----------
    string : str
        The string to split by camel case words.

    Returns
    -------
    list

    Example
    -------
    >>> split_camel_case("ACamelCaseString")
    ['A', 'Camel', 'Case', 'String']
    """
    import re

    matches = re.finditer(
        ".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)",
        string,
    )
    return [m.group(0) for m in matches]


def magnitude_string_from_components(u_name, v_name):
    """
    Create a magnitude string from vector component names.

    Identifies and removes U/V component indicators from the names to extract
    the underlying physical quantity. Handles various naming conventions including
    both slugified (underscores) and regular (spaces/hyphens) formats.

    Parameters
    ----------
    u_name : str
        The name of the U component.
    v_name : str
        The name of the V component.

    Returns
    -------
    str
        The magnitude string with component indicators removed.

    Examples
    --------
    >>> magnitude_string_from_components("U component of wind", "V component of wind")
    'wind'
    >>> magnitude_string_from_components("u_component_of_wind", "v_component_of_wind")
    'wind'
    >>> magnitude_string_from_components(
    ...     "10m u-component of wind", "10m v-component of wind"
    ... )
    '10m wind'
    >>> magnitude_string_from_components(
    ...     "10m_u_component_of_wind", "10m_v_component_of_wind"
    ... )
    '10m wind'
    >>> magnitude_string_from_components("eastward_wind", "northward_wind")
    'wind'
    """
    import re

    if not u_name or not v_name:
        return "magnitude"

    # Convert to lowercase for comparison
    u_lower = u_name.lower()
    v_lower = v_name.lower()

    # Use [_\s-]+ to match any combination of underscores, spaces, or hyphens
    SEP = r"[_\s-]+"

    patterns = [
        # "U component of X" / "u_component_of_X" -> "X"
        # Also handles "X u component of Y" -> "X Y"
        (rf"(.+?){SEP}[uv]{SEP}component{SEP}of{SEP}(.+)", r"\1 \2"),
        # "u component of X" with no prefix -> "X"
        (rf"^[uv]{SEP}component{SEP}of{SEP}(.+)", r"\1"),
        # "X U component" / "X_u_component" -> "X"
        (rf"(.+?){SEP}[uv]{SEP}component$", r"\1"),
        # "eastward_X" / "northward_X" (with underscore/hyphen/space) -> "X"
        (rf"(?:eastward|northward){SEP}(.+)", r"\1"),
        # "eastwardX" / "northwardX" (no separator) -> "X"
        (r"^(?:eastward|northward)(.+)", r"\1"),
        # "X eastward" / "X northward" / "X_eastward" -> "X"
        (rf"(.+?){SEP}(?:eastward|northward)$", r"\1"),
        # "uX" / "vX" where X is digits (like u10, v10) -> "wind speed"
        (r"^[uv](\d+)$", r"wind speed"),
        # "Xu" / "Xv" where X is digits (like 10u, 10v) -> "wind speed"
        (r"^(\d+)[uv]$", r"wind speed"),
    ]

    magnitude = None
    for pattern, replacement in patterns:
        match_u = re.search(pattern, u_lower)
        match_v = re.search(pattern, v_lower)

        if match_u and match_v:
            # Extract the magnitude part from both components
            magnitude_u = re.sub(pattern, replacement, u_lower).strip()
            magnitude_v = re.sub(pattern, replacement, v_lower).strip()

            # Check if both give the same result
            if magnitude_u == magnitude_v:
                magnitude = magnitude_u
                break

    # If no pattern matched, try simple prefix/suffix removal
    if magnitude is None:
        # Normalise separators for comparison (convert to underscores)
        u_norm = re.sub(r"[_\s-]+", "_", u_lower).strip("_")
        v_norm = re.sub(r"[_\s-]+", "_", v_lower).strip("_")

        # Remove leading 'u' or 'v'
        if u_norm.startswith("u_") and v_norm.startswith("v_"):
            u_stripped = u_norm[2:]
            v_stripped = v_norm[2:]
            if u_stripped == v_stripped and u_stripped:
                magnitude = u_stripped
        # Remove trailing '_u' or '_v'
        elif u_norm.endswith("_u") and v_norm.endswith("_v"):
            u_stripped = u_norm[:-2]
            v_stripped = v_norm[:-2]
            if u_stripped == v_stripped and u_stripped:
                magnitude = u_stripped

    # Clean up the result
    if magnitude:
        # Replace underscores/hyphens with spaces
        magnitude = re.sub(r"[_-]+", " ", magnitude)
        # Remove multiple spaces (including leading/trailing)
        magnitude = re.sub(r"\s+", " ", magnitude).strip()

    if not magnitude:
        # If we couldn't extract a common name, use both component names
        magnitude = f"{u_name} and {v_name}"

    return magnitude

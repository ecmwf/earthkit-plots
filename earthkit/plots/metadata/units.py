import re

_NO_CF_UNITS = False
try:
    import cf_units
except ImportError:
    _NO_CF_UNITS = True


MAPPABLE_UNITS = {
    "celsius": "°C",
    "degrees_celsius": "°C",
    "degrees_c": "°C",
    "farenheit": "°F",
    "degrees_farenheit": "°F",
    "degrees_f": "°F",
}


def superscript(in_string):
    return f"<sup>{in_string}</sup>"


def subscript(in_string):
    return f"<sub>{in_string}</sub>"


def pretty_units(units):
    multiplicands = []
    for multiplicand in units.split(" "):
        dividends = []
        for dividend in multiplicand.split("/"):
            exponentiations = []
            for exponentiation in re.findall(r"[^\W\d_]+|\^?_?-?\d+|.", dividend):
                modifier = superscript
                # Handle sub/superscript definition using "_" or "^"
                if len(exponentiation) > 1:
                    if exponentiation.startswith("_"):
                        modifier = subscript
                        exponentiation = exponentiation.replace("_", "")
                    elif exponentiation.startswith("^"):
                        exponentiation = exponentiation.replace("^", "")

                # modify exponent/subscript
                if (
                    exponentiation.replace("-", "").replace("+", "").isnumeric()
                    and exponentiations
                ):
                    exponentiation = modifier(exponentiation)
                exponentiations.append(exponentiation)
            dividends.append("".join(exponentiations))
        multiplicands.append("/".join(dividends))
    units = " ".join(multiplicands)

    for unit in MAPPABLE_UNITS:
        if unit in units:
            units = units.replace(unit, MAPPABLE_UNITS[unit])

    return units


def convert(data, source_units, target_units):
    if _NO_CF_UNITS:
        raise ImportError("cf-units is required for unit conversion")
    return cf_units.Unit(source_units).convert(data, target_units)


def convert_dataset_units(data, target_units):
    if data.__class__.__name__ == "Dataset":
        for var in list(data.data_vars):
            if isinstance(target_units, dict):
                if var not in target_units:
                    continue
                else:
                    data[var] = convert_dataarray_units(data[var], target_units[var])
            else:
                data[var] = convert_dataarray_units(data[var], target_units)
    else:
        data = convert_dataarray_units(data, target_units)
    return data


def convert_dataarray_units(data, target_units):
    source_units = data.attrs.get("units")
    if source_units is None:
        raise ValueError(f"No units found in data; cannot convert to '{target_units}'")
    new_values = convert(data.values, source_units, target_units)
    data.values = new_values
    data.attrs["units"] = target_units
    return data

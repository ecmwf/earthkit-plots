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

import numpy as np

from earthkit.plots.schemas import schema


def auto_range(data, divergence_point=None, n_levels=schema.default_style_levels):
    """
    Generate a suitable range of levels for arbitrary input data.

    Parameters
    ----------
    data : numpy.ndarray or xarray.DataArray or earthkit.data.core.Base
        The data for which to generate a list of levels.
    divergence_point : float, optional
        If provided, force the levels to be centered on this point. Useful for
        parameters that use diverging colors in their style, such as anomalies.
    n_levels : int, optional
        The target number of levels to generate (default is 10).

    Returns
    -------
    list
        A list of levels spaced across the data range with easy-to-interpret intervals.
    """
    if hasattr(data, "to_numpy"):
        data = data.to_numpy()

    min_value = np.nanmin(data)
    max_value = np.nanmax(data)

    if np.isnan(min_value) or min_value == max_value:
        return [0] * (n_levels + 1)

    if divergence_point is not None:
        max_diff = max(
            abs(max_value - divergence_point), abs(divergence_point - min_value)
        )
        min_value, max_value = divergence_point - max_diff, divergence_point + max_diff

    data_range = max_value - min_value
    step_candidates = [1, 2, 5, 10]
    magnitude = 10 ** np.floor(np.log10(data_range / n_levels))

    best_levels = None
    min_diff = float("inf")

    for step_factor in step_candidates:
        step = step_factor * magnitude
        levels = np.arange(
            np.floor(min_value / step) * step,
            np.ceil(max_value / step) * step + step,
            step,
        )
        diff = abs(len(levels) - n_levels)
        if diff < min_diff:
            best_levels = levels
            min_diff = diff

    return best_levels.tolist()


def step_range(data, step, reference=None):
    """
    Generate a range of levels for some data based on a level step and multiple.

    Parameters
    ----------
    data : numpy.ndarray or xarray.DataArray or earthkit.data.core.Base
        The data for which to generate a list of levels.
    step : float
        The step/difference between each level in the desired level range.
    reference : float, optional
        The reference point around which to calibrate the level range. For
        example, if a `step` of 4 is used and a `reference` of 2 is used, then
        the generated levels will be generated as steps of 4 above and below
        the number 2.

    Returns
    -------
    list
    """
    try:
        data = data.to_numpy()
    except AttributeError:
        pass

    if reference is None:
        reference = step

    min_value = np.nanmin(data)
    max_value = np.nanmax(data)

    max_modifier = reference % step
    min_modifier = max_modifier if max_modifier == 0 else step - max_modifier

    min_value = min_value - (min_value % step) - min_modifier

    levels = np.arange(min_value, max_value + step, step).tolist()
    if levels[1] <= np.nanmin(data):
        levels = levels[1:]

    return levels


def categorical_range(values):
    """
    Generate a range of levels for categorical data.

    This can be necessary to make sure that categorical data falls inside the
    correct bins, as values at the edge of a bin may not be included in the
    bin.

    Parameters
    ----------
    values : numpy.ndarray or xarray.DataArray or earthkit.data.core.Base
        The data for which to generate a list of levels.

    Returns
    -------
    list
    """
    # Ensure the values are sorted and unique
    values = sorted(set(values))

    # Calculate bin edges
    if len(values) == 1:
        # Special case for a single value, create a small bin around it
        return [values[0] - 0.1, values[0] + 0.1]

    bins = [values[0] - (values[1] - values[0]) / 2]  # First bin edge

    # Middle bin edges based on midpoints between consecutive values
    for i in range(1, len(values)):
        mid_point = (values[i] + values[i - 1]) / 2
        bins.append(mid_point)

    # Last bin edge
    bins.append(values[-1] + (values[-1] - values[-2]) / 2)

    return bins


class Levels:
    """
    Class defining levels to use with a mapping style.

    Parameters
    ----------
    levels : list, optional
        A static list of levels to always use, no matter the input data.
    step : float, optional
        The step/difference between each level in the desired level range.
    reference : float, optional
        The reference point around which to calibrate the level range. For
        example, if a `step` of 4 is used and a `reference` of 2 is used, then
        the generated levels will be generated as steps of 4 above and below
        the number 2.
    divergence_point : float, optional
        If provided, force the levels to be centred on this point. This is
        mostly useful for parameters which use diverging colors in their style,
        such as anomalies.
    """

    @classmethod
    def from_config(cls, config):
        if isinstance(config, str):
            if config.startswith("range"):
                args = (
                    int(i)
                    for i in config.replace("range(", "").replace(")", "").split(",")
                )
                kwargs = {"levels": range(*args)}
        elif isinstance(config, dict):
            kwargs = config
        else:
            kwargs = {"levels": config}
        return cls(**kwargs)

    def __eq__(self, other):
        if self._levels is not None and other is not None:
            is_self_arr = isinstance(self._levels, np.ndarray)
            is_other_arr = isinstance(other._levels, np.ndarray)
            if is_self_arr and is_other_arr:
                return np.array_equal(self._levels, other._levels)
            if is_self_arr != is_other_arr:
                return False
            return self._levels == other._levels
        return False

    def __init__(
        self,
        levels=None,
        step=None,
        reference=None,
        divergence_point=None,
        categorical=False,
    ):
        if categorical and levels is not None:
            self._levels = categorical_range(levels)
        else:
            self._levels = levels
        self._step = step
        self._reference = reference
        self._divergence_point = divergence_point
        self._categorical = categorical

    def apply(self, data):
        """
        Generate levels specific to some data.

        Parameters
        ----------
        data : numpy.ndarray or xarray.DataArray or earthkit.data.core.Base
            The data for which to generate a list of levels.

        Returns
        -------
        list
        """
        if self._levels is None:
            if self._categorical:
                return categorical_range(np.unique(data))
            if self._step is None:
                return auto_range(data, self._divergence_point)
            else:
                return step_range(data, self._step, self._reference)
        return self._levels

# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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
import plotly.graph_objects as go

from earthkit.plots.interactive import inputs

THICKEST = 0.6
THINNEST = 0.3

DEFAULT_QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]

DEFAULT_KWARGS = {
    "line_color": "#6E78FA",
    "fillcolor": "#B1B6FC",
}


@inputs.sanitise(multiplot=False)
def box(*args, quantiles=DEFAULT_QUANTILES, time_axis=0, **kwargs):
    """
    Generate a set of box plot traces based on the provided data and quantiles.

    Parameters
    ----------
    data : array-like or earthkit.data.FieldList
        The data to be plotted.

    *args : tuple
        Positional arguments passed to the plotly `go.Box` constructors.

    quantiles : list of float, optional
        A list of quantiles to calculate for the data. The default is
        [0.05, 0.25, 0.5, 0.75, 0.95]. Note that any number of quantiles
        can be provided, but the default is based on the standard five-point
        box plot.

    time_axis : int, optional
        The axis along which to calculate the quantiles. The default is 0.

    **kwargs : dict
        Additional keyword arguments passed to the `go.Box` constructor.

    Returns
    -------
    list of plotly.graph_objects.Box

    Notes
    -----
    - The width of the box plots is scaled based on the x-axis spacing.
    - Extra boxes are added for quantiles beyond the standard five-point box plot.
    - Hover information is included for quantile scatter points, showing the
      quantile value and percentage.
    """
    kwargs = {**DEFAULT_KWARGS, **kwargs}

    extra_boxes = (len(quantiles) - 5) // 2

    quantile_values = np.quantile(kwargs.pop("y"), quantiles, axis=time_axis)

    x = kwargs["x"]
    width = float(x[1] - x[0]) * 1e-06

    traces = []
    traces.append(
        go.Box(
            *args,
            lowerfence=quantile_values[0],
            upperfence=quantile_values[-1],
            q1=quantile_values[1],
            q3=quantile_values[-2],
            median=quantile_values[len(quantiles) // 2],
            width=width * (THICKEST if not extra_boxes else THINNEST),
            hoverinfo="skip",
            **kwargs,
        )
    )

    for j in range(extra_boxes):
        traces.append(
            go.Box(
                *args,
                lowerfence=quantile_values[0],
                upperfence=quantile_values[-1],
                showwhiskers=False,
                q1=quantile_values[1 + (j + 1)],
                q3=quantile_values[-2 - (j + 1)],
                median=quantile_values[len(quantiles) // 2],
                width=width * THICKEST,
                hoverinfo="skip",
                **kwargs,
            )
        )

    for y, p in zip(quantile_values, quantiles):
        traces.append(
            go.Scatter(
                y=y,
                x=kwargs["x"],
                mode="markers",
                marker={"size": 0.00001, "color": kwargs.get("line_color", "#333333")},
                hovertemplate=f"%{{y:.2f}}<extra>P<sub>{p*100:g}%</sub></extra>",
            )
        )

    return traces

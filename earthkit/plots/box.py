
import numpy as np
import plotly.graph_objects as go

from earthkit.plots import utils, inputs, times
from earthkit.plots.schemas import schema


THICKEST = 0.6
THINNEST = 0.3


@schema.box.apply()
@inputs.sanitise(multiplot=False)
def box(*args, quantiles=None, time_axis=0, **kwargs):
    quantiles = quantiles if quantiles is not None else schema.box.quantiles
    extra_boxes = (len(quantiles) - 5) // 2

    quantile_values = np.quantile(kwargs.pop("y"), quantiles, axis=time_axis)
    
    x = kwargs["x"]
    width = float(x[1]-x[0])*1e-06
    
    traces = []
    traces.append(
        go.Box(
            *args,
            lowerfence=quantile_values[0],
            upperfence=quantile_values[-1],
            q1=quantile_values[1],
            q3=quantile_values[-2],
            median=quantile_values[len(quantiles)//2],
            width=width*(THICKEST if not extra_boxes else THINNEST),
            hoverinfo='skip',
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
                q1=quantile_values[1+(j+1)],
                q3=quantile_values[-2-(j+1)],
                median=quantile_values[len(quantiles)//2],
                width=width*THICKEST,
                hoverinfo='skip',
                **kwargs,
            )
        )

    for y, p in zip(quantile_values, quantiles):
        traces.append(
            go.Scatter(
                y=y,
                x=kwargs["x"],
                mode='markers',
                marker={'size': 0.00001, 'color': kwargs.get("line_color", "#333333")},
                hovertemplate=f"%{{y:.2f}}<extra>P<sub>{p*100:g}%</sub></extra>",
            )
        )

    return traces
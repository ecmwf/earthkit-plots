
import plotly.graph_objects as go

from earthkit.plots import utils, inputs
from earthkit.plots.schemas import schema


@schema.line.apply()
@inputs.sanitise()
def line(*args, **kwargs):
    trace = go.Scatter(*args, **kwargs)
    return trace
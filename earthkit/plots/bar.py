
import plotly.graph_objects as go

from earthkit.plots import utils, inputs
from earthkit.plots.schemas import schema


@inputs.sanitise()
def bar(*args, **kwargs):
    trace = go.Bar(*args, **kwargs)
    return trace
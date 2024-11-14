import plotly.graph_objects as go

from earthkit.plots.interactive import inputs


# @schema.line.apply()
@inputs.sanitise()
def line(*args, **kwargs):
    trace = go.Scatter(*args, **kwargs)
    return trace

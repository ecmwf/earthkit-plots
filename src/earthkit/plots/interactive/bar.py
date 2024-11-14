import plotly.graph_objects as go

from earthkit.plots.interactive import inputs


@inputs.sanitise()
def bar(*args, **kwargs):
    trace = go.Bar(*args, **kwargs)
    return trace

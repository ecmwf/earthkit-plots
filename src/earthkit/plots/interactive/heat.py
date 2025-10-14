import numpy as np
import plotly.graph_objects as go
import xarray as xr


# --- Helper Functions ---
def _digitize_data(data: np.ndarray, bins: list):
    binned = np.digitize(data, bins) - 1
    return np.clip(binned, 0, len(bins) - 2)


def _create_hover_text(binned_data, bin_labels):
    hover_text = np.full(binned_data.shape, "", dtype=object)
    for i, label in enumerate(bin_labels):
        hover_text[binned_data == i] = label
    return hover_text


# --- Main Heatmap Function ---
def heatmap(
    data_array,
    *args,
    style="continuous",
    bins=None,
    bin_labels=None,
    colorscale=None,
    **kwargs,
):
    if not isinstance(data_array, xr.DataArray) or len(data_array.dims) != 2:
        return []

    y_dim, x_dim = data_array.dims
    x_coords, y_coords = (
        data_array.coords[x_dim].values,
        data_array.coords[y_dim].values,
    )
    z_values = data_array.values

    if style == "continuous":
        return go.Heatmap(
            z=z_values,
            x=x_coords,
            y=y_coords,
            colorscale=colorscale if colorscale is not None else "Viridis",
            hovertemplate="<b>Time:</b> %{x}<br><b>Level:</b> %{y}<br><b>Value:</b> %{z:.2f}<extra></extra>",
            **kwargs,
        )
    elif style == "categorical":
        if bins is None:
            bins = [0, 1, 19, 39, 59, 79, 100]
        elif isinstance(bins, int):
            data_min, data_max = np.nanmin(z_values), np.nanmax(z_values)
            bins = np.linspace(data_min, data_max, bins + 1).tolist()

        if bin_labels is None:
            bin_labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins) - 1)]

        binned_data = _digitize_data(z_values, bins)
        hover_text = _create_hover_text(binned_data, bin_labels)

        if colorscale is None:
            # Default to a sequential scale if none is provided by the user
            colorscale = "Plasma_r"

        from plotly import colors

        n_colors = len(bin_labels)

        # Sample N discrete colors from the continuous colorscale
        discrete_colors = colors.sample_colorscale(
            colorscale, np.linspace(0, 1, n_colors)
        )

        # Build the special discrete colorscale structure Plotly needs
        discrete_plotly_colorscale = []
        scale_points = np.linspace(0, 1, n_colors + 1)
        for i in range(n_colors):
            discrete_plotly_colorscale.extend(
                [
                    [scale_points[i], discrete_colors[i]],
                    [scale_points[i + 1], discrete_colors[i]],
                ]
            )

        return go.Heatmap(
            z=binned_data,
            x=x_coords,
            y=y_coords,
            colorscale=discrete_plotly_colorscale,
            text=hover_text,
            hovertemplate="<b>Time:</b> %{x}<br><b>Level:</b> %{y}<br><b>Category:</b> %{text}<extra></extra>",
            zmin=0,
            zmax=len(bin_labels) - 1,
            colorbar=dict(
                tickmode="array",
                tickvals=np.arange(len(bin_labels)),
                ticktext=bin_labels,
            ),
            **kwargs,
        )

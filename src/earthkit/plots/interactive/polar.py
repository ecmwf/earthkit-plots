import numpy as np
import pandas as pd
import plotly.graph_objects as go
import scipy.special
from scipy.interpolate import RegularGridInterpolator, splev, splprep
from scipy.spatial import ConvexHull
from scipy.stats import gaussian_kde

from . import inputs

# --- Helper functions for Hybrid Von Mises Density Calculation ---


def vonmises_kde(data: np.ndarray, kappa: float, n_bins: int = 360):
    """Performs a von Mises kernel density estimation for circular variables."""
    bins = np.linspace(0.0, 2 * np.pi, n_bins)
    x = np.linspace(0.0, 2 * np.pi, n_bins)
    kappa = min(kappa, 700)
    kde = np.exp(kappa * np.cos(x[:, None] - data[None, :])).sum(1) / (
        2 * np.pi * scipy.special.i0(kappa)
    )
    kde /= np.trapz(kde, x=bins)
    return bins, kde


def circular_var(data):
    """Basic circular variance calculation: V = 1 - R̄ = 1 - sqrt(C̄²-S̄²) = 1- sqrt(mean(cos(x))^2 + mean(sin(x))^2)"""
    mean_cos = np.mean(np.cos(data))
    mean_sin = np.mean(np.sin(data))
    r_bar = np.sqrt(mean_cos**2 + mean_sin**2)
    return 1 - r_bar


def calculate_wind_density_hybrid_vonmises_on_grid(
    speed_data,
    direction_data,
    speed_bandwidth_factor=1.0,
    num_speed_points=100,
    num_direction_points=360,
    max_speed_override=None,
):
    """Calculates a 2D hybrid KDE over wind direction (von Mises) and speed (Gaussian)."""
    speed_data, direction_data = np.asarray(speed_data), np.asarray(direction_data)
    valid = ~np.isnan(speed_data) & ~np.isnan(direction_data)
    speed_data_clean, direction_data_clean = speed_data[valid], direction_data[valid]

    direction_grid_deg = np.linspace(0, 360, num_direction_points, endpoint=False)

    if max_speed_override is not None:
        max_speed = float(max_speed_override)
    elif len(speed_data_clean) > 0:
        max_speed = float(speed_data_clean.max() * 1.2)
    else:
        max_speed = 10.0
    speed_eval_grid = np.linspace(0, max(max_speed, 1.0), num_speed_points)

    if len(speed_data_clean) == 0:
        empty = np.zeros((num_direction_points, num_speed_points))
        return empty, direction_grid_deg, speed_eval_grid

    try:
        dir_radians = np.radians(direction_data_clean)
        kappa = (
            700 if circular_var(dir_radians) < 1e-9 else 1.0 / circular_var(dir_radians)
        )
        dir_grid_rad, dir_kde = vonmises_kde(
            dir_radians, kappa, n_bins=num_direction_points
        )
        dir_density = np.interp(
            np.radians(direction_grid_deg), dir_grid_rad, dir_kde, period=2 * np.pi
        )
    except Exception as e:
        print(f"Von Mises KDE failed: {e}. Using uniform density.")
        dir_density = np.ones(num_direction_points) / num_direction_points

    try:
        speed_kde = gaussian_kde(speed_data_clean)
        if speed_bandwidth_factor != 1.0:
            speed_kde.set_bandwidth(speed_kde.factor * speed_bandwidth_factor)
        speed_density = speed_kde(speed_eval_grid)
    except Exception as e:
        print(f"Gaussian KDE failed: {e}. Using uniform density.")
        speed_density = np.ones(num_speed_points) / num_speed_points

    joint_density_map = np.outer(dir_density, speed_density)

    return joint_density_map, direction_grid_deg, speed_eval_grid


# --- Other Density Calculation Helpers ---
def _calculate_density_kde(x, y):
    xy = np.vstack([x, y])
    valid_mask = ~np.isnan(xy).any(axis=0)
    kernel = gaussian_kde(xy[:, valid_mask])
    return kernel(xy)


def _calculate_density_adaptive_kde(x, y, params=None):
    params = params or {}
    bandwidth_factor = params.get("bandwidth_factor", 0.75)
    xy = np.vstack([x, y])
    valid_mask = ~np.isnan(xy).any(axis=0)
    kernel = gaussian_kde(xy[:, valid_mask])
    kernel.set_bandwidth(bw_method=kernel.factor * bandwidth_factor)
    return kernel(xy)


def _calculate_density_hybrid_vonmises(r, theta, params=None):
    params = params or {}
    density_map, dir_grid_deg, r_grid = calculate_wind_density_hybrid_vonmises_on_grid(
        r, theta, **params
    )
    interpolator = RegularGridInterpolator(
        (dir_grid_deg, r_grid), density_map, bounds_error=False, fill_value=0
    )
    query_points = np.vstack([theta % 360, r]).T
    return interpolator(query_points)


# --- Contour Smoothing ---
def generate_smoothed_hull_contour(points, smoothing_factor=0.1, num_eval_points=100):
    if len(points) < 4:
        return np.array([]), np.array([])
    hull = ConvexHull(points)
    hull_vertices = points[hull.vertices]
    hull_vertices_closed = np.vstack([hull_vertices, hull_vertices[0]])
    x_coords, y_coords = hull_vertices_closed[:, 0], hull_vertices_closed[:, 1]
    k_spline = min(3, len(x_coords) - 1)
    if k_spline <= 0:
        return np.array([]), np.array([])
    tck, u = splprep([x_coords, y_coords], s=smoothing_factor, k=k_spline, per=True)
    u_new = np.linspace(u.min(), u.max(), num_eval_points)
    x_smooth, y_smooth = splev(u_new, tck, der=0)
    smooth_r, smooth_theta = (
        np.sqrt(x_smooth**2 + y_smooth**2),
        np.rad2deg(np.arctan2(y_smooth, x_smooth)) % 360,
    )
    return smooth_r, smooth_theta


# --- Windrose Function ---
@inputs.sanitise(axes=("r", "theta"))
def windrose(*args, colors=None, **kwargs):
    traces = []
    r_speed = kwargs.get("r")
    theta_deg = kwargs.get("theta")
    density_method = kwargs.get("density_method", "kde")
    density_params = kwargs.get("density_params")
    show_ensemble_points = kwargs.get("show_ensemble_points", False)
    show_density_blobs = kwargs.get("show_density_blobs", True)

    if colors is None:
        colors = [
            "rgba(0, 122, 204, 0.2)",
            "rgba(0, 122, 204, 0.4)",
            "rgb(0, 122, 204)",
        ]

    if show_density_blobs:
        theta_rad = np.deg2rad(theta_deg)
        x_coords, y_coords = r_speed * np.cos(theta_rad), r_speed * np.sin(theta_rad)
        if density_method == "adaptive_kde":
            density = _calculate_density_adaptive_kde(
                x_coords, y_coords, density_params
            )
        elif density_method == "hybrid_vonmises":
            density = _calculate_density_hybrid_vonmises(
                r_speed, theta_deg, density_params
            )
        elif density_method == "kde":
            density = _calculate_density_kde(x_coords, y_coords)
        else:
            raise ValueError(f"Unknown density_method: '{density_method}'")
        df_ensemble = pd.DataFrame({"x": x_coords, "y": y_coords, "density": density})
        df_sorted = df_ensemble.sort_values(by="density", ascending=False)

        regions = [
            {
                "name": "Less Likely",
                "percentage": 0.99,
                "smoothing": 0.1,
                "fillcolor": colors[0],
            },
            {
                "name": "Likely (67%)",
                "percentage": 0.67,
                "smoothing": 0.05,
                "fillcolor": colors[1],
            },
            {
                "name": "Most Likely (33%)",
                "percentage": 0.33,
                "smoothing": 0.01,
                "fillcolor": colors[2],
            },
        ]

        for region in regions:
            n_points = int(len(df_sorted) * region["percentage"])
            subset_points = df_sorted.iloc[:n_points][["x", "y"]].values
            r_smooth, theta_smooth = generate_smoothed_hull_contour(
                subset_points, region["smoothing"]
            )
            if r_smooth.size > 0:
                traces.append(
                    go.Scatterpolar(
                        r=r_smooth,
                        theta=theta_smooth,
                        mode="lines",
                        fill="toself",
                        name=region["name"],
                        fillcolor=region["fillcolor"],
                        line_width=0,
                    )
                )
    if show_ensemble_points:
        traces.append(
            go.Scatterpolar(
                r=r_speed,
                theta=theta_deg,
                mode="markers",
                name="Ensemble Members",
                marker=dict(color="rgba(100, 100, 100, 0.7)", size=5),
            )
        )
    return traces


@inputs.sanitise(axes=("r", "theta"))
def frequency(*args, radial_bins=None, n_angular_sectors=16, **kwargs):
    """
    Generates traces for a polar frequency bar chart.
    """
    r_data = kwargs.get("r")
    theta_data = kwargs.get("theta")
    df = pd.DataFrame({"r": r_data, "theta": theta_data}).dropna()

    # Angular data
    sector_width = 360.0 / n_angular_sectors
    df["theta_bin"] = (
        (df["theta"] + sector_width / 2.0) // sector_width * sector_width
    ) % 360

    # Radial data
    if radial_bins is None:
        min_val, max_val = df["r"].min(), df["r"].max()
        radial_bins = np.linspace(min_val, max_val, 6).tolist()

    radial_labels = [
        f"{radial_bins[i]:.1f}-{radial_bins[i+1]:.1f}"
        for i in range(len(radial_bins) - 1)
    ]

    df["r_bin"] = pd.cut(
        df["r"],
        bins=radial_bins,
        labels=radial_labels,
        right=False,
        include_lowest=True,
    )

    # Frequency
    freq_df = (
        df.groupby(["theta_bin", "r_bin"], observed=False)
        .size()
        .reset_index(name="frequency")
    )

    traces = []
    for r_label in radial_labels:
        subset = freq_df[freq_df["r_bin"] == r_label]

        traces.append(
            go.Barpolar(
                r=subset["frequency"],
                theta=subset["theta_bin"],
                name=r_label,
                width=sector_width * 0.9,
            )
        )

    return traces

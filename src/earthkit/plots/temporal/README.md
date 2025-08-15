# Temporal Plotting Submodule

The `temporal` submodule provides specialized plotting classes for time-based data visualization, including time series, meteograms, and other temporal plots.

## Overview

The `TimeSeries` class extends the base `Subplot` class with specialized functionality for handling temporal data:

- **Automatic time dimension detection** from xarray, pandas, and numpy data
- **Intelligent time axis configuration** with customizable formatting and frequency
- **Specialized plotting methods** for time series data
- **Integration with existing earthkit.plots infrastructure**

## Quick Start

```python
import earthkit.plots as ekp

# Create a TimeSeries subplot
ts = ekp.temporal.TimeSeries(time_frequency='M', time_format='%b %Y')

# Plot time series data (time dimension auto-detected)
ts.line(data, label='Temperature')

# Show the plot
ts.show()
```

## TimeSeries Class

### Constructor Parameters

- `row`, `column`: Position in the figure grid
- `figure`: Parent Figure object
- `size`: Subplot size (when not part of a figure)
- `time_format`: Format string for time axis labels
- `time_frequency`: Frequency for time axis ticks (e.g., 'D', 'M', 'H')
- `**kwargs`: Additional matplotlib Axes parameters

### Key Methods

#### Plotting Methods

All plotting methods support the `@plot_temporal()` decorator for automatic time handling:

- `line()`: Line plots
- `bar()`: Bar charts
- `scatter()`: Scatter plots

#### Time Axis Configuration

- `set_time_axis()`: Configure time axis formatting and highlighting
- `_detect_time_dimension()`: Auto-detect time dimensions in data
- `_configure_time_axis()`: Set up time axis with appropriate formatting

## Data Support

### Xarray DataArray/Dataset

```python
import xarray as xr

# Create sample data
dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
da = xr.DataArray(
    np.random.randn(len(dates)),
    coords={'time': dates},
    dims=['time']
)

# Plot with auto-detected time dimension
ts = ekp.temporal.TimeSeries()
ts.line(da)  # 'time' dimension automatically detected
```

### Pandas DataFrame/Series

```python
import pandas as pd

# Create sample data
df = pd.DataFrame({
    'temperature': np.random.randn(365),
    'precipitation': np.random.exponential(5, 365)
}, index=pd.date_range('2024-01-01', '2024-12-31', freq='D'))

# Plot with datetime index
ts = ekp.temporal.TimeSeries()
ts.line(df, x='index', y='temperature')
```

### Numpy Arrays with Explicit Coordinates

```python
import numpy as np

# Create sample data
dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
values = np.random.randn(len(dates))

# Plot with explicit time coordinates
ts = ekp.temporal.TimeSeries()
ts.line(values, x=dates, y=values)
```

## Time Axis Configuration

### Automatic Configuration

The `@plot_temporal()` decorator automatically:

1. Detects time dimensions in your data
1. Configures appropriate time axis formatting
1. Sets up major and minor tick marks
1. Applies time-specific styling

### Manual Configuration

```python
ts = ekp.temporal.TimeSeries()

# Set time axis properties
ts.set_time_axis(
    frequency='M',           # Monthly ticks
    format='%b %Y',         # Month Year format
    highlight={'month': 1}   # Highlight January
)

# Or configure during creation
ts = ekp.temporal.TimeSeries(
    time_frequency='D',      # Daily ticks
    time_format='%Y-%m-%d'   # YYYY-MM-DD format
)
```

### Frequency Options

- `'D'`: Daily
- `'W'`: Weekly
- `'M'`: Monthly
- `'Q'`: Quarterly
- `'Y'`: Yearly
- `'H'`: Hourly
- `'T'`: Minute

## Advanced Features

### Multiple Variables

```python
ts = ekp.temporal.TimeSeries()

# Plot multiple variables
ts.line(data1, label='Temperature')
ts.line(data2, label='Humidity')

# Add legend
ts.legend()
```

### Custom Styling

```python
ts = ekp.temporal.TimeSeries()

# Apply custom styles
ts.line(data, style=custom_style, linewidth=2, color='red')
```

### Time Highlighting

```python
ts = ekp.temporal.TimeSeries()

# Highlight specific dates
ts.set_time_axis(
    highlight={
        'month': [1, 7],     # January and July
        'day': 15            # 15th of each month
    },
    highlight_color='red'
)
```

## Integration with Figure

```python
import earthkit.plots as ekp

# Create figure with TimeSeries subplots
fig = ekp.Figure(rows=2, columns=1)

# Add TimeSeries subplots
ts1 = fig.add_timeseries(row=0, column=0, time_frequency='D')
ts2 = fig.add_timeseries(row=1, column=0, time_frequency='M')

# Plot data
ts1.line(daily_data)
ts2.line(monthly_data)

# Show figure
fig.show()
```

## Examples

See `examples/timeseries_example.py` for comprehensive examples demonstrating:

- Basic time series plotting
- Multiple variable plots
- Bar charts
- Custom time axis configuration
- Integration with different data types

## Future Enhancements

Planned features for the temporal submodule:

- **Meteogram class** for vertical time axis plots
- **Climatology plots** for seasonal patterns
- **Hovmöller diagrams** for time-latitude/longitude plots
- **Interactive time selection** and zooming
- **Time range highlighting** and annotation
- **Seasonal decomposition** plots

## Contributing

The temporal submodule is designed to be extensible. To add new temporal plot types:

1. Inherit from `TimeSeries` or create new classes
1. Use the `@plot_temporal()` decorator for time-aware methods
1. Implement appropriate time axis configuration
1. Add comprehensive documentation and examples

## Dependencies

- `matplotlib.dates` for time axis formatting
- `numpy` for data handling
- `pandas` for datetime operations (optional)
- `xarray` for multi-dimensional data (optional)

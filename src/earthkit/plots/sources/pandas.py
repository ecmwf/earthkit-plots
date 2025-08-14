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

import earthkit.data
import numpy as np
import pandas as pd

from earthkit.plots.identifiers import find_time, find_u, find_v, find_x, find_y
from earthkit.plots.sources.single import SingleSource
from earthkit.plots.utils import time_utils


class PandasSource(SingleSource):
    """
    A data source for pandas-like inputs, extending Source with additional support
    for identifying x, y, and z columns within a pandas DataFrame or Series.

    Parameters
    ----------
    dataframe : pandas.DataFrame or pandas.Series
        The pandas data to use as the source.
    x : str or array-like, optional
        The x-coordinate column name or values of the data.
    y : str or array-like, optional
        The y-coordinate column name or values of the data.
    z : str or array-like, optional
        The z-coordinate column name or values of the data.
    u : array-like, optional
        The u-component of the data.
    v : array-like, optional
        The v-component of the data.
    crs : cartopy.crs.CRS, optional
        The CRS of the data.
    style : str, optional
        The style to use when plotting the data.
    metadata : dict, optional
        Metadata to attach to this Source.
    **kwargs
        Additional metadata keys and values to attach to this Source.
    """

    def __init__(self, dataframe, x=None, y=None, z=None, **kwargs):
        # Handle pandas Series
        if isinstance(dataframe, pd.Series):
            dataframe = dataframe.to_frame()
        
        # Handle DataFrame with single column
        if isinstance(dataframe, pd.DataFrame) and len(dataframe.columns) == 1:
            if z is not None:
                # If z is specified, use that column
                dataframe = dataframe[[z]]
            else:
                # Use the single column as the main data
                pass
        
        self._pandas_source = dataframe
        super().__init__(dataframe, x=x, y=y, z=z, **kwargs)
        self._data = dataframe

        self._x_values, self._y_values, self._z_values = self._infer_xyz()

    def _infer_xyz(self):
        """Infers x, y, and z values based on pandas input columns and provided names."""
        if isinstance(self._data, pd.DataFrame):
            # Check if any of x, y, z are explicitly provided
            if self._x is not None or self._y is not None or self._z is not None:
                return self._explicit_xyz()
            else:
                return self._implicit_xyz()
        else:
            # Fall back to base Source handling if not pandas input
            return super()._infer_xyz()

    def _implicit_xyz(self):
        """Default identification of x, y and z when self._x, self._y and self._z are all None."""
        if isinstance(self._data, pd.DataFrame):
            # Get the data shape and columns
            data_shape = self._data.shape
            data_columns = list(self._data.columns)
            
            # Case 1: Single column DataFrame (1D data)
            if len(data_columns) == 1:
                col_name = data_columns[0]
                # Single column becomes y_values, index becomes x_values
                x_values = self._data.index.values
                y_values = self._data[col_name].values
                z_values = None  # No z values for 1D data
                # Set implicit coordinate names
                self._x = None  # Index, no name
                self._y = col_name
                self._z = None
                return x_values, y_values, z_values
            
            # Case 2: Two column DataFrame (2D data)
            elif len(data_columns) == 2:
                # Try to identify x and y columns using find_x and find_y
                x_col = find_x(data_columns)
                y_col = find_y(data_columns)
                
                # If identification fails, assume first column is x and second is y
                if x_col is None:
                    x_col = data_columns[0]
                if y_col is None:
                    y_col = data_columns[1]
                
                # Get column values for x and y
                x_values = self._data[x_col].values
                y_values = self._data[y_col].values
                
                # The remaining data becomes z_values (if any)
                remaining_cols = [col for col in data_columns if col not in [x_col, y_col]]
                if remaining_cols:
                    z_values = self._data[remaining_cols[0]].values
                    self._z = remaining_cols[0]
                else:
                    z_values = None
                    self._z = None
                
                # Set implicit coordinate names
                self._x = x_col
                self._y = y_col
                return x_values, y_values, z_values
            
            # Case 3: Three or more columns (3D+ data)
            else:
                # Try to identify x and y columns using find_x and find_y
                x_col = find_x(data_columns)
                y_col = find_y(data_columns)
                
                # If identification fails, assume first column is x and second is y
                if x_col is None:
                    x_col = data_columns[0]
                if y_col is None:
                    y_col = data_columns[1]
                
                # Get column values for x and y
                x_values = self._data[x_col].values
                y_values = self._data[y_col].values
                
                # The remaining columns become z_values (use first remaining as default)
                remaining_cols = [col for col in data_columns if col not in [x_col, y_col]]
                if remaining_cols:
                    z_values = self._data[remaining_cols[0]].values
                    self._z = remaining_cols[0]
                else:
                    z_values = None
                    self._z = None
                
                # Set implicit coordinate names
                self._x = x_col
                self._y = y_col
                return x_values, y_values, z_values
        else:
            # Fall back to base Source handling if not pandas input
            return super()._infer_xyz()

    def _explicit_xyz(self):
        """Handle explicit x, y, z values when any of self._x, self._y, self._z are not None."""
        if isinstance(self._data, pd.DataFrame):
            data_shape = self._data.shape
            data_columns = list(self._data.columns)
            
            # Handle 1D data with explicit x and y arguments
            if len(data_columns) == 1:
                return self._explicit_xyz_1d()
            
            # Handle 2D data with explicit x and y arguments
            elif len(data_columns) == 2:
                return self._explicit_xyz_2d()
            
            # Handle higher dimensional data
            else:
                return self._explicit_xyz_nd()
        else:
            # Fall back to base Source handling if not pandas input
            return super()._infer_xyz()

    def _explicit_xyz_1d(self):
        """Handle explicit x, y arguments for 1D data."""
        data_columns = list(self._data.columns)
        
        # Case 1: Both x and y are provided
        if self._x is not None and self._y is not None:
            x_values = self._get_column_or_array_values(self._x)
            y_values = self._get_column_or_array_values(self._y)
            z_values = None  # No z values for 1D data
            
        # Case 2: Only x is provided
        elif self._x is not None:
            x_values = self._get_column_or_array_values(self._x)
            # If x is a column name, y should be the remaining column values
            # If x is an array, y should be the column values
            if self._x in data_columns:
                # x is a column name, so y should be the remaining column values
                remaining_cols = [col for col in data_columns if col != self._x]
                if remaining_cols:
                    y_values = self._data[remaining_cols[0]].values
                    y_name = remaining_cols[0]
                else:
                    # No other columns, use index array
                    y_values = np.arange(len(x_values))
                    y_name = None
            else:
                # x is an array, so y should be the column values
                if data_columns:
                    y_values = self._data[data_columns[0]].values
                    y_name = data_columns[0]
                else:
                    y_values = np.arange(len(x_values))
                    y_name = None
            z_values = None
            
            # Set the y attribute for the implicitly identified coordinate
            if y_name is not None:
                self._y = y_name
            
        # Case 3: Only y is provided
        elif self._y is not None:
            y_values = self._get_column_or_array_values(self._y)
            # If y is a column name, x should be the remaining column values
            # If y is an array, x should be the column values
            if self._y in data_columns:
                # y is a column name, so x should be the remaining column values
                remaining_cols = [col for col in data_columns if col != self._y]
                if remaining_cols:
                    x_values = self._data[remaining_cols[0]].values
                    x_name = remaining_cols[0]
                else:
                    # No other columns, use index array
                    x_values = np.arange(len(y_values))
                    x_name = None
            else:
                # y is an array, so x should be the column values
                if data_columns:
                    x_values = self._data[data_columns[0]].values
                    x_name = data_columns[0]
                else:
                    x_values = np.arange(len(y_values))
                    x_name = None
            z_values = None
            
            # Set the x attribute for the implicitly identified coordinate
            if x_name is not None:
                self._x = x_name
            
        # Case 4: Only z is provided (unusual for 1D, but handle gracefully)
        elif self._z is not None:
            z_values = self._get_column_or_array_values(self._z)
            # For 1D data, if only z is provided, we need to infer x and y
            if len(data_columns) == 1:
                x_values = self._data.index.values
                y_values = self._data[data_columns[0]].values
            else:
                x_values = np.arange(len(z_values))
                y_values = np.arange(len(z_values))
        else:
            # This shouldn't happen given the calling logic, but handle gracefully
            raise ValueError("No explicit x, y, or z values provided")
            
        return x_values, y_values, z_values

    def _explicit_xyz_2d(self):
        """Handle explicit x, y arguments for 2D data."""
        data_columns = list(self._data.columns)
        
        # Case 1: All three (x, y, z) are provided
        if self._x is not None and self._y is not None and self._z is not None:
            x_values = self._get_column_or_array_values(self._x)
            y_values = self._get_column_or_array_values(self._y)
            z_values = self._get_column_or_array_values(self._z)
            
        # Case 2: x and y are provided, z is not
        elif self._x is not None and self._y is not None:
            x_values = self._get_column_or_array_values(self._x)
            y_values = self._get_column_or_array_values(self._y)
            # For 2D data, z values are the remaining column values
            remaining_cols = [col for col in data_columns if col not in [self._x, self._y]]
            if remaining_cols:
                z_values = self._data[remaining_cols[0]].values
            else:
                z_values = None
            
        # Case 3: Only x is provided
        elif self._x is not None:
            x_values = self._get_column_or_array_values(self._x)
            # Find y from remaining columns using identifiers
            remaining_cols = [col for col in data_columns if col != self._x]
            y_col = find_y(remaining_cols) if remaining_cols else None
            
            if y_col is None and remaining_cols:
                # If no y column found, use the first remaining column
                y_col = remaining_cols[0]
            
            if y_col:
                y_values = self._data[y_col].values
            else:
                # No other columns, use index array
                y_values = np.arange(self._data.shape[0])
            
            z_values = None
            
            # Set the y attribute for the implicitly identified coordinate
            if y_col:
                self._y = y_col
            
        # Case 4: Only y is provided
        elif self._y is not None:
            y_values = self._get_column_or_array_values(self._y)
            # Find x from remaining columns using identifiers
            remaining_cols = [col for col in data_columns if col != self._y]
            x_col = find_x(remaining_cols) if remaining_cols else None
            
            if x_col is None and remaining_cols:
                # If no x column found, use the first remaining column
                x_col = remaining_cols[0]
            
            if x_col:
                x_values = self._data[x_col].values
            else:
                # No other columns, use index array
                x_values = np.arange(self._data.shape[1])
            
            z_values = None
            
            # Set the x attribute for the implicitly identified coordinate
            if x_col:
                self._x = x_col
            
        # Case 5: Only z is provided
        elif self._z is not None:
            z_values = self._get_column_or_array_values(self._z)
            # Find x and y from columns using identifiers
            x_col = find_x(data_columns)
            y_col = find_y(data_columns)
            
            # If identifiers fail, assume first column is x and second is y
            if x_col is None:
                x_col = data_columns[0] if data_columns else None
            if y_col is None:
                y_col = data_columns[1] if len(data_columns) > 1 else None
            
            if x_col and y_col:
                x_values = self._data[x_col].values
                y_values = self._data[y_col].values
            elif x_col:
                x_values = self._data[x_col].values
                y_values = np.arange(self._data.shape[0])
            elif y_col:
                x_values = np.arange(self._data.shape[1])
                y_values = self._data[y_col].values
            else:
                # No columns found, use index arrays
                x_values = np.arange(self._data.shape[1])
                y_values = np.arange(self._data.shape[0])
            
            # Set the x and y attributes for the implicitly identified coordinates
            if x_col:
                self._x = x_col
            if y_col:
                self._y = y_col
                
        else:
            # This shouldn't happen given the calling logic, but handle gracefully
            raise ValueError("No explicit x, y, or z values provided for 2D data")
            
        return x_values, y_values, z_values

    def _explicit_xyz_nd(self):
        """Handle explicit x, y arguments for higher dimensional data."""
        data_columns = list(self._data.columns)
        
        # For higher dimensional data, we need to handle explicit x, y, z arguments
        # Case 1: All three (x, y, z) are provided
        if self._x is not None and self._y is not None and self._z is not None:
            x_values = self._get_column_or_array_values(self._x)
            y_values = self._get_column_or_array_values(self._y)
            z_values = self._get_column_or_array_values(self._z)
            
        # Case 2: x and y are provided, z is not
        elif self._x is not None and self._y is not None:
            x_values = self._get_column_or_array_values(self._x)
            y_values = self._get_column_or_array_values(self._y)
            # For higher dimensional data, z values are the remaining column values
            remaining_cols = [col for col in data_columns if col not in [self._x, self._y]]
            if remaining_cols:
                z_values = self._data[remaining_cols[0]].values
            else:
                z_values = None
            
        # Case 3: Only x is provided
        elif self._x is not None:
            x_values = self._get_column_or_array_values(self._x)
            # Find y from remaining columns using identifiers
            remaining_cols = [col for col in data_columns if col != self._x]
            y_col = find_y(remaining_cols) if remaining_cols else None
            
            if y_col is None and remaining_cols:
                # If no y column found, use the first remaining column
                y_col = remaining_cols[0]
            
            if y_col:
                y_values = self._data[y_col].values
            else:
                # No other columns, use index array
                y_values = np.arange(self._data.shape[0])
            
            z_values = None
            
            # Set the y attribute for the implicitly identified coordinate
            if y_col:
                self._y = y_col
            
        # Case 4: Only y is provided
        elif self._y is not None:
            y_values = self._get_column_or_array_values(self._y)
            # Find x from remaining columns using identifiers
            remaining_cols = [col for col in data_columns if col != self._y]
            x_col = find_x(remaining_cols) if remaining_cols else None
            
            if x_col is None and remaining_cols:
                # If no x column found, use the first remaining column
                x_col = remaining_cols[0]
            
            if x_col:
                x_values = self._data[x_col].values
            else:
                # No other columns, use index array
                x_values = np.arange(self._data.shape[1])
            
            z_values = None
            
            # Set the x attribute for the implicitly identified coordinate
            if x_col:
                self._x = x_col
            
        # Case 5: Only z is provided
        elif self._z is not None:
            z_values = self._get_column_or_array_values(self._z)
            # Find x and y from columns using identifiers
            x_col = find_x(data_columns)
            y_col = find_y(data_columns)
            
            # If identifiers fail, assume first column is x and second is y
            if x_col is None:
                x_col = data_columns[0] if data_columns else None
            if y_col is None:
                y_col = data_columns[1] if len(data_columns) > 1 else None
            
            if x_col and y_col:
                x_values = self._data[x_col].values
                y_values = self._data[y_col].values
            elif x_col:
                x_values = self._data[x_col].values
                y_values = np.arange(self._data.shape[0])
            elif y_col:
                x_values = np.arange(self._data.shape[1])
                y_values = self._data[y_col].values
            else:
                # No columns found, use index arrays
                x_values = np.arange(self._data.shape[1])
                y_values = np.arange(self._data.shape[0])
            
            # Set the x and y attributes for the implicitly identified coordinates
            if x_col:
                self._x = x_col
            if y_col:
                self._y = y_col
                
        else:
            # This shouldn't happen given the calling logic, but handle gracefully
            raise ValueError("No explicit x, y, or z values provided for higher dimensional data")
            
        return x_values, y_values, z_values

    def _get_column_or_array_values(self, name):
        """Get values for a column name or array-like value."""
        if isinstance(name, str):
            # Check if it's a column name
            if name in self._data.columns:
                return self._data[name].values
            else:
                raise ValueError(f"'{name}' not found in DataFrame columns")
        else:
            # If not a string, assume it's already an array-like value
            return np.asarray(name)

    def _axis_metadata(self, name):
        """Get metadata for a column or variable name."""
        if isinstance(name, str):
            if name in self._data.columns:
                # For pandas columns, we can extract some metadata
                col = self._data[name]
                attrs = {}
                
                # Try to get dtype information
                if hasattr(col.dtype, 'name'):
                    attrs['dtype'] = col.dtype.name
                
                # Check if it's the index
                if name == self._data.index.name:
                    attrs['is_index'] = True
                
                # Add the column name as long_name if no other metadata
                if not attrs:
                    attrs = {
                        "long_name": name,
                    }
                return attrs
            else:
                return {}
        else:
            return {}

    @property
    def x_metadata(self):
        """Returns metadata for the x coordinate."""
        return self._axis_metadata(self._x)

    @property
    def y_metadata(self):
        """Returns metadata for the y coordinate."""
        return self._axis_metadata(self._y)
    
    @property
    def z_metadata(self):
        """Returns metadata for the z coordinate."""
        return self._axis_metadata(self._z)

    @property
    def data(self):
        """Return the original pandas data, if provided."""
        return self._data

    @staticmethod
    def extract_u(data, u=None):
        """Return the u-component values of the data, if found."""
        u_data = None
        if u is not None:
            u_data = data[u]
        else:
            u_var = find_u(data.columns)
            if u_var:
                u_data = data[u_var]
        return u_data

    @staticmethod
    def extract_v(data, v=None):
        """Return the v-component values of the data, if found."""
        v_data = None
        if v is not None:
            v_data = data[v]
        else:
            v_var = find_v(data.columns)
            if v_var:
                v_data = data[v_var]
        return v_data

    @property
    def z_values(self):
        """Returns the inferred or provided z values (or color values)."""
        return self._z_values

    def metadata(self, key, default=None):
        """
        Extract metadata from the data.

        Parameters
        ----------
        key : str
            The metadata key to extract.
        default : any, optional
            The default value to return if the key is not found.
        """
        value = super().metadata(key, default)
        if value == default:
            if key in self.data.attrs:
                value = self.data.attrs[key]
            elif hasattr(self.data, key):
                value = getattr(self.data, key)
            elif hasattr(self._pandas_source, key):
                value = getattr(self._pandas_source, key)
            if hasattr(value, "values"):
                value = value.values
        return value

    @property
    def crs(self):
        """The CRS of the data."""
        if self._crs is None:
            earthkit_data = self.to_earthkit()
            try:
                self._crs = earthkit_data.projection().to_cartopy_crs()
            except ValueError:
                try:
                    self._crs = earthkit_data[0].projection().to_cartopy_crs()
                except (AttributeError, NotImplementedError):
                    self._crs = None
            except (AttributeError, NotImplementedError):
                self._crs = None
        return self._crs

    def to_earthkit(self):
        """Convert the data to an earthkit.data.core.Base object."""
        if self._earthkit_data is None:
            self._earthkit_data = earthkit.data.from_object(self._pandas_source)
        return self._earthkit_data

    def datetime(self):
        """Get the datetime of the data."""
        from datetime import datetime

        datetimes = None
        
        # Check if any column is a time column
        time_col = find_time(self.data.columns)
        if time_col is not None:
            time_series = self.data[time_col]
            if pd.api.types.is_datetime64_any_dtype(time_series):
                datetimes = [time_utils.to_pydatetime(dt) for dt in time_series]
            else:
                # Try to parse as datetime
                try:
                    parsed_times = pd.to_datetime(time_series)
                    datetimes = [time_utils.to_pydatetime(dt) for dt in parsed_times]
                except:
                    datetimes = None
        
        # Check if index is datetime
        if datetimes is None and pd.api.types.is_datetime64_any_dtype(self.data.index):
            datetimes = [time_utils.to_pydatetime(dt) for dt in self.data.index]
        
        return {
            "base_time": datetimes,
            "valid_time": datetimes,
        }

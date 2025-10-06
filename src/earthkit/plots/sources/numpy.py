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

from functools import cached_property

import numpy as np

from earthkit.plots.sources.single import SingleSource


class NumpySource(SingleSource):
    """
    A single source of data for a plot, capable of interpreting input as x, y, and z (or color) values.
    """

    def __init__(
        self,
        *args,
        x=None,
        y=None,
        z=None,
        u=None,
        v=None,
        crs=None,
        metadata=None,
        **kwargs,
    ):
        self._u = u
        self._v = v
        self._crs = crs
        self._metadata = metadata or {}
        self._metadata.update(kwargs)
        self._earthkit_data = None
        self._gridspec = None

        self._x = x
        self._y = y
        self._z = z

        self.regrid = True

        # Collect only non-None inputs into a dictionary
        inputs = self._collect_inputs(*args, x=x, y=y, z=z)
        # Infer x, y, z values from inputs
        self._x_values, self._y_values, self._z_values = self._infer_xyz(inputs)

    @cached_property
    def data(self):
        """Returns the data as a NumPy array."""
        if self.z_values is not None:
            return self.z_values
        return self.y_values

    def _infer_xyz(self, inputs):
        """Infers x, y, and z values based on inputs."""
        num_inputs = len(inputs)
        try:
            infer_pos_inputs = getattr(self, f"_infer_pos_inputs_from_{num_inputs}")
        except AttributeError:
            raise ValueError(
                f"{self.__class__.__name__} accepts at most three arguments (got {num_inputs})."
            )

        inputs = infer_pos_inputs(inputs)
        inputs = self._add_missing_arrays(inputs)
        self._check_dims(inputs)

        x, y = inputs["x"], inputs["y"]
        z = inputs.get("z", None)
        return x, y, z

    @staticmethod
    def _collect_inputs(*args, x=None, y=None, z=None):
        # bring together all inputs into a dictionary for easier manipulation
        _to_numpy = np.atleast_1d
        inputs = {i: _to_numpy(arg) for i, arg in enumerate(args)}
        for var in ("x", "y", "z"):
            value = vars()[var]
            # assume None values weren't explicitly passed in
            if value is not None:
                inputs[var] = _to_numpy(value)
        return inputs

    @staticmethod
    def _infer_pos_inputs_from_1(inputs):
        # if one positional arg passed in, assume y if 1D
        if 0 in inputs:
            new_key = "y" if inputs[0].ndim == 1 else "z"
            inputs[new_key] = inputs.pop(0)
        return inputs

    @staticmethod
    def _infer_pos_inputs_from_2(inputs):
        if 1 in inputs:
            # two postional args, assume x and y
            for idx, key in enumerate(("x", "y")):
                inputs[key] = inputs.pop(idx)
        elif 0 in inputs:
            # one positional arg - other arg must be kwarg
            # allow only x or y as the kwarg and infer the other
            # (if z passed in, unclear whether pos arg should be x or y)
            if "z" in inputs:
                raise ValueError("Ambiguously defined inputs. Pass by kwargs instead")
            key = "y" if "x" in inputs else "x"
            inputs[key] = inputs.pop(0)
        return inputs

    @staticmethod
    def _infer_pos_inputs_from_3(inputs):
        if 2 in inputs:
            # all (three) positional, assume x, y, z (in order)
            for idx, key in enumerate(("x", "y", "z")):
                inputs[key] = inputs.pop(idx)
        elif 1 in inputs:
            # two positional, one kwarg
            # check the dims can be used to unambiguously define the order
            # i.e. one is 1D, the other is 2D
            input_dims = {inputs[key].ndim for key in (0, 1)}
            if input_dims != {1, 2}:
                raise ValueError(
                    "Unable to infer positional inputs from dimensions alone"
                )
            # now safe to assign the 2D one to z
            for key in (0, 1):
                value = inputs.pop(key)
                if value.ndim == 2:
                    new_key = "z"
                else:
                    new_key = "y" if "x" in inputs else "x"
                inputs[new_key] = value
        elif 0 in inputs:
            # one positional input, two kwargs - set missing value
            missing_key = ({"x", "y", "z"} - set(inputs.keys())).pop()
            inputs[missing_key] = inputs.pop(0)
        return inputs

    @staticmethod
    def _check_dims(inputs):
        for key, value in inputs.items():
            if value.ndim not in (1, 2):
                raise ValueError(f"{key} values expected to be 1D or 2D")

        if inputs["x"].ndim != inputs["y"].ndim:
            raise ValueError("x and y values must be the same dimensionality")

        if "z" in inputs and inputs["x"].ndim == 2 and inputs["z"].ndim != 2:
            raise ValueError("z must be 2D if x and y are 2D")

    @staticmethod
    def _add_missing_arrays(inputs):
        if "z" in inputs and inputs["z"].ndim == 1:
            # don't add index arrays for 1D z data (lists of points)
            return inputs

        create_index = np.arange
        if "x" not in inputs:
            n = inputs["z"].shape[1] if "z" in inputs else len(inputs["y"])
            inputs["x"] = create_index(n)
        if "y" not in inputs:
            n = inputs["z"].shape[0] if "z" in inputs else len(inputs["x"])
            inputs["y"] = create_index(n)
        return inputs

    @property
    def _data(self):
        if self.z_values is None:
            if self.y_values is None:
                return self.x_values
            else:
                return self.y_values
        else:
            return self.z_values

    @property
    def x_values(self):
        """Returns the x values."""
        return self._x_values

    @property
    def y_values(self):
        """Returns the y values."""
        return self._y_values

    @property
    def z_values(self):
        """Returns the z values (or color values)."""
        return self._z_values

    @cached_property
    def units(self):
        """The units of the data, if specified in metadata."""
        result = self.metadata("units")
        if isinstance(result, list):
            result = result[0]
        return result

    def mutate(self):
        """
        Mutate the source with new attributes.

        Parameters
        ----------
        **kwargs
            The attributes to update.
        """
        if not self._crs and self.metadata("gridSpec", default=None) is not None:
            import earthkit.data

            from .earthkit import EarthkitSource

            m = self._metadata

            if self._x is not None and self._y is not None:
                if "latitudes" not in m and "longitudes" not in m:
                    m["latitudes"] = self._y
                    m["longitudes"] = self._x

            if self._z is not None:
                data = self._z
            else:
                data = self._data

            d = earthkit.data.ArrayField(data, metadata=m)
            return EarthkitSource(d, regrid=self.regrid)

        return self

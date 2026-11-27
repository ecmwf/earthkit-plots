# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

"""
Plotting support for the parcel computations of earthkit-meteo.

The parcel ascent, its key levels and CAPE/CIN are computed by
:func:`earthkit.meteo.thermo.surface_cape_cin`,
:func:`~earthkit.meteo.thermo.mixed_layer_cape_cin` or
:func:`~earthkit.meteo.thermo.most_unstable_cape_cin` with
``extra_outputs=["parcel_path"]``. This module converts the resulting
``ParcelPath`` into the units of the diagrams.
"""

import dataclasses as dc

import numpy as np

from earthkit.plots.thermodynamic.transforms import T_C2K


@dc.dataclass(frozen=True)
class ParcelProfiles:
    """
    The profiles of a parcel ascent in diagram units, ordered from the start of the ascent upwards.

    Attributes
    ----------
    p : numpy.ndarray
        Pressure (hPa).
    t : numpy.ndarray
        Parcel temperature (°C).
    tv : numpy.ndarray
        Parcel virtual temperature (°C).
    tv_env : numpy.ndarray
        Virtual temperature of the environment (°C).
    """

    p: np.ndarray
    t: np.ndarray
    tv: np.ndarray
    tv_env: np.ndarray

    @classmethod
    def from_path(cls, path):
        """
        Create from an earthkit-meteo ``ParcelPath`` of a single profile.

        Parameters
        ----------
        path : earthkit.meteo.thermo.array.cape_cin.ParcelPath
            The parcel path, e.g. ``extras["parcel_path"]`` returned by
            :func:`earthkit.meteo.thermo.surface_cape_cin` for 1-D (single
            profile) inputs.
        """
        if not hasattr(path, "p"):
            raise TypeError(
                "The parcel path has no pressure; a version of earthkit-meteo whose ParcelPath has a 'p' "
                "attribute is required"
            )
        p = np.asarray(path.p, dtype=float)
        if p.ndim != 1:
            raise ValueError(
                f"Expected the parcel path of a single profile (1-D arrays); got arrays of shape {p.shape}. "
                "Compute the parcel from 1-D profiles, or select a single column."
            )
        t, tv, tv_env = (np.asarray(a, dtype=float) for a in (path.t, path.tv, path.tv_env))
        # Levels below the ground or below the start of the ascent are NaN
        ok = np.isfinite(p) & np.isfinite(t) & np.isfinite(tv) & np.isfinite(tv_env)
        order = np.argsort(-p[ok], kind="stable")
        return cls(
            p=p[ok][order] / 100.0,
            t=t[ok][order] - T_C2K,
            tv=tv[ok][order] - T_C2K,
            tv_env=tv_env[ok][order] - T_C2K,
        )


def level(parcel_level):
    """
    Pressure (hPa) and temperature (°C) of a key level, or ``None`` if it does not exist.

    Parameters
    ----------
    parcel_level : earthkit.meteo.thermo.array.cape_cin.ParcelLevel
        E.g. ``path.lcl``, ``path.lfc`` or ``path.el``.
    """
    p = float(np.asarray(parcel_level.p))
    t = float(np.asarray(parcel_level.t))
    if not (np.isfinite(p) and np.isfinite(t)):
        return None
    return p / 100.0, t - T_C2K


def shading_top(path):
    """
    Top (hPa) of the layer in which the buoyancy areas are shaded.

    The areas are shaded from the start of the ascent up to the equilibrium
    level (EL). When the parcel is still buoyant at the top of the profile
    (there is an LFC but no EL) they are shaded up to the top; without an LFC
    there is no free convection and nothing is shaded.

    Returns
    -------
    float or None
        The pressure (hPa), ``-inf`` for the top of the profile, or ``None``.
    """
    el = level(path.el)
    if el is not None:
        return el[0]
    if level(path.lfc) is not None:
        return -np.inf
    return None

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


class ExtractionError(Exception):
    """
    Base exception for all dimension extraction errors.
    
    This is the parent class for all extraction-related exceptions,
    allowing us to catch all extraction errors with a single except clause.
    """
    pass


class MissingDimensionError(ExtractionError):
    """
    Raised when required dimensions cannot be found or inferred.
    
    This occurs when the extractor cannot determine sensible defaults
    and the user hasn't provided enough information.
    """
    pass


class AmbiguousDimensionError(ExtractionError):
    """
    Raised when multiple valid options exist and the choice is ambiguous.
    
    This occurs when the data contains multiple possible candidates for
    a dimension (e.g., multiple variables that could be y) and the extractor
    cannot determine which one to use without user input.
    """
    pass


class IncompatibleDimensionsError(ExtractionError):
    """
    Raised when dimensions are incompatible with each other or the plot type.
    
    This occurs when the shapes or types of x, y, z don't match up properly,
    or when dimensions don't match the requirements of the plot type.
    """
    pass


class InvalidSpecificationError(ExtractionError):
    """
    Raised when user-provided dimension specifications are invalid.
    
    This occurs when the user specifies a dimension name, variable, or
    coordinate that doesn't exist in the data, or specifies something
    that doesn't make sense for the data type.
    """
    pass


class MetadataError(ExtractionError):
    """
    Raised when metadata is missing, malformed, or inconsistent.
    
    This occurs when the extractor relies on metadata (e.g., CF conventions)
    but the metadata is incomplete or contradictory.
    """
    pass
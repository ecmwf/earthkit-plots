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

"""
Web Map Service (WMS) server for serving map tiles on-demand.

This module provides a WMS server implementation that generates tiles dynamically
using earthkit-plots' Tile class. The server responds to WMS GetMap requests and
renders tiles on-the-fly from the provided data.
"""

import io
import logging
import threading
from urllib.parse import parse_qs
from multiprocessing import Pool, cpu_count
import functools

import cartopy.crs as ccrs

logger = logging.getLogger(__name__)


def _generate_tile_worker(data, bbox, width, height, crs_name, style):
    """
    Worker function for multiprocessing tile generation.

    This function must be at module level (not a method) for pickling.

    Parameters
    ----------
    data : any
        Data object to plot
    bbox : tuple
        Bounding box (x_min, y_min, x_max, y_max)
    width : int
        Tile width in pixels
    height : int
        Tile height in pixels
    crs_name : str
        CRS name (e.g., "PlateCarree")
    style : Style or None
        earthkit-plots Style object

    Returns
    -------
    bytes
        PNG tile data
    """
    from earthkit.plots.core.tiles import Tile

    # Create tile
    tile = Tile(domain=bbox, size=(width, height), crs=ccrs.PlateCarree())

    # Get transform CRS
    if crs_name == "PlateCarree":
        transform = ccrs.PlateCarree()
    else:
        # For future: support other CRS types
        transform = ccrs.PlateCarree()

    # Plot data on the tile
    if style is not None:
        tile.contourf(data, style=style, transform=transform)
    else:
        tile.contourf(data, transform=transform)

    # Save to bytes buffer
    buffer = io.BytesIO()
    tile.save(buffer, format="png")
    buffer.seek(0)

    return buffer.read()


class WMS:
    """
    A Web Map Service (WMS) server for serving map tiles on-demand.

    This class creates a lightweight WMS server that responds to GetMap requests
    and generates tiles dynamically using the Tile class. The server runs in a
    background thread and can serve multiple layers from different data sources.

    Currently supports:
    - WMS 1.3.0 protocol
    - EPSG:4326 (PlateCarree) CRS
    - PNG image format
    - Single field data

    Parameters
    ----------
    data : numpy.ndarray, xarray.DataArray, or earthkit.data object
        The data to serve. Can be a 2D array or a data object with coordinate
        information.
    x : numpy.ndarray, optional
        X coordinates (longitudes) for the data. If not provided, will be
        extracted from data if possible.
    y : numpy.ndarray, optional
        Y coordinates (latitudes) for the data. If not provided, will be
        extracted from data if possible.
    layer_name : str, optional
        The name of the layer to serve. Default is "layer0".
    title : str, optional
        Human-readable title for the layer. Default is the layer_name.
    style : earthkit.plots.styles.Style, optional
        The style to use for rendering. If not provided, a default style
        will be used.
    port : int, optional
        The port on which to run the WMS server. Default is 8080.
    host : str, optional
        The host address to bind to. Default is "127.0.0.1" (localhost only).
        Use "0.0.0.0" to allow external connections.
    crs : str or cartopy.crs.CRS, optional
        The CRS of the source data. Default is "PlateCarree".

    Examples
    --------
    Basic usage with numpy array:

    >>> import numpy as np
    >>> from earthkit.plots.core.wms import WMS
    >>>
    >>> # Create test data
    >>> lons = np.linspace(-180, 180, 360)
    >>> lats = np.linspace(-90, 90, 180)
    >>> data = np.random.randn(180, 360)
    >>>
    >>> # Start WMS server
    >>> wms = WMS(data, x=lons, y=lats, port=8080)
    >>> wms.start()
    >>>
    >>> # Server is now running at http://localhost:8080/wms
    >>> # Stop when done
    >>> wms.stop()

    Using with xarray:

    >>> import xarray as xr
    >>> ds = xr.open_dataset("temperature.nc")
    >>> wms = WMS(ds['temperature'].isel(time=0))
    >>> wms.start()

    Custom style and layer name:

    >>> from earthkit.plots.styles import Style
    >>> style = Style(cmap='viridis', vmin=0, vmax=100)
    >>> wms = WMS(data, x=lons, y=lats,
    ...           layer_name="temperature",
    ...           title="Surface Temperature",
    ...           style=style)
    >>> wms.start()

    Notes
    -----
    The WMS server implements a subset of the WMS 1.3.0 specification:

    - GetCapabilities: Returns XML describing available layers and supported formats
    - GetMap: Generates and returns a tile for the requested bounding box

    The server runs in a background thread and does not block. Use `start()` to
    begin serving and `stop()` to shut down the server.

    Currently only supports EPSG:4326 (PlateCarree) projection. Support for
    additional projections will be added in future versions.
    """

    def __init__(
        self,
        data,
        x=None,
        y=None,
        layer_name="layer0",
        title=None,
        style=None,
        port=8080,
        host="127.0.0.1",
        crs="PlateCarree",
        max_workers=None,
        use_multiprocessing=True,
    ):
        self.data = data
        self.x = x
        self.y = y
        self.layer_name = layer_name
        self.title = title or layer_name
        self.style = style
        self.port = port
        self.host = host
        self.crs = crs if isinstance(crs, str) else type(crs).__name__

        # Multiprocessing configuration
        self.use_multiprocessing = use_multiprocessing
        self.max_workers = max_workers or cpu_count()

        # Use earthkit-plots' dimension extraction infrastructure
        from earthkit.plots.sources import get_dimension_set
        from earthkit.plots.sources.core import PlotType

        # Extract dimension information using earthkit-plots
        self._dimension_set = get_dimension_set(
            data,
            x=x,
            y=y,
            plot_type=PlotType.GEOGRAPHIC_2D,
            crs="auto",
        )

        # Extract coordinates from dimension set
        self.x = self._dimension_set.x.values
        self.y = self._dimension_set.y.values

        # Get data bounds
        self.x_min = float(self.x.min())
        self.x_max = float(self.x.max())
        self.y_min = float(self.y.min())
        self.y_max = float(self.y.max())

        logger.info(f"WMS initialized with data")
        logger.info(f"  X range: [{self.x_min:.2f}, {self.x_max:.2f}]")
        logger.info(f"  Y range: [{self.y_min:.2f}, {self.y_max:.2f}]")
        logger.info(f"  Data shape: {self._dimension_set.z.values.shape}")
        if self.use_multiprocessing:
            logger.info(f"  Multiprocessing enabled with {self.max_workers} workers")

        # Server state
        self._server = None
        self._server_thread = None
        self._running = False
        self._process_pool = None

        # Statistics
        self._tile_count = 0
        self._request_count = 0

    def _get_capabilities_xml(self):
        """Generate WMS GetCapabilities XML response."""
        # Use cached bounds
        x_min, x_max = self.x_min, self.x_max
        y_min, y_max = self.y_min, self.y_max

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:schemaLocation="http://www.opengis.net/wms http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd">
  <Service>
    <Name>WMS</Name>
    <Title>earthkit-plots WMS Server</Title>
    <Abstract>Web Map Service for serving tiles generated by earthkit-plots</Abstract>
    <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                    xlink:href="http://{self.host}:{self.port}/wms"/>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>text/xml</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                              xlink:href="http://{self.host}:{self.port}/wms?"/>
            </Get>
          </HTTP>
        </DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                              xlink:href="http://{self.host}:{self.port}/wms?"/>
            </Get>
          </HTTP>
        </DCPType>
      </GetMap>
    </Request>
    <Exception>
      <Format>XML</Format>
    </Exception>
    <Layer>
      <Title>earthkit-plots Layers</Title>
      <CRS>EPSG:4326</CRS>
      <Layer queryable="0">
        <Name>{self.layer_name}</Name>
        <Title>{self.title}</Title>
        <CRS>EPSG:4326</CRS>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>{x_min}</westBoundLongitude>
          <eastBoundLongitude>{x_max}</eastBoundLongitude>
          <southBoundLatitude>{y_min}</southBoundLatitude>
          <northBoundLatitude>{y_max}</northBoundLatitude>
        </EX_GeographicBoundingBox>
        <BoundingBox CRS="EPSG:4326" minx="{x_min}" miny="{y_min}" maxx="{x_max}" maxy="{y_max}"/>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>"""
        return xml

    def _generate_tile(self, bbox, width, height):
        """
        Generate a tile for the given bounding box and dimensions.

        Uses multiprocessing if enabled, otherwise generates in main thread.

        Parameters
        ----------
        bbox : tuple
            Bounding box (x_min, y_min, x_max, y_max) in EPSG:4326
        width : int
            Tile width in pixels
        height : int
            Tile height in pixels

        Returns
        -------
        io.BytesIO
            PNG image data as bytes
        """
        if self.use_multiprocessing and self._process_pool is not None:
            # Use multiprocessing for tile generation
            try:
                # Submit task to process pool
                result = self._process_pool.apply_async(
                    _generate_tile_worker,
                    (self.data, bbox, width, height, self.crs, self.style)
                )
                # Wait for result (with timeout to avoid hanging)
                tile_data = result.get(timeout=30)

                # Wrap in BytesIO
                buffer = io.BytesIO(tile_data)

                self._tile_count += 1
                logger.debug(f"Generated tile #{self._tile_count} (multiprocessing) for bbox={bbox}, size=({width}, {height})")

                return buffer
            except Exception as e:
                logger.error(f"Multiprocessing tile generation failed: {e}. Falling back to single-threaded.")
                # Fall through to single-threaded generation

        # Single-threaded tile generation (fallback or when multiprocessing disabled)
        from earthkit.plots.core.tiles import Tile

        # Create tile with the requested dimensions
        tile = Tile(domain=bbox, size=(width, height), crs=ccrs.PlateCarree())

        # Get transform CRS
        if self.crs == "PlateCarree":
            transform = ccrs.PlateCarree()
        else:
            # For future: support other CRS types
            transform = ccrs.PlateCarree()

        # Plot data on the tile using the original data object
        # earthkit-plots will extract the data properly using its own infrastructure
        # Use "auto" for coordinates to let earthkit-plots handle extraction
        if self.style is not None:
            tile.contourf(self.data, style=self.style, transform=transform)
        else:
            tile.contourf(self.data, transform=transform)

        # Save to bytes buffer
        buffer = io.BytesIO()
        tile.save(buffer, format="png")
        buffer.seek(0)

        self._tile_count += 1
        logger.debug(f"Generated tile #{self._tile_count} (single-threaded) for bbox={bbox}, size=({width}, {height})")

        return buffer

    def _handle_request(self, environ, start_response):
        """
        WSGI request handler.

        Handles WMS GetCapabilities and GetMap requests.
        """
        self._request_count += 1

        # Parse query string
        query_string = environ.get("QUERY_STRING", "")
        params = parse_qs(query_string)

        # Get request type (case-insensitive)
        request_type = None
        for key in params:
            if key.upper() == "REQUEST":
                request_type = params[key][0].upper()
                break

        try:
            if request_type == "GETCAPABILITIES":
                # Return capabilities XML
                xml = self._get_capabilities_xml()
                start_response("200 OK", [
                    ("Content-Type", "text/xml"),
                    ("Content-Length", str(len(xml))),
                ])
                return [xml.encode("utf-8")]

            elif request_type == "GETMAP":
                # Parse GetMap parameters
                bbox_str = None
                width = None
                height = None
                layers = None

                for key in params:
                    key_upper = key.upper()
                    if key_upper == "BBOX":
                        bbox_str = params[key][0]
                    elif key_upper == "WIDTH":
                        width = int(params[key][0])
                    elif key_upper == "HEIGHT":
                        height = int(params[key][0])
                    elif key_upper == "LAYERS":
                        layers = params[key][0]

                # Validate parameters
                if not bbox_str or not width or not height:
                    error = "Missing required parameters: BBOX, WIDTH, HEIGHT"
                    start_response("400 Bad Request", [
                        ("Content-Type", "text/plain"),
                    ])
                    return [error.encode("utf-8")]

                # Parse bbox
                try:
                    bbox = [float(x) for x in bbox_str.split(",")]
                    if len(bbox) != 4:
                        raise ValueError("BBOX must have 4 values")
                except ValueError as e:
                    error = f"Invalid BBOX format: {e}"
                    start_response("400 Bad Request", [
                        ("Content-Type", "text/plain"),
                    ])
                    return [error.encode("utf-8")]

                # Generate tile
                tile_buffer = self._generate_tile(bbox, width, height)
                tile_data = tile_buffer.read()

                start_response("200 OK", [
                    ("Content-Type", "image/png"),
                    ("Content-Length", str(len(tile_data))),
                ])
                return [tile_data]

            else:
                # Unknown request type
                error = f"Unknown REQUEST type: {request_type}"
                start_response("400 Bad Request", [
                    ("Content-Type", "text/plain"),
                ])
                return [error.encode("utf-8")]

        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            error = f"Internal server error: {str(e)}"
            start_response("500 Internal Server Error", [
                ("Content-Type", "text/plain"),
            ])
            return [error.encode("utf-8")]

    def start(self):
        """
        Start the WMS server in a background thread.

        The server will begin listening on the configured host and port.
        This method returns immediately and does not block.

        If multiprocessing is enabled, creates a process pool for parallel
        tile generation.

        Raises
        ------
        RuntimeError
            If the server is already running.
        ImportError
            If Flask is not installed.
        """
        if self._running:
            raise RuntimeError("WMS server is already running")

        try:
            from werkzeug.serving import make_server
        except ImportError:
            raise ImportError(
                "Flask/Werkzeug is required for WMS server. "
                "Install with: pip install flask"
            )

        logger.info(f"Starting WMS server on {self.host}:{self.port}")

        # Create process pool for parallel tile generation if enabled
        if self.use_multiprocessing:
            logger.info(f"Creating process pool with {self.max_workers} workers")
            self._process_pool = Pool(processes=self.max_workers)

        # Create WSGI server
        self._server = make_server(self.host, self.port, self._handle_request, threaded=True)

        # Start server in background thread
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()

        self._running = True

        logger.info(f"WMS server started successfully")
        logger.info(f"GetCapabilities: http://{self.host}:{self.port}/wms?REQUEST=GetCapabilities")
        logger.info(f"Layer: {self.layer_name}")
        if self.use_multiprocessing:
            logger.info(f"Multiprocessing enabled: {self.max_workers} workers available for parallel tile generation")

        return self

    def stop(self):
        """
        Stop the WMS server.

        This will shut down the server and wait for the background thread to finish.
        """
        if not self._running:
            logger.warning("WMS server is not running")
            return

        logger.info("Stopping WMS server...")

        if self._server:
            self._server.shutdown()

        if self._server_thread:
            self._server_thread.join(timeout=5)

        self._running = False
        self._server = None
        self._server_thread = None

        logger.info(f"WMS server stopped. Served {self._tile_count} tiles from {self._request_count} requests")

    def is_running(self):
        """
        Check if the WMS server is currently running.

        Returns
        -------
        bool
            True if the server is running, False otherwise.
        """
        return self._running

    def __enter__(self):
        """Context manager entry - start the server."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop the server."""
        self.stop()

    def __repr__(self):
        status = "running" if self._running else "stopped"
        return (
            f"WMS(layer='{self.layer_name}', "
            f"status={status}, "
            f"url=http://{self.host}:{self.port}/wms)"
        )

import io
import uuid
from pathlib import Path
from IPython.display import IFrame, Image

from earthkit.plots.components._coastlines import COASTLINES
from earthkit.plots import styles

GLOBE_HTML = """
<head>
    <style> body {{ margin: 0; }} </style>
  
    <script src="https://unpkg.com/react/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone"></script>
  
    <script src="https://unpkg.com/react-globe.gl"></script>
    <script src="https://unpkg.com/three/build/three.module.js"></script>
    <!--<script src="../../dist/react-globe.gl.js"></script>-->
  </head>
  
  <body>
    <div id="globeViz"></div>
  
  <script type="text/jsx" data-type="module">
    import * as THREE from '//unpkg.com/three/build/three.module.js';
    const globeMaterial = new THREE.MeshBasicMaterial();

  const {{ useState, useEffect }} = React;

  const World = () => {{

    const coastlines = {coastlines}

    return <Globe
      globeImageUrl="{img_url}"
      backgroundColor="#00000000"
      width={{{width}}}
      height={{{height}}}
      globeMaterial={{globeMaterial}}
    pathsData={{coastlines}}
    pathPoints="coords"
    pathPointLat={{p => p[1]}}
    pathPointLng={{p => p[0]}}
    pathPointAlt={{0.001}}
    pathColor="#555"
    pathStroke={{0.75}}
    pathTransitionDuration={{0}}
    />;
  }};

  ReactDOM.render(
    <World />,
    document.getElementById('globeViz')
  );
  </script>
  </body>
"""

def globe(data, style=None, out_fn = None, out_path='.',
          size=500, **kwargs):
    """Generate an IFrame containing a templated javascript package."""
    from earthkit.plots import Figure
    import matplotlib.pyplot as plt
    import base64
    import cartopy.crs as ccrs
    
    img_url = "test.png"
    
    figure = Figure(left=0, right=1, bottom=0, top=1, size=(30, 30))
    
    crs = data.projection().to_cartopy_crs()
    if crs.__class__.__name__ != "PlateCarree":
        crs = ccrs.PlateCarree()
    
    subplot = figure.add_map(crs=crs)
    subplot.block(data, style=style, transform_first=True)
    extent = subplot.ax.get_extent()
    if extent != (-180.0, 180.0, -90.0, 90.0):
        subplot.ax.set_global()
    subplot.ax.set_frame_on(False)
    figure.save(img_url, pad_inches=0)
    plt.close()
    
    if not out_fn:
        out_fn = Path(f"{uuid.uuid4()}.html")
    
    # Generate the path to the output file
    out_path = Path(out_path)
    filepath = out_path / out_fn
    # Check the required directory path exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    image = Image(img_url)
    
    img_url = "data:image/png;base64," + base64.b64encode(image.data).decode('ascii')
 
    # The open "wt" parameters are: write, text mode;
    with io.open(filepath, 'wt', encoding='utf8') as outfile:
        # The data is passed in as a dictionary so we can pass different
        # arguments to the template
        outfile.write(GLOBE_HTML.format(img_url=img_url, width=size, height=size, coastlines=COASTLINES))
 
    return IFrame(src=filepath, width=size, height=size)



.. _styles-gallery:

Styles gallery
==============

This page lists all built-in styles shipped with **earthkit-plots**.
Each entry shows the style name and a preview of the colorbar.
Click the copy button next to any name to copy it for use in your code::

    chart.contourf(data, style="temperature-2m-turbo-celsius")

.. note::

   This page is auto-generated during the documentation build.
   Any new styles added to ``data/styles/auto-styles/`` will appear
   here automatically.

.. raw:: html

   <style>
   .ek-style-entry {
     display: flex;
     align-items: center;
     justify-content: space-between;
     margin-bottom: 1.2em;
   }
   .ek-style-left { display: flex; align-items: center; gap: 6px; }
   .ek-style-name {
     font-family: monospace;
     font-size: 0.95em;
     background: #f5f5f5;
     border: 1px solid #ddd;
     border-radius: 3px;
     padding: 2px 6px;
   }
   .ek-copy-btn {
     display: inline-flex;
     align-items: center;
     gap: 5px;
     padding: 3px 10px;
     font-size: 0.8em;
     cursor: pointer;
     border: 1px solid #aaa;
     border-radius: 3px;
     background: #fff;
     white-space: nowrap;
     flex-shrink: 0;
   }
   .ek-copy-btn:hover { background: #e8e8e8; }
   .ek-copy-btn svg { width: 14px; height: 14px; vertical-align: middle; }
   </style>
   <script>
   var EK_COPY_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg>';
   var EK_CHECK_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 12l5 5l10 -10" /></svg>';
   function ekCopy(btn, text) {
     navigator.clipboard.writeText(text).then(function() {
       btn.innerHTML = EK_CHECK_SVG + ' Style name copied';
       setTimeout(function() {
         btn.innerHTML = EK_COPY_SVG + ' Copy this style name';
       }, 1500);
     });
   }
   </script>

Mean sea level pressure
-----------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mslp-contour-pa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mslp-contour-pa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

*(Contour style — levels are determined from data at plot time)*

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mslp-contour-hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mslp-contour-hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

*(Contour style — levels are determined from data at plot time)*

Temperature at 850hpa
---------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">temperature-850hpa-rainbow-celsius</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'temperature-850hpa-rainbow-celsius')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/temperature-850hpa-rainbow-celsius.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">temperature-850hpa-rainbow-kelvin</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'temperature-850hpa-rainbow-kelvin')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/temperature-850hpa-rainbow-kelvin.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">temperature-850hpa-rainbow-fahrenheit</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'temperature-850hpa-rainbow-fahrenheit')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/temperature-850hpa-rainbow-fahrenheit.png
   :alt: colorbar preview

River discharge
---------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">river-discharge-blues-europe</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'river-discharge-blues-europe')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/river-discharge-blues-europe.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">river-discharge-blues-global</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'river-discharge-blues-global')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/river-discharge-blues-global.png
   :alt: colorbar preview

Sea surface temperature
-----------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sst-spectral-celsius</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sst-spectral-celsius')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sst-spectral-celsius.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sst-spectral-kelvin</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sst-spectral-kelvin')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sst-spectral-kelvin.png
   :alt: colorbar preview

Snow water equivalent
---------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">snow-water-equivalent-kg-m2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'snow-water-equivalent-kg-m2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/snow-water-equivalent-kg-m2.png
   :alt: colorbar preview

Soil wetness index
------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">soil-wetness-greens</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'soil-wetness-greens')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/soil-wetness-greens.png
   :alt: colorbar preview

Near surface air temperature
----------------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">temperature-2m-turbo-celsius</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'temperature-2m-turbo-celsius')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/temperature-2m-turbo-celsius.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">temperature-2m-turbo-kelvin</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'temperature-2m-turbo-kelvin')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/temperature-2m-turbo-kelvin.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">temperature-2m-turbo-fahrenheit</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'temperature-2m-turbo-fahrenheit')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/temperature-2m-turbo-fahrenheit.png
   :alt: colorbar preview

Total precipitation
-------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">precipitation-turbo-mm</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'precipitation-turbo-mm')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/precipitation-turbo-mm.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">precipitation-turbo-m</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'precipitation-turbo-m')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/precipitation-turbo-m.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">precipitation-turbo-kg-m2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'precipitation-turbo-kg-m2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/precipitation-turbo-kg-m2.png
   :alt: colorbar preview

Total runoff water equivalent
-----------------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">runoff-blues-kg-m2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'runoff-blues-kg-m2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/runoff-blues-kg-m2.png
   :alt: colorbar preview

Wind gust at 10m in last 6 hours
--------------------------------

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">wind-gust-6h-m-s</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'wind-gust-6h-m-s')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/wind-gust-6h-m-s.png
   :alt: colorbar preview

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">wind-speed-10m-m-s</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'wind-speed-10m-m-s')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/wind-speed-10m-m-s.png
   :alt: colorbar preview

Wind
----

.. raw:: html

   <div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">wind-quiver-m-s</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'wind-quiver-m-s')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

*(No colorbar — vector style)*

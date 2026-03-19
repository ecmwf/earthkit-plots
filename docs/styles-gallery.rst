.. _styles-gallery:

Styles gallery
==============

This page lists all built-in styles shipped with **earthkit-plots**.
Each entry shows the style name and a preview of the colorbar.
Click the copy button next to any name to copy it for use in your code::

    chart.contourf(data, style="temperature-2m-turbo-celsius")

.. note::

   Many styles have units in their colorbar labels (e.g. °C, m/s).
   These styles will attempt to automatically convert the units of
   your data to match the style's units.

.. raw:: html

   <style>
   .ek-search-wrap {
     margin-bottom: 1.5em;
   }
   #ek-search {
     width: 100%;
     max-width: 480px;
     padding: 6px 10px;
     font-size: 0.95em;
     border: 1px solid #ccc;
     border-radius: 4px;
     box-sizing: border-box;
   }
   #ek-search-count {
     margin-top: 4px;
     font-size: 0.85em;
     color: #666;
   }
   .ek-section { }
   .ek-section-heading { }
   .ek-style-block { }
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
   <div class="ek-search-wrap">
     <input id="ek-search" type="search" placeholder="Search by style name, parameter name, short name, standard name…" oninput="ekFilter()">
     <div id="ek-search-count"></div>
   </div>
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
   function ekFilter() {
     var q = document.getElementById('ek-search').value.toLowerCase().trim();
     var blocks = document.querySelectorAll('.ek-style-block');
     var sections = document.querySelectorAll('.ek-section');
     var total = 0, shown = 0;
     blocks.forEach(function(block) {
       total++;
       var terms = (block.dataset.search || '').toLowerCase();
       var match = !q || terms.indexOf(q) !== -1;
       block.style.display = match ? '' : 'none';
       if (match) shown++;
     });
     sections.forEach(function(sec) {
       var visible = Array.from(sec.querySelectorAll('.ek-style-block')).some(function(b) {
         return b.style.display !== 'none';
       });
       sec.style.display = visible ? '' : 'none';
     });
     var countEl = document.getElementById('ek-search-count');
     if (q) {
       countEl.textContent = shown + ' of ' + total + ' styles match';
     } else {
       countEl.textContent = '';
     }
   }
   </script>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Divergence</h2>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 d divergence divergence_of_wind sh-blured-fm50t50lst-cell"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-fm50t50lst-cell</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-fm50t50lst-cell')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-fm50t50lst-cell.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 d divergence divergence_of_wind sh-blured-fm50t50lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-fm50t50lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-fm50t50lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-fm50t50lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 d divergence divergence_of_wind sh-blured-fm50t50lst-less"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-fm50t50lst-less</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-fm50t50lst-less')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-fm50t50lst-less.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 d divergence divergence_of_wind sh-blu-fm50tm1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-fm50tm1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-fm50tm1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-fm50tm1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 d divergence divergence_of_wind sh-red-f1t50lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f1t50lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f1t50lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f1t50lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 d divergence divergence_of_wind sh-viobrn-fm50t50lst-less"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-viobrn-fm50t50lst-less</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-viobrn-fm50t50lst-less')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-viobrn-fm50t50lst-less.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="1000divergence 155 ct-blured-fm5t50 d divergence divergence_of_wind"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blured-fm5t50</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blured-fm5t50')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blured-fm5t50.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Instantaneous 10 metre wind gust</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 3 hours 10 metre wind gust in the last 6 hours 10 metre wind gust since previous post-processing 10fg 10fg3 10fg6 10m_fg_interval 123 228028 228029 260065 49 gust i10fg instantaneous 10 metre wind gust sh-red-f10t70lst vmax_10m"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f10t70lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f10t70lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f10t70lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 3 hours 10 metre wind gust in the last 6 hours 10 metre wind gust since previous post-processing 10fg 10fg3 10fg6 10m_fg_interval 123 228028 228029 260065 49 gust i10fg instantaneous 10 metre wind gust sh-all-f2t50i2 vmax_10m"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f2t50i2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f2t50i2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f2t50i2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 3 hours 10 metre wind gust in the last 6 hours 10 metre wind gust since previous post-processing 10fg 10fg3 10fg6 10m_fg_interval 123 228028 228029 260065 49 gust i10fg instantaneous 10 metre wind gust sh-grn-f10t100lst vmax_10m"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grn-f10t100lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grn-f10t100lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grn-f10t100lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 3 hours 10 metre wind gust in the last 6 hours 10 metre wind gust since previous post-processing 10fg 10fg3 10fg6 10m_fg_interval 123 228028 228029 260065 49 gust i10fg instantaneous 10 metre wind gust sh-all-f03t70-beauf vmax_10m"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f03t70-beauf</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f03t70-beauf')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f03t70-beauf.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 3 hours 10 metre wind gust in the last 6 hours 10 metre wind gust since previous post-processing 10fg 10fg3 10fg6 10m_fg_interval 123 228028 228029 260065 49 ct-red-i5 gust i10fg instantaneous 10 metre wind gust vmax_10m"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-red-i5</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-red-i5')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-red-i5.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Wind speed</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 200_windspeed_field sh-grn-f30t100i10 wind speed ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grn-f30t100i10</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grn-f30t100i10')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grn-f30t100i10.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 200_windspeed_field sh-all-f30t100i10 wind speed ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f30t100i10</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f30t100i10')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f30t100i10.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 200_windspeed_field ct-grn-f30-i10 wind speed ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-grn-f30-i10</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-grn-f30-i10')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-grn-f30-i10.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">2 metre temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2m-temperature-spectral-kelvin 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">2m-temperature-spectral-kelvin</code></div><button class="ek-copy-btn" onclick="ekCopy(this, '2m-temperature-spectral-kelvin')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/2m-temperature-spectral-kelvin.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2m-temperature-spectral-fahrenheit 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">2m-temperature-spectral-fahrenheit</code></div><button class="ek-copy-btn" onclick="ekCopy(this, '2m-temperature-spectral-fahrenheit')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/2m-temperature-spectral-fahrenheit.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2m-temperature-spectral-celsius 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">2m-temperature-spectral-celsius</code></div><button class="ek-copy-btn" onclick="ekCopy(this, '2m-temperature-spectral-celsius')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/2m-temperature-spectral-celsius.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm48t56i4 t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm48t56i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm48t56i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm48t56i4.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm64t52i4 t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm64t52i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm64t52i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm64t52i4.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature ct-red-i2-dash mean 2 metre temperature near-surface air temperature screen level temperature t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-red-i2-dash</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-red-i2-dash')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-red-i2-dash.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm32t42i2 t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm32t42i2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm32t42i2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm32t42i2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm48t56i4-ct-wh t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm48t56i4-ct-wh</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm48t56i4-ct-wh')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm48t56i4-ct-wh.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm52t48i4 t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm52t48i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm52t48i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm52t48i4.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm52t48i4-light t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm52t48i4-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm52t48i4-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm52t48i4-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-gry-fm72t56lst t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-gry-fm72t56lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-gry-fm72t56lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-gry-fm72t56lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature ct-red-i4-t3 mean 2 metre temperature near-surface air temperature screen level temperature t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-red-i4-t3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-red-i4-t3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-red-i4-t3.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm80t56i4-v2 t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm80t56i4-v2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm80t56i4-v2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm80t56i4-v2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature sh-all-fm50t58i2 t temp_scrn temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fm50t58i2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fm50t58i2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fm50t58i2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 167 2 metre temperature 2t 500015 500016 air_temperature mean 2 metre temperature near-surface air temperature screen level temperature t temp_scrn temperature transparent-zero-blue"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">transparent-zero-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'transparent-zero-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/transparent-zero-blue.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Wind speed</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 300_windspeed ct-ylw-f30-i10 wind speed ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-ylw-f30-i10</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-ylw-f30-i10')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-ylw-f30-i10.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Potential vorticity</h2>

.. raw:: html

   <div class="ek-style-block" data-search="315Kpotvort 60 potential vorticity pv sh-blu-f02t30"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f02t30</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f02t30')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f02t30.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="315Kpotvort 60 potential vorticity pv sh-gry-f0t20lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-gry-f0t20lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-gry-f0t20lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-gry-f0t20lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="315Kpotvort 60 ct-vio-i1-t1 potential vorticity pv"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-vio-i1-t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-vio-i1-t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-vio-i1-t1.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Potential vorticity</h2>

.. raw:: html

   <div class="ek-style-block" data-search="500pv 60 ct-magenta-i2-t3 potential vorticity pv"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-magenta-i2-t3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-magenta-i2-t3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-magenta-i2-t3.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Vorticity (relative)</h2>

.. raw:: html

   <div class="ek-style-block" data-search="138 700vorticity atmosphere_relative_vorticity sh-blured-fm50t50lst-narrow-range vo vorticity (relative)"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-fm50t50lst-narrow-range</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-fm50t50lst-narrow-range')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-fm50t50lst-narrow-range.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Vertical velocity</h2>

.. raw:: html

   <div class="ek-style-block" data-search="135 700w lagrangian_tendency_of_air_pressure sh-blured-fm5t5lst vertical velocity w"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-fm5t5lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-fm5t5lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-fm5t5lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="135 700w lagrangian_tendency_of_air_pressure sh-blu-fm5tm005lst vertical velocity w"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-fm5tm005lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-fm5tm005lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-fm5tm005lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="135 700w lagrangian_tendency_of_air_pressure sh-red-f005t5lst vertical velocity w"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f005t5lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f005t5lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f005t5lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="135 700w lagrangian_tendency_of_air_pressure sh-viobrn-fm5t5lst vertical velocity w"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-viobrn-fm5t5lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-viobrn-fm5t5lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-viobrn-fm5t5lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="135 700w ct-blured-lst lagrangian_tendency_of_air_pressure vertical velocity w"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blured-lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blured-lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blured-lst.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Wind speed</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 800ws sh-red-f5t70lst wind speed ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f5t70lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f5t70lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f5t70lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 800ws sh-all-f5t70lst wind speed ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f5t70lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f5t70lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f5t70lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">850Ws Mean</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 850ws_mean ct-blk-i5-t2 ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i5-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i5-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i5-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 850ws_mean ct-blk-i5-t1 ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i5-t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i5-t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i5-t1.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 850ws_mean ct-blue-i5-t2 ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blue-i5-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blue-i5-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blue-i5-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">850Ws Spread</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 850ws_spread sh-range-f02t30 ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-range-f02t30</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-range-f02t30')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-range-f02t30.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Drought code</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260542 260543 aristotle_drought_code drought code drought-code-1 drtcode duff moisture code dufmcode"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">drought-code-1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'drought-code-1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/drought-code-1.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="260542 260543 aristotle_drought_code drought code drought-code-2 drtcode duff moisture code dufmcode"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">drought-code-2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'drought-code-2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/drought-code-2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Forest fire weather index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260540 aristotle_fwi forest fire weather index fwi-1 fwinx"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">fwi-1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'fwi-1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/fwi-1.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="260540 aristotle_fwi forest fire weather index fwi-3 fwinx"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">fwi-3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'fwi-3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/fwi-3.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Fine fuel moisture code</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260541 aristotle_risico ffmcode fine fuel moisture code risico-1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">risico-1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'risico-1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/risico-1.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="260541 aristotle_risico ffmcode fine fuel moisture code risico-2"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">risico-2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'risico-2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/risico-2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Convective available potential energy</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228035 59 cape convective available potential energy maximum cape in the last 6 hours mxcape6 range-100-4500"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">range-100-4500</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'range-100-4500')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/range-100-4500.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228035 59 cape convective available potential energy maximum cape in the last 6 hours mxcape6 range-50-9000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">range-50-9000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'range-50-9000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/range-50-9000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228035 59 cape convective available potential energy ct-red-f50t8000 maximum cape in the last 6 hours mxcape6"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-red-f50t8000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-red-f50t8000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-red-f50t8000.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228035 59 cape convective available potential energy ct-green-f10t8000 maximum cape in the last 6 hours mxcape6"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-green-f10t8000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-green-f10t8000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-green-f10t8000.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228035 59 cape cape-extra1 convective available potential energy maximum cape in the last 6 hours mxcape6"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">cape-extra1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'cape-extra1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/cape-extra1.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Cloud base height</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228023 cbh cloud base height cloud_base_altitude convective_cloud_base_altitude convective_cloud_base_height sh-cbh-blk-f0t22000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-cbh-blk-f0t22000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-cbh-blk-f0t22000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-cbh-blk-f0t22000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228023 cbh cloud base height cloud_base_altitude convective_cloud_base_altitude convective_cloud_base_height sh-cbh-f0t22000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-cbh-f0t22000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-cbh-f0t22000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-cbh-f0t22000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Convective inhibition</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228001 atmosphere_convective_inhibition cin convective inhibition sh-red-f0t900"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f0t900</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f0t900')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f0t900.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228001 atmosphere_convective_inhibition cin convective inhibition sh-black-f0t900"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-black-f0t900</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-black-f0t900')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-black-f0t900.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228001 atmosphere_convective_inhibition cin convective inhibition sh-grey-min50"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grey-min50</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grey-min50')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grey-min50.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228001 atmosphere_convective_inhibition cin convective inhibition sh-grey-min100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grey-min100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grey-min100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grey-min100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228001 atmosphere_convective_inhibition cin convective inhibition sh-grey-min200"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grey-min200</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grey-min200')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grey-min200.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total Aerosol Optical Depth at 550nm</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210207 aod550 composition_aod550 sh-all-aod total aerosol optical depth at 550nm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-aod</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-aod')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-aod.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210207 aod550 composition_aod550 sh-buylrd-aod total aerosol optical depth at 550nm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-buylrd-aod</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-buylrd-aod')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-buylrd-aod.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210207 aod550 composition_aod550 sh-buylrd-aod-lowthreshold total aerosol optical depth at 550nm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-buylrd-aod-lowthreshold</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-buylrd-aod-lowthreshold')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-buylrd-aod-lowthreshold.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210207 aod550 composition_aod550 sh-oranges-aod total aerosol optical depth at 550nm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-oranges-aod</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-oranges-aod')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-oranges-aod.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Composition Ch4 300</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_300 sh-nipy-spectral-ch4-300hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-ch4-300hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-ch4-300hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-ch4-300hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_300 sh-rdgy-r-ch4-300hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-ch4-300hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-ch4-300hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-ch4-300hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Composition Ch4 50</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_50 sh-nipy-spectral-ch4-50hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-ch4-50hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-ch4-50hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-ch4-50hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_50 sh-rdgy-r-ch4-50hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-ch4-50hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-ch4-50hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-ch4-50hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Methane</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_500 methane methane (chemistry) sh-nipy-spectral-ch4-500hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-ch4-500hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-ch4-500hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-ch4-500hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_500 methane methane (chemistry) sh-rdgy-r-ch4-500hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-ch4-500hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-ch4-500hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-ch4-500hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Composition Ch4 850</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_850 sh-nipy-spectral-ch4-850hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-ch4-850hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-ch4-850hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-ch4-850hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_850 sh-rdgy-r-ch4-850hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-ch4-850hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-ch4-850hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-ch4-850hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Composition Ch4 Surface</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_surface sh-nipy-spectral-ch4-surface"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-ch4-surface</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-ch4-surface')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-ch4-surface.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210062 217004 ch4 ch4_c composition_ch4_surface sh-rdgy-r-ch4-surface"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-ch4-surface</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-ch4-surface')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-ch4-surface.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">CH4 column-mean molar fraction</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210065 ch4 column-mean molar fraction composition_ch4_totalcolumn sh-nipy-spectral-ch4-totalcolumn tcch4"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-ch4-totalcolumn</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-ch4-totalcolumn')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-ch4-totalcolumn.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210065 ch4 column-mean molar fraction composition_ch4_totalcolumn sh-rdgy-r-ch4-totalcolumn tcch4"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-ch4-totalcolumn</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-ch4-totalcolumn')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-ch4-totalcolumn.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">CO2 column-mean molar fraction</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210064 co2 column-mean molar fraction composition_co2_totalcolumn sh-nipy-spectral-co2-totalcolumn tcco2"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-nipy-spectral-co2-totalcolumn</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-nipy-spectral-co2-totalcolumn')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-nipy-spectral-co2-totalcolumn.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210064 co2 column-mean molar fraction composition_co2_totalcolumn sh-spectral-r-co2-totalcolumn tcco2"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-spectral-r-co2-totalcolumn</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-spectral-r-co2-totalcolumn')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-spectral-r-co2-totalcolumn.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210064 co2 column-mean molar fraction composition_co2_totalcolumn sh-rdgy-r-co2-totalcolumn tcco2"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rdgy-r-co2-totalcolumn</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rdgy-r-co2-totalcolumn')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rdgy-r-co2-totalcolumn.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Carbon monoxide</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210123 carbon monoxide co composition_co700 sh-all-co-upper"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-co-upper</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-co-upper')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-co-upper.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210123 carbon monoxide co composition_co700 sh-ylgnbu-co-upper"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-ylgnbu-co-upper</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-ylgnbu-co-upper')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-ylgnbu-co-upper.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Carbon monoxide</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210123 carbon monoxide co composition_co_500hpa sh-all-co-500hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-co-500hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-co-500hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-co-500hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210123 carbon monoxide co composition_co_500hpa sh-viridis-co-500hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-viridis-co-500hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-viridis-co-500hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-viridis-co-500hpa.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total column Carbon monoxide</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210127 composition_co_totalcolumn sh-all-tcco tcco total column carbon monoxide"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-tcco</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-tcco')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-tcco.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Wildfire radiative power</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210099 composition_fire frpfire sh-all-fire wildfire radiative power"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-fire</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-fire')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-fire.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210099 composition_fire frpfire symb-all-fire wildfire radiative power"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">symb-all-fire</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'symb-all-fire')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/symb-all-fire.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Nitrogen dioxide</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210121 composition_no2_surface nitrogen dioxide no2 sh-all-no2-surface"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-no2-surface</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-no2-surface')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-no2-surface.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">GEMS Ozone</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210203 composition_o3_surface gems ozone go3 sh-all-o3-sfc"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-o3-sfc</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-o3-sfc')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-o3-sfc.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210203 composition_o3_surface gems ozone go3 sh-ylgnbu-o3-sfc"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-ylgnbu-o3-sfc</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-ylgnbu-o3-sfc')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-ylgnbu-o3-sfc.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">GEMS Total column ozone</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210206 composition_o3_totalcolumn gems total column ozone gtco3 sh-all-tco3"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-tco3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-tco3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-tco3.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Particulate matter d < 10 um</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210074 composition_pm10 particulate matter d < 10 um pm10 sh-all-pm10-defra-daqi"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-pm10-defra-daqi</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-pm10-defra-daqi')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-pm10-defra-daqi.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210074 composition_pm10 particulate matter d < 10 um pm10 sh-all-pmx-ncl-precip-11lev"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-pmx-ncl-precip-11lev</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-pmx-ncl-precip-11lev')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-pmx-ncl-precip-11lev.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Particulate matter d < 2.5 um</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210073 composition_pm2p5 particulate matter d < 2.5 um pm2p5 sh-all-pm2p5-defra-daqi"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-pm2p5-defra-daqi</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-pm2p5-defra-daqi')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-pm2p5-defra-daqi.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="210073 composition_pm2p5 particulate matter d < 2.5 um pm2p5 sh-all-pmx-regional"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-pmx-regional</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-pmx-regional')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-pmx-regional.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total column Sulphur dioxide</h2>

.. raw:: html

   <div class="ek-style-block" data-search="210126 composition_so2_totalcolumn sh-all-tcso2 tcso2 total column sulphur dioxide"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-tcso2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-tcso2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-tcso2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading"> UV biologically effective dose</h2>

.. raw:: html

   <div class="ek-style-block" data-search=" uv biologically effective dose 214002 composition_uvindex sh-all-uvindex uvbed"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-uvindex</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-uvindex')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-uvindex.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">2 metre temperature index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="132167 132201 132202 2 metre temperature index 2ti efi_2t_data maximum temperature at 2 metres index minimum temperature at 2 metres index mn2ti mx2ti sh-blured-fm1t1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-fm1t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-fm1t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-fm1t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="132167 132201 132202 2 metre temperature index 2ti efi_2t_data maximum temperature at 2 metres index minimum temperature at 2 metres index mn2ti mx2ti sh-efi2t-fm1t1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-efi2t-fm1t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-efi2t-fm1t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-efi2t-fm1t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="132167 132201 132202 2 metre temperature index 2ti efi_2t_data maximum temperature at 2 metres index minimum temperature at 2 metres index mn2ti mx2ti sh-efi2t-fm1t1lst-nc"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-efi2t-fm1t1lst-nc</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-efi2t-fm1t1lst-nc')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-efi2t-fm1t1lst-nc.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Convective available potential energy shear index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="132044 132059 capei capesi convective available potential energy index convective available potential energy shear index efi_capeshear_field sh-red-f05t1i01"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f05t1i01</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f05t1i01')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f05t1i01.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="132044 132059 capei capesi convective available potential energy index convective available potential energy shear index efi_capeshear_field mrk-efi-capes-f06t1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mrk-efi-capes-f06t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mrk-efi-capes-f06t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/mrk-efi-capes-f06t1.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="132044 132059 capei capesi convective available potential energy index convective available potential energy shear index efi_capeshear_field sh-efi-f05t1-nc"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-efi-f05t1-nc</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-efi-f05t1-nc')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-efi-f05t1-nc.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Snowfall index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="132144 efi_sf_field mrk-efi-tp-f06t1 sfi snowfall index"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mrk-efi-tp-f06t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mrk-efi-tp-f06t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/mrk-efi-tp-f06t1.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="132144 efi_sf_field mrk-efi-sf-f06t1 sfi snowfall index"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mrk-efi-sf-f06t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mrk-efi-sf-f06t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/mrk-efi-sf-f06t1.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">10 metre wind gust index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre speed index 10 metre wind gust index 10fgi 10wsi 132049 132165 efi_wg_field mrk-efi-wg-f06t1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mrk-efi-wg-f06t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mrk-efi-wg-f06t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/mrk-efi-wg-f06t1.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Accumulated freezing rain</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228216 accumulated freezing rain fzra sh-all-f05t100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f05t100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f05t100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f05t100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228216 accumulated freezing rain fzra sh-red-f001t10"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f001t10</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f001t10')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f001t10.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228216 accumulated freezing rain ct-blk-f005t25 fzra"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-f005t25</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-f005t25')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-f005t25.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Probability of a hurricane</h2>

.. raw:: html

   <div class="ek-style-block" data-search="131089 131090 131091 genesis-prob genesis_hr ph probability of a hurricane probability of a tropical depression probability of a tropical storm ptd pts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">genesis-prob</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'genesis-prob')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/genesis-prob.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131089 131090 131091 genesis-prob-light genesis_hr ph probability of a hurricane probability of a tropical depression probability of a tropical storm ptd pts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">genesis-prob-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'genesis-prob-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/genesis-prob-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131089 131090 131091 genesis-prob-dark genesis_hr ph probability of a hurricane probability of a tropical depression probability of a tropical storm ptd pts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">genesis-prob-dark</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'genesis-prob-dark')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/genesis-prob-dark.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131089 131090 131091 genesis_hr ph prob-red2blue probability of a hurricane probability of a tropical depression probability of a tropical storm ptd pts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">prob-red2blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'prob-red2blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/prob-red2blue.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131089 131090 131091 genesis_hr ph prob-blue2yellow probability of a hurricane probability of a tropical depression probability of a tropical storm ptd pts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">prob-blue2yellow</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'prob-blue2yellow')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/prob-blue2yellow.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131089 131090 131091 genesis_hr ph prob-green2yellow probability of a hurricane probability of a tropical depression probability of a tropical storm ptd pts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">prob-green2yellow</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'prob-green2yellow')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/prob-green2yellow.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">High cloud cover</h2>

.. raw:: html

   <div class="ek-style-block" data-search="188 hcc high cloud cover high_type_cloud_area_fraction transparency-white"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">transparency-white</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'transparency-white')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/transparency-white.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="188 hcc high cloud cover high_type_cloud_area_fraction sh-whi-f0t1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-whi-f0t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-whi-f0t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-whi-f0t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="188 hcc high cloud cover high_type_cloud_area_fraction sh-blugry-f0t1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blugry-f0t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blugry-f0t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blugry-f0t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="188 hcc high cloud cover high_type_cloud_area_fraction tran-whi-f03t1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">tran-whi-f03t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'tran-whi-f03t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/tran-whi-f03t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Height of convective cloud top</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228046 hcct height of convective cloud top sh-hcct-blk-f0t22000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-hcct-blk-f0t22000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-hcct-blk-f0t22000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-hcct-blk-f0t22000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228046 hcct height of convective cloud top sh-hcct-f0t22000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-hcct-f0t22000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-hcct-f0t22000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-hcct-f0t22000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">K index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260121 k index kindex kx sh-red-f15t60"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f15t60</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f15t60')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f15t60.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="260121 k index kindex kx sh-green-f15t60"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-green-f15t60</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-green-f15t60')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-green-f15t60.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="260121 ct-blk-f10-i10-t2 k index kindex kx"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-f10-i10-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-f10-i10-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-f10-i10-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Low cloud cover</h2>

.. raw:: html

   <div class="ek-style-block" data-search="164 186 248 cc cloud_area_fraction cloud_area_fraction_in_atmosphere_layer convective_cloud_area_fraction convective_cloud_area_fraction_in_atmosphere_layer fraction of cloud cover large_scale_cloud_area_fraction lcc low cloud cover low_type_cloud_area_fraction stratiform_cloud_area_fraction tcc total cloud cover total cloud fraction transparency-grey"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">transparency-grey</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'transparency-grey')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/transparency-grey.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="164 186 248 cc cloud_area_fraction cloud_area_fraction_in_atmosphere_layer convective_cloud_area_fraction convective_cloud_area_fraction_in_atmosphere_layer fraction of cloud cover large_scale_cloud_area_fraction lcc low cloud cover low_type_cloud_area_fraction sh-gry-f0t1lst stratiform_cloud_area_fraction tcc total cloud cover total cloud fraction"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-gry-f0t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-gry-f0t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-gry-f0t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="164 186 248 cc cloud_area_fraction cloud_area_fraction_in_atmosphere_layer convective_cloud_area_fraction convective_cloud_area_fraction_in_atmosphere_layer fraction of cloud cover large_scale_cloud_area_fraction lcc low cloud cover low_type_cloud_area_fraction sh-redgry-f0t1lst stratiform_cloud_area_fraction tcc total cloud cover total cloud fraction"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-redgry-f0t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-redgry-f0t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-redgry-f0t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="164 186 248 cc cloud_area_fraction cloud_area_fraction_in_atmosphere_layer convective_cloud_area_fraction convective_cloud_area_fraction_in_atmosphere_layer fraction of cloud cover large_scale_cloud_area_fraction lcc low cloud cover low_type_cloud_area_fraction stratiform_cloud_area_fraction tcc total cloud cover total cloud fraction tran-gry-f03t1lst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">tran-gry-f03t1lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'tran-gry-f03t1lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/tran-gry-f03t1lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mc 10Fg</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10fg 228005 49 mc_10fg mean10ws sh-mc-wind-f0t80"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-wind-f0t80</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-wind-f0t80')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-wind-f0t80.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10fg 228005 49 ct-mc-wind-f0t80-black mc_10fg mean10ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-wind-f0t80-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-wind-f0t80-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-wind-f0t80-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10fg 228005 49 ct-mc-wind-f0t80-blue mc_10fg mean10ws"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-wind-f0t80-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-wind-f0t80-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-wind-f0t80-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mc 2Tmean</h2>

.. raw:: html

   <div class="ek-style-block" data-search="201 202 228004 mc_2tmean mean2t mn2t mx2t sh-mc-t-fm80t60"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-t-fm80t60</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-t-fm80t60')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-t-fm80t60.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="201 202 228004 ct-mc-t-fm80t60-black mc_2tmean mean2t mn2t mx2t"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-t-fm80t60-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-t-fm80t60-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-t-fm80t60-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="201 202 228004 ct-mc-t-fm80t60-blue mc_2tmean mean2t mn2t mx2t"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-t-fm80t60-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-t-fm80t60-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-t-fm80t60-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Convective available potential energy</h2>

.. raw:: html

   <div class="ek-style-block" data-search="59 cape convective available potential energy mc_cape sh-mc-cape-f10t13000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-cape-f10t13000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-cape-f10t13000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-cape-f10t13000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="59 cape convective available potential energy ct-mc-cape-f10t13000-black mc_cape"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-cape-f10t13000-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-cape-f10t13000-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-cape-f10t13000-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="59 cape convective available potential energy ct-mc-cape-f10t13000-blue mc_cape"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-cape-f10t13000-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-cape-f10t13000-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-cape-f10t13000-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Convective available potential energy shear</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228044 capes convective available potential energy shear mc_capeshear sh-mc-capes-f10t4000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-capes-f10t4000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-capes-f10t4000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-capes-f10t4000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228044 capes convective available potential energy shear ct-mc-capes-f10t4000-black mc_capeshear"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-capes-f10t4000-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-capes-f10t4000-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-capes-f10t4000-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228044 capes convective available potential energy shear ct-mc-capes-f10t4000-blue mc_capeshear"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-capes-f10t4000-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-capes-f10t4000-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-capes-f10t4000-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Snowfall</h2>

.. raw:: html

   <div class="ek-style-block" data-search="144 lwe_thickness_of_snowfall_amount mc_sf sf sh-mc-sf-f01t100 snowfall"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-sf-f01t100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-sf-f01t100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-sf-f01t100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="144 ct-mc-sf-f01t100-black lwe_thickness_of_snowfall_amount mc_sf sf snowfall"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-sf-f01t100-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-sf-f01t100-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-sf-f01t100-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="144 ct-mc-sf-f01t100-blue lwe_thickness_of_snowfall_amount mc_sf sf snowfall"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-sf-f01t100-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-sf-f01t100-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-sf-f01t100-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Maximum of significant wave height</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140200 maximum of significant wave height maxswh mc_swh sh-mc-swh-f0t20"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-swh-f0t20</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-swh-f0t20')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-swh-f0t20.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140200 ct-mc-swh-f0t20-black maximum of significant wave height maxswh mc_swh"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-swh-f0t20-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-swh-f0t20-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-swh-f0t20-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140200 ct-mc-swh-f0t20-blue maximum of significant wave height maxswh mc_swh"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-swh-f0t20-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-swh-f0t20-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-swh-f0t20-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total precipitation</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228 mc_tp sh-mc-tp-f01t1000 total precipitation tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mc-tp-f01t1000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mc-tp-f01t1000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mc-tp-f01t1000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228 ct-mc-tp-f01t1000-black mc_tp total precipitation tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-tp-f01t1000-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-tp-f01t1000-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-tp-f01t1000-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228 ct-mc-tp-f01t1000-blue mc_tp total precipitation tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-mc-tp-f01t1000-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-mc-tp-f01t1000-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-mc-tp-f01t1000-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mcc</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228164 500046 500307 502341 mcc transparency-lightgrey-100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">transparency-lightgrey-100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'transparency-lightgrey-100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/transparency-lightgrey-100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mean sea level pressure</h2>

.. raw:: html

   <div class="ek-style-block" data-search="151 air_pressure_at_sea_level mean sea level pressure mean-sea-level-pressure msl mslp-contour-pa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mslp-contour-pa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mslp-contour-pa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/mslp-contour-pa.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="151 air_pressure_at_sea_level mean sea level pressure mean-sea-level-pressure msl mslp-contour-hpa"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">mslp-contour-hpa</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'mslp-contour-hpa')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/mslp-contour-hpa.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Temperature anomaly</h2>

.. raw:: html

   <div class="ek-style-block" data-search="171130 mofc_10_t_anomaly t-upper-anomaly ta temperature anomaly"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t-upper-anomaly</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't-upper-anomaly')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t-upper-anomaly.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="171130 mofc_10_t_anomaly sh-anomaly-rb-m20t20 ta temperature anomaly"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-anomaly-rb-m20t20</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-anomaly-rb-m20t20')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-anomaly-rb-m20t20.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">2 metre temperature probability</h2>

.. raw:: html

   <div class="ek-style-block" data-search="131139 131151 131167 131228 2 metre temperature probability 2tp mean sea level pressure probability mofc_2t_pdist mslpp sh-mf-pdist soil temperature level 1 probability stl1p total precipitation probability tpp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mf-pdist</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mf-pdist')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mf-pdist.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131139 131151 131167 131228 2 metre temperature probability 2tp mean sea level pressure probability mofc_2t_pdist mslpp sh-mf-pdist-2 soil temperature level 1 probability stl1p total precipitation probability tpp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mf-pdist-2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mf-pdist-2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mf-pdist-2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131139 131151 131167 131228 2 metre temperature probability 2tp mean sea level pressure probability mofc_2t_pdist mslpp sh-mf-2t-tercile soil temperature level 1 probability stl1p total precipitation probability tpp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mf-2t-tercile</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mf-2t-tercile')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mf-2t-tercile.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131139 131151 131167 131228 2 metre temperature probability 2tp mean sea level pressure probability mofc_2t_pdist mslpp sh-mf-pdist-quintile soil temperature level 1 probability stl1p total precipitation probability tpp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mf-pdist-quintile</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mf-pdist-quintile')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mf-pdist-quintile.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="131139 131151 131167 131228 2 metre temperature probability 2tp mean sea level pressure probability mofc_2t_pdist mslpp sh-mf-pdist-decile soil temperature level 1 probability stl1p total precipitation probability tpp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-mf-pdist-decile</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-mf-pdist-decile')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-mf-pdist-decile.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Sunshine duration anomalous rate of accumulation</h2>

.. raw:: html

   <div class="ek-style-block" data-search="173189 mofc_sduration_anomaly sh-rb-fm100t100 sundara sunshine duration anomalous rate of accumulation"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rb-fm100t100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rb-fm100t100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rb-fm100t100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="173189 ct-blk-i4-t2-sduration mofc_sduration_anomaly sundara sunshine duration anomalous rate of accumulation"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i4-t2-sduration</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i4-t2-sduration')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i4-t2-sduration.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="173189 ct-blk-i4-t2-dashed-sduration mofc_sduration_anomaly sundara sunshine duration anomalous rate of accumulation"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i4-t2-dashed-sduration</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i4-t2-dashed-sduration')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i4-t2-dashed-sduration.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Geopotential anomaly</h2>

.. raw:: html

   <div class="ek-style-block" data-search="171129 geopotential anomaly mofc_z500_anomaly sh-range-fm40t40 za"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-range-fm40t40</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-range-fm40t40')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-range-fm40t40.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Geopotential</h2>

.. raw:: html

   <div class="ek-style-block" data-search="129 ct-blk-i6-t2 geopotential mofc_z500_weekly_mean z"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i6-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i6-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i6-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="129 ct-red-i5-t2 geopotential mofc_z500_weekly_mean z"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-red-i5-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-red-i5-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-red-i5-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="129 ct-green-i5-t2 geopotential mofc_z500_weekly_mean z"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-green-i5-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-green-i5-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-green-i5-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="129 ct-brn-i4-t2 geopotential mofc_z500_weekly_mean z"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-brn-i4-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-brn-i4-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-brn-i4-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="129 ct-blk-i2-t4 geopotential mofc_z500_weekly_mean z"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i2-t4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i2-t4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i2-t4.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="129 ct-green-i2-t4 geopotential mofc_z500_weekly_mean z"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-green-i2-t4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-green-i2-t4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-green-i2-t4.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mean sea level pressure</h2>

.. raw:: html

   <div class="ek-style-block" data-search="151 260074 air_pressure_at_mean_sea_level air_pressure_at_sea_level ct-blk-i5-t1-hilo mean sea level pressure msl prmsl sea level pressure"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i5-t1-hilo</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i5-t1-hilo')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i5-t1-hilo.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="151 260074 air_pressure_at_mean_sea_level air_pressure_at_sea_level ct-blk-i5-t1-hilo-label mean sea level pressure msl prmsl sea level pressure"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i5-t1-hilo-label</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i5-t1-hilo-label')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i5-t1-hilo-label.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="151 260074 air_pressure_at_mean_sea_level air_pressure_at_sea_level ct-blk-i1-t1 mean sea level pressure msl prmsl sea level pressure"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i1-t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i1-t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i1-t1.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="151 260074 air_pressure_at_mean_sea_level air_pressure_at_sea_level ct-blk-i1-t2 mean sea level pressure msl prmsl sea level pressure"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i1-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i1-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i1-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="151 260074 air_pressure_at_mean_sea_level air_pressure_at_sea_level ct-red-i5-t4 mean sea level pressure msl prmsl sea level pressure"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-red-i5-t4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-red-i5-t4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-red-i5-t4.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Msl Spread</h2>

.. raw:: html

   <div class="ek-style-block" data-search="151 msl msl_spread sh-blu-f02t50"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f02t50</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f02t50')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f02t50.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="151 msl msl_spread sh-range-f02t50"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-range-f02t50</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-range-f02t50')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-range-f02t50.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Nc Gh100</h2>

.. raw:: html

   <div class="ek-style-block" data-search="156 ct-blk-i8-t2 gh nc_gh100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i8-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i8-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i8-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="156 ct-blk-i10-t2 gh nc_gh100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i10-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i10-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i10-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Nc Sd</h2>

.. raw:: html

   <div class="ek-style-block" data-search="nc_sd snow-1to10000 thickness_of_convective_snowfall_amount thickness_of_snowfall_amount thickness_of_stratiform_snowfall_amount"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">snow-1to10000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'snow-1to10000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/snow-1to10000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="nc_sd snow-1to1000-whi thickness_of_convective_snowfall_amount thickness_of_snowfall_amount thickness_of_stratiform_snowfall_amount"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">snow-1to1000-whi</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'snow-1to1000-whi')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/snow-1to1000-whi.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Nc Tp Interval</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-blured-f05t300lst stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-f05t300lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-f05t300lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-f05t300lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-blured-f1t100lst stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-f1t100lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-f1t100lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-f1t100lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-blured-f1t100lst-dark stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-f1t100lst-dark</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-f1t100lst-dark')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-f1t100lst-dark.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-grnvio-f1t100lst stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grnvio-f1t100lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grnvio-f1t100lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grnvio-f1t100lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-all-f05t300lst stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f05t300lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f05t300lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f05t300lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-blured-f01t500lst stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-f01t500lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-f01t500lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-f01t500lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount large_scale_precipitation_amount nc_tp_interval precipitation_amount sh-blured-f0t300 stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blured-f0t300</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blured-f0t300')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blured-f0t300.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228228 convective_precipitation_amount ct-blumag-lst large_scale_precipitation_amount nc_tp_interval precipitation_amount stratiform_precipitation_amount tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blumag-lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blumag-lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blumag-lst.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Specific humidity</h2>

.. raw:: html

   <div class="ek-style-block" data-search="133 q q1000 sh-spechum-option1 specific humidity specific_humidity"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-spechum-option1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-spechum-option1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-spechum-option1.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="133 q q1000 sh-spechum-option2 specific humidity specific_humidity"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-spechum-option2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-spechum-option2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-spechum-option2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="133 q q1000 sh-spechum-option3 specific humidity specific_humidity"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-spechum-option3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-spechum-option3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-spechum-option3.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="133 ct-blk-i2-t2 q q1000 specific humidity specific_humidity"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-blk-i2-t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-blk-i2-t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-blk-i2-t2.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="133 q q1000 spechum-extra1 specific humidity specific_humidity"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">spechum-extra1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'spechum-extra1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/spechum-extra1.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Relative humidity</h2>

.. raw:: html

   <div class="ek-style-block" data-search="157 260242 2r r relative humidity relative_humidity rh1000 sh-grnblu-f65t100i15"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grnblu-f65t100i15</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grnblu-f65t100i15')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grnblu-f65t100i15.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="157 260242 2r r relative humidity relative_humidity rh1000 sh-grnblu-f65t100i15-light"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grnblu-f65t100i15-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grnblu-f65t100i15-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grnblu-f65t100i15-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="157 260242 2r ct-grnblu-f65t100i15 r relative humidity relative_humidity rh1000"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-grnblu-f65t100i15</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-grnblu-f65t100i15')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-grnblu-f65t100i15.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mean discharge in the last 6 hours</h2>

.. raw:: html

   <div class="ek-style-block" data-search="240023 mean discharge in the last 24 hours mean discharge in the last 6 hours river-discharge river-discharge-blues-europe"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">river-discharge-blues-europe</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'river-discharge-blues-europe')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/river-discharge-blues-europe.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="240023 mean discharge in the last 24 hours mean discharge in the last 6 hours river-discharge river-discharge-blues-global"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">river-discharge-blues-global</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'river-discharge-blues-global')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/river-discharge-blues-global.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">sea surface temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="34 sea surface temperature sea-surface-temperature sea_surface_skin_temperature sea_surface_temperature sst sst-spectral-celsius"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sst-spectral-celsius</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sst-spectral-celsius')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sst-spectral-celsius.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="34 sea surface temperature sea-surface-temperature sea_surface_skin_temperature sea_surface_temperature sst sst-spectral-kelvin"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sst-spectral-kelvin</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sst-spectral-kelvin')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sst-spectral-kelvin.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Sea-ice cover</h2>

.. raw:: html

   <div class="ek-style-block" data-search="31 ci sea ice area fraction sea-ice cover sea_ice_area_fraction sea_ice_cover sic-grey"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sic-grey</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sic-grey')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sic-grey.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="31 ci sea ice area fraction sea-ice cover sea_ice_area_fraction sea_ice_cover sic-25to100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sic-25to100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sic-25to100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sic-25to100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="31 ci sea ice area fraction sea-ice cover sea_ice_area_fraction sea_ice_cover transparent-ice"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">transparent-ice</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'transparent-ice')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/transparent-ice.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="31 ci sea ice area fraction sea-ice cover sea_ice_area_fraction sea_ice_cover sic-10to100"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sic-10to100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sic-10to100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sic-10to100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Cloudy brightness temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260510 500340 clbt cloudy brightness temperature sim-image-ir-fixed-range sim_image_ir"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sim-image-ir-fixed-range</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sim-image-ir-fixed-range')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sim-image-ir-fixed-range.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Cloudy brightness temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260510 500346 clbt cloudy brightness temperature sim-image-wv-fixed-range sim_image_wv"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sim-image-wv-fixed-range</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sim-image-wv-fixed-range')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sim-image-wv-fixed-range.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Sim Image Wv Ch6</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260510 clbt sim-image-wv-500 sim_image_wv_ch6"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sim-image-wv-500</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sim-image-wv-500')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sim-image-wv-500.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Snow Water Equivalent</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228141 sd snow-water-equivalent snow-water-equivalent-kg-m2"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">snow-water-equivalent-kg-m2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'snow-water-equivalent-kg-m2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/snow-water-equivalent-kg-m2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Soil Wetness Index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="231026 soil-wetness-greens soil-wetness-index swir"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">soil-wetness-greens</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'soil-wetness-greens')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/soil-wetness-greens.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Sot Tp N90</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10fgi 10wsi 132044 132049 132059 132144 132165 132167 132201 132202 132216 132228 2ti capei capesi ct-sot-black-f0t8t1 maxswhi mn2ti mx2ti sfi sot_tp_n90 tpi"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-sot-black-f0t8t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-sot-black-f0t8t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-sot-black-f0t8t1.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10fgi 10wsi 132044 132049 132059 132144 132165 132167 132201 132202 132216 132228 2ti capei capesi ct-sot-blue-f0t8t1 maxswhi mn2ti mx2ti sfi sot_tp_n90 tpi"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-sot-blue-f0t8t1</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-sot-blue-f0t8t1')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-sot-blue-f0t8t1.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Sea surface temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="34 sea surface temperature sea_surface_skin_temperature sea_surface_temperature sh-sst-fm2t36i2 sst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-sst-fm2t36i2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-sst-fm2t36i2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-sst-fm2t36i2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="34 sea surface temperature sea_surface_skin_temperature sea_surface_temperature sh-sst-fm5t45 sst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-sst-fm5t45</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-sst-fm5t45')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-sst-fm5t45.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="34 ct-sst-blk-fm2t36i2-i4 sea surface temperature sea_surface_skin_temperature sea_surface_temperature sst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-sst-blk-fm2t36i2-i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-sst-blk-fm2t36i2-i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-sst-blk-fm2t36i2-i4.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="34 ct-sst-blue-fm2t36i2-i4 sea surface temperature sea_surface_skin_temperature sea_surface_temperature sst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-sst-blue-fm2t36i2-i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-sst-blue-fm2t36i2-i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-sst-blue-fm2t36i2-i4.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="34 ct-sst-multicolour sea surface temperature sea_surface_skin_temperature sea_surface_temperature sst"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-sst-multicolour</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-sst-multicolour')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-sst-multicolour.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">2m temperature anomaly of at least +2K</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-blup-f0t100lst stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blup-f0t100lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blup-f0t100lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blup-f0t100lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-blup-f0t100lst-light stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blup-f0t100lst-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blup-f0t100lst-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blup-f0t100lst-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-rgb-f5t100 stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rgb-f5t100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rgb-f5t100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rgb-f5t100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-rgb-transparent-f5t100 stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rgb-transparent-f5t100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rgb-transparent-f5t100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rgb-transparent-f5t100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-rgb-transparent25-f5t100 stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-rgb-transparent25-f5t100</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-rgb-transparent25-f5t100')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-rgb-transparent25-f5t100.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-grn-f0t100lst stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grn-f0t100lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grn-f0t100lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grn-f0t100lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-grn-f0t100lst-light stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grn-f0t100lst-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grn-f0t100lst-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grn-f0t100lst-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-red-f0t100lst stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f0t100lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f0t100lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f0t100lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 mean sea level pressure anomaly of at least 0 pa mslag0 sh-red-f0t100lst-light stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f0t100lst-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f0t100lst-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f0t100lst-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 ct-prob-black-f5t100t2 mean sea level pressure anomaly of at least 0 pa mslag0 stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-prob-black-f5t100t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-prob-black-f5t100t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-prob-black-f5t100t2.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust of at least 10 m/s 10 metre wind gust of at least 15 m/s 10 metre wind gust of at least 20 m/s 10 metre wind gust of at least 25 m/s 10 metre wind speed of at least 10 m/s 10 metre wind speed of at least 15 m/s 10fgg10 10fgg15 10fgg20 10fgg25 131001 131002 131003 131004 131005 131006 131007 131008 131009 131010 131060 131061 131062 131063 131064 131065 131066 131067 131068 131069 131070 131071 131072 131073 2 metre temperature less than 273.15 k 2m temperature anomaly of at least +1k 2m temperature anomaly of at least +2k 2m temperature anomaly of at least 0k 2m temperature anomaly of at most -1k 2m temperature anomaly of at most -2k 2tag0 2tag1 2tag2 2talm1 2talm2 2tl273 ct-prob-blue-f5t100t2 mean sea level pressure anomaly of at least 0 pa mslag0 stag0 surface temperature anomaly of at least 0k swh_prob_data total precipitation anomaly of at least 0 mm total precipitation anomaly of at least 10 mm total precipitation anomaly of at least 20 mm total precipitation less than 0.1 mm total precipitation of at least 1 mm total precipitation of at least 10 mm total precipitation of at least 20 mm total precipitation of at least 5 mm total precipitation rate less than 1 mm/day total precipitation rate of at least 3 mm/day total precipitation rate of at least 5 mm/day tpag0 tpag10 tpag20 tpg1 tpg10 tpg20 tpg5 tpl01 tprg3 tprg5 tprl1"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-prob-blue-f5t100t2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-prob-blue-f5t100t2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-prob-blue-f5t100t2.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t100 t100-sh-all-fm96tm8i4 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t100-sh-all-fm96tm8i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't100-sh-all-fm96tm8i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t100-sh-all-fm96tm8i4.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t100 t100-ct-red-i2-dash temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t100-ct-red-i2-dash</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't100-ct-red-i2-dash')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t100-ct-red-i2-dash.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t100 t100-sh-gry-fm72t56lst temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t100-sh-gry-fm72t56lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't100-sh-gry-fm72t56lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t100-sh-gry-fm72t56lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t100 t100-sh-all-fm80t56i4-v2 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t100-sh-all-fm80t56i4-v2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't100-sh-all-fm80t56i4-v2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t100-sh-all-fm80t56i4-v2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t100 t100-ct-red-i4-t3 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t100-ct-red-i4-t3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't100-ct-red-i4-t3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t100-ct-red-i4-t3.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t3 t3-sh-all-fm80t16i4 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t3-sh-all-fm80t16i4</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't3-sh-all-fm80t16i4')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t3-sh-all-fm80t16i4.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t3 t3-ct-red-i2-dash temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t3-ct-red-i2-dash</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't3-ct-red-i2-dash')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t3-ct-red-i2-dash.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t3 t3-sh-all-fm50t58i2 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t3-sh-all-fm50t58i2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't3-sh-all-fm50t58i2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t3-sh-all-fm50t58i2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t3 t3-sh-gry-fm72t56lst temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t3-sh-gry-fm72t56lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't3-sh-gry-fm72t56lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t3-sh-gry-fm72t56lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t3 t3-sh-all-fm80t56i4-v2 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t3-sh-all-fm80t56i4-v2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't3-sh-all-fm80t56i4-v2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t3-sh-all-fm80t56i4-v2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature t t3 t3-ct-red-i4-t3 temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">t3-ct-red-i4-t3</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 't3-ct-red-i4-t3')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/t3-ct-red-i4-t3.png
   :alt: contour line sample

*(Levels are determined from data at plot time)*

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature sh-blu-f008t25 t t850_spread temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f008t25</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f008t25')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f008t25.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="130 air_temperature sh-range-f008to25 t t850_spread temperature"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-range-f008to25</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-range-f008to25')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-range-f008to25.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total precipitation</h2>

.. raw:: html

   <div class="ek-style-block" data-search="228 precipitation-turbo-mm total precipitation total-precipitation total_precipitation tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">precipitation-turbo-mm</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'precipitation-turbo-mm')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/precipitation-turbo-mm.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228 precipitation-turbo-m total precipitation total-precipitation total_precipitation tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">precipitation-turbo-m</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'precipitation-turbo-m')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/precipitation-turbo-m.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="228 precipitation-turbo-kg-m2 total precipitation total-precipitation total_precipitation tp"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">precipitation-turbo-kg-m2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'precipitation-turbo-kg-m2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/precipitation-turbo-kg-m2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total Runoff Water Equivalent</h2>

.. raw:: html

   <div class="ek-style-block" data-search="231002 rowe runoff-blues-kg-m2 total-runoff-water-equivalent"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">runoff-blues-kg-m2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'runoff-blues-kg-m2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/runoff-blues-kg-m2.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Total totals index</h2>

.. raw:: html

   <div class="ek-style-block" data-search="260123 sh-red-f44t70 total totals index totalx"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f44t70</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f44t70')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f44t70.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="260123 sh-green-f44t70 total totals index totalx"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-green-f44t70</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-green-f44t70')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-green-f44t70.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Precipitation rate</h2>

.. raw:: html

   <div class="ek-style-block" data-search="174142 174143 228218 228219 228220 228221 228222 228223 228224 228225 228226 228227 260048 3059 3064 500052 500132 500145 convective rain rate convective rainfall rate convective snowfall rate water equivalent crfrate crr csfr large scale rain rate large scale rainfall rate large scale snowfall rate water equivalent lsrr lsrrate lssfr maximum total precipitation rate in the last 3 hours maximum total precipitation rate in the last 6 hours maximum total precipitation rate since previous post-processing minimum total precipitation rate in the last 3 hours minimum total precipitation rate in the last 6 hours minimum total precipitation rate since previous post-processing mntpr mntpr3 mntpr6 mxtpr mxtpr3 mxtpr6 prate precipitation rate sh-prate-radarlike-grided snow fall rate water equivalent srweq tp_rate tprate"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-prate-radarlike-grided</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-prate-radarlike-grided')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-prate-radarlike-grided.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="174142 174143 228218 228219 228220 228221 228222 228223 228224 228225 228226 228227 260048 3059 3064 500052 500132 500145 convective rain rate convective rainfall rate convective snowfall rate water equivalent crfrate crr csfr large scale rain rate large scale rainfall rate large scale snowfall rate water equivalent lsrr lsrrate lssfr maximum total precipitation rate in the last 3 hours maximum total precipitation rate in the last 6 hours maximum total precipitation rate since previous post-processing minimum total precipitation rate in the last 3 hours minimum total precipitation rate in the last 6 hours minimum total precipitation rate since previous post-processing mntpr mntpr3 mntpr6 mxtpr mxtpr3 mxtpr6 prate precipitation rate sh-prate-radarlike-grided-f01 snow fall rate water equivalent srweq tp_rate tprate"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-prate-radarlike-grided-f01</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-prate-radarlike-grided-f01')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-prate-radarlike-grided-f01.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="174142 174143 228218 228219 228220 228221 228222 228223 228224 228225 228226 228227 260048 3059 3064 500052 500132 500145 convective rain rate convective rainfall rate convective snowfall rate water equivalent crfrate crr csfr large scale rain rate large scale rainfall rate large scale snowfall rate water equivalent lsrr lsrrate lssfr maximum total precipitation rate in the last 3 hours maximum total precipitation rate in the last 6 hours maximum total precipitation rate since previous post-processing minimum total precipitation rate in the last 3 hours minimum total precipitation rate in the last 6 hours minimum total precipitation rate since previous post-processing mntpr mntpr3 mntpr6 mxtpr mxtpr3 mxtpr6 prate precipitation rate sh-prate-radarlike snow fall rate water equivalent srweq tp_rate tprate"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-prate-radarlike</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-prate-radarlike')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-prate-radarlike.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Visibility</h2>

.. raw:: html

   <div class="ek-style-block" data-search="3020 sh-navy-f0t13500 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-navy-f0t13500</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-navy-f0t13500')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-navy-f0t13500.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3020 sh-vis-f0t1500 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-vis-f0t1500</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-vis-f0t1500')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-vis-f0t1500.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3020 sh-vis-f0t100000 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-vis-f0t100000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-vis-f0t100000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-vis-f0t100000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3020 sh-red-f0t90000 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f0t90000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f0t90000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f0t90000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3020 sh-grey-f0t90000 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grey-f0t90000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grey-f0t90000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grey-f0t90000.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3020 ct-navy-f0t13500 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-navy-f0t13500</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-navy-f0t13500')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-navy-f0t13500.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3020 ct-vis-blk-f0t10000 vis visibility"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-vis-blk-f0t10000</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-vis-blk-f0t10000')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-vis-blk-f0t10000.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Mean period of total swell</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140239 mean period of total swell mpts sh-all-f0t18i1-5 wave_mpts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f0t18i1-5</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f0t18i1-5')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f0t18i1-5.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140239 mean period of total swell mpts sh-grn-f0t18i1-5 wave_mpts"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-grn-f0t18i1-5</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-grn-f0t18i1-5')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-grn-f0t18i1-5.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Significant wave height of all waves with period larger than 10s</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140120 sh-all-f0t20lst sh10 significant wave height of all waves with period larger than 10s wave_sh10"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f0t20lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f0t20lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f0t20lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140120 sh-blu-f0t20lst sh10 significant wave height of all waves with period larger than 10s wave_sh10"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f0t20lst</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f0t20lst')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f0t20lst.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140120 sh-blu-f0t20lst-light sh10 significant wave height of all waves with period larger than 10s wave_sh10"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f0t20lst-light</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f0t20lst-light')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f0t20lst-light.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140120 sh-blu-f0t20lst-warn sh10 significant wave height of all waves with period larger than 10s wave_sh10"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f0t20lst-warn</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f0t20lst-warn')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f0t20lst-warn.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140120 sh-douglas-sea-scale sh10 significant wave height of all waves with period larger than 10s wave_sh10"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-douglas-sea-scale</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-douglas-sea-scale')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-douglas-sea-scale.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Significant wave height of all waves with periods within the inclusive range from 10 to 12 seconds</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140114 h1012 sh-wave-f0t10-red significant wave height of all waves with periods within the inclusive range from 10 to 12 seconds wave_sh1012"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f0t10-red</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f0t10-red')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f0t10-red.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140114 h1012 sh-wave-f0t10-purple significant wave height of all waves with periods within the inclusive range from 10 to 12 seconds wave_sh1012"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f0t10-purple</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f0t10-purple')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f0t10-purple.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Significant wave height of all waves with periods within the inclusive range from 21 to 25 seconds</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140118 h2125 sh-wave-f005t5-rose significant wave height of all waves with periods within the inclusive range from 21 to 25 seconds wave_sh2125"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f005t5-rose</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f005t5-rose')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f005t5-rose.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140118 h2125 sh-wave-f005t5-red significant wave height of all waves with periods within the inclusive range from 21 to 25 seconds wave_sh2125"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f005t5-red</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f005t5-red')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f005t5-red.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140118 h2125 sh-wave-f005t5-purple significant wave height of all waves with periods within the inclusive range from 21 to 25 seconds wave_sh2125"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f005t5-purple</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f005t5-purple')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f005t5-purple.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140118 ct-t2-f005t5-black h2125 significant wave height of all waves with periods within the inclusive range from 21 to 25 seconds wave_sh2125"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-t2-f005t5-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-t2-f005t5-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-t2-f005t5-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140118 ct-t2-f005t5-blue h2125 significant wave height of all waves with periods within the inclusive range from 21 to 25 seconds wave_sh2125"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-t2-f005t5-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-t2-f005t5-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-t2-f005t5-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Significant wave height of all waves with periods within the inclusive range from 25 to 30 seconds</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140119 h2530 sh-wave-f002t1-blue significant wave height of all waves with periods within the inclusive range from 25 to 30 seconds wave_sh2530"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f002t1-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f002t1-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f002t1-blue.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140119 h2530 sh-wave-f002t1-red significant wave height of all waves with periods within the inclusive range from 25 to 30 seconds wave_sh2530"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f002t1-red</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f002t1-red')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f002t1-red.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140119 h2530 sh-wave-f002t1-purple significant wave height of all waves with periods within the inclusive range from 25 to 30 seconds wave_sh2530"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-wave-f002t1-purple</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-wave-f002t1-purple')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-wave-f002t1-purple.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140119 ct-t2-f002t1-black h2530 significant wave height of all waves with periods within the inclusive range from 25 to 30 seconds wave_sh2530"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-t2-f002t1-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-t2-f002t1-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-t2-f002t1-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140119 ct-t2-f002t1-blue h2530 significant wave height of all waves with periods within the inclusive range from 25 to 30 seconds wave_sh2530"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-t2-f002t1-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-t2-f002t1-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-t2-f002t1-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Significant height of wind waves</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140234 sh-blu-f0t20-douglas shww significant height of wind waves wave_shww"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f0t20-douglas</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f0t20-douglas')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f0t20-douglas.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Wave energy flux magnitude</h2>

.. raw:: html

   <div class="ek-style-block" data-search="140112 sh-red-f0t640-energy wave energy flux magnitude wave_wefm wefxm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-red-f0t640-energy</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-red-f0t640-energy')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-red-f0t640-energy.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140112 sh-all-f0t640-energy wave energy flux magnitude wave_wefm wefxm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-all-f0t640-energy</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-all-f0t640-energy')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-all-f0t640-energy.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140112 ct-t3-f0t640-black wave energy flux magnitude wave_wefm wefxm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-t3-f0t640-black</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-t3-f0t640-black')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-t3-f0t640-black.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="140112 ct-t3-f0t640-blue wave energy flux magnitude wave_wefm wefxm"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-t3-f0t640-blue</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-t3-f0t640-blue')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-t3-f0t640-blue.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Potential temperature</h2>

.. raw:: html

   <div class="ek-style-block" data-search="3 ct-black-i2-solid potential temperature pt wbpt850"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-black-i2-solid</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-black-i2-solid')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-black-i2-solid.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3 ct-black-i4-solid potential temperature pt wbpt850"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-black-i4-solid</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-black-i4-solid')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-black-i4-solid.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="3 ct-multicolour-fm20t40i2 potential temperature pt wbpt850"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">ct-multicolour-fm20t40i2</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'ct-multicolour-fm20t40i2')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/ct-multicolour-fm20t40i2.png
   :alt: contour line sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">10 metre wind gust in the last 6 hours</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 6 hours 10fg6 123 wind-gust-6h-m-s wind-gust-at-10m-in-last-6-hours"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">wind-gust-6h-m-s</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'wind-gust-6h-m-s')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/wind-gust-6h-m-s.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-style-block" data-search="10 metre wind gust in the last 6 hours 10fg6 123 wind-gust-at-10m-in-last-6-hours wind-speed-10m-m-s"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">wind-speed-10m-m-s</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'wind-speed-10m-m-s')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/wind-speed-10m-m-s.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Wind</h2>

.. raw:: html

   <div class="ek-style-block" data-search="10u 10v 165 166 500028 500030 u v wind wind-quiver-m-s"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">wind-quiver-m-s</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'wind-quiver-m-s')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/wind-quiver-m-s.png
   :alt: vector style sample

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   <div class="ek-section">
   <h2 class="ek-section-heading">Z300 Spread</h2>

.. raw:: html

   <div class="ek-style-block" data-search="129 sh-blu-f03t75 z z300_spread"><div class="ek-style-entry"><div class="ek-style-left"><code class="ek-style-name">sh-blu-f03t75</code></div><button class="ek-copy-btn" onclick="ekCopy(this, 'sh-blu-f03t75')"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" /><path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" /></svg> Copy this style name</button></div>

.. image:: _static/styles/sh-blu-f03t75.png
   :alt: colorbar preview

.. raw:: html

   </div>

.. raw:: html

   </div>


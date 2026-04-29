.. _domains-gallery:

Named domains
=============

Any of the names below can be passed as the ``domain`` argument to any
earthkit-plots map function.

Use the dropdowns below to preview the map extent and default projection
chosen automatically for each domain, along with the code snippet to reproduce it.

.. raw:: html

   <style>
   #ek-domain-wrap { margin-bottom: 1.5em; }
   .ek-domain-row {
     display: flex; gap: 0.75em; align-items: center;
     flex-wrap: wrap; margin-bottom: 0.6em;
   }
   .ek-domain-label {
     font-size: 0.9em; color: #555; white-space: nowrap;
   }
   .ek-domain-sel {
     padding: 6px 10px; font-size: 0.95em;
     border: 1px solid #ccc; border-radius: 4px;
     min-width: 200px;
   }
   #ek-domain-img-wrap { margin-top: 1em; }
   #ek-domain-img {
     max-width: 100%; border: 1px solid #ddd; border-radius: 4px;
   }
   #ek-domain-error {
     color: #a00; font-size: 0.9em; margin-top: 0.5em; display: none;
   }
   #ek-domain-code-wrap {
     position: relative; margin-top: 1.2em;
   }
   #ek-domain-code {
     background: #2b2b2b; border: 1px solid #444; color: #d4d4d4;
     border-radius: 4px; padding: 0.8em 1em; font-family: monospace;
     font-size: 1.1em; white-space: pre; margin: 0;
   }
   #ek-domain-code .ek-str { color: #e06c75; }
   #ek-domain-code .ek-eq  { color: #c792ea; }
   #ek-domain-copy {
     position: absolute; top: 0.5em; right: 0.5em;
     width: 1.1em; height: 1.1em; cursor: pointer; opacity: 0.4;
     background: none; border: none; padding: 0; filter: invert(1);
   }
   #ek-domain-copy:hover { opacity: 0.9; }
   </style>
   <div id="ek-domain-wrap">
     <div class="ek-domain-row">
       <span class="ek-domain-label">Category:</span>
       <select id="ek-cat-select" class="ek-domain-sel" onchange="ekCatSwap(this)">
         <option value="countries">Countries</option>
         <option value="regions">Other regions</option>
       </select>
     </div>
     <div class="ek-domain-row">
       <span class="ek-domain-label">Domain:</span>
       <select id="ek-domain-select" class="ek-domain-sel" onchange="ekDomainSwap(this)">
       </select>
     </div>
     <div id="ek-domain-img-wrap">
       <img id="ek-domain-img" src="" alt="">
       <div id="ek-domain-error"></div>
     </div>
     <div id="ek-domain-code-wrap">
       <pre id="ek-domain-code"></pre>
       <img id="ek-domain-copy" src="_static/copy.svg" alt="Copy" title="Copy" onclick="ekCopyCode()">
     </div>
   </div>
   <script>
   var EK_DOMAIN_BASE = '_static/domains/';
   var EK_LISTS = {
     countries: [
      {name: "Afghanistan", slug: "afghanistan"},
      {name: "Albania", slug: "albania"},
      {name: "Algeria", slug: "algeria"},
      {name: "Angola", slug: "angola"},
      {name: "Antarctica", slug: "antarctica"},
      {name: "Argentina", slug: "argentina"},
      {name: "Armenia", slug: "armenia"},
      {name: "Australia", slug: "australia"},
      {name: "Austria", slug: "austria"},
      {name: "Azerbaijan", slug: "azerbaijan"},
      {name: "Bahamas", slug: "bahamas"},
      {name: "Bangladesh", slug: "bangladesh"},
      {name: "Belarus", slug: "belarus"},
      {name: "Belgium", slug: "belgium"},
      {name: "Belize", slug: "belize"},
      {name: "Benin", slug: "benin"},
      {name: "Bhutan", slug: "bhutan"},
      {name: "Bolivia", slug: "bolivia"},
      {name: "Bosnia and Herzegovina", slug: "bosnia_and_herzegovina"},
      {name: "Botswana", slug: "botswana"},
      {name: "Brazil", slug: "brazil"},
      {name: "Brunei Darussalam", slug: "brunei_darussalam"},
      {name: "Bulgaria", slug: "bulgaria"},
      {name: "Burkina Faso", slug: "burkina_faso"},
      {name: "Burundi", slug: "burundi"},
      {name: "Cambodia", slug: "cambodia"},
      {name: "Cameroon", slug: "cameroon"},
      {name: "Canada", slug: "canada"},
      {name: "Central African Republic", slug: "central_african_republic"},
      {name: "Chad", slug: "chad"},
      {name: "Chile", slug: "chile"},
      {name: "China", slug: "china"},
      {name: "Colombia", slug: "colombia"},
      {name: "Costa Rica", slug: "costa_rica"},
      {name: "Croatia", slug: "croatia"},
      {name: "Cuba", slug: "cuba"},
      {name: "Cyprus", slug: "cyprus"},
      {name: "Czech Republic", slug: "czech_republic"},
      {name: "Côte d'Ivoire", slug: "côte_d_ivoire"},
      {name: "Dem. Rep. Korea", slug: "dem_rep_korea"},
      {name: "Democratic Republic of the Congo", slug: "democratic_republic_of_the_congo"},
      {name: "Denmark", slug: "denmark"},
      {name: "Djibouti", slug: "djibouti"},
      {name: "Dominican Republic", slug: "dominican_republic"},
      {name: "Ecuador", slug: "ecuador"},
      {name: "Egypt", slug: "egypt"},
      {name: "El Salvador", slug: "el_salvador"},
      {name: "Equatorial Guinea", slug: "equatorial_guinea"},
      {name: "Eritrea", slug: "eritrea"},
      {name: "Estonia", slug: "estonia"},
      {name: "Ethiopia", slug: "ethiopia"},
      {name: "Falkland Islands / Malvinas", slug: "falkland_islands_malvinas"},
      {name: "Fiji", slug: "fiji"},
      {name: "Finland", slug: "finland"},
      {name: "France", slug: "france"},
      {name: "French Southern and Antarctic Lands", slug: "french_southern_and_antarctic_lands"},
      {name: "Gabon", slug: "gabon"},
      {name: "Georgia", slug: "georgia"},
      {name: "Germany", slug: "germany"},
      {name: "Ghana", slug: "ghana"},
      {name: "Greece", slug: "greece"},
      {name: "Greenland", slug: "greenland"},
      {name: "Guatemala", slug: "guatemala"},
      {name: "Guinea", slug: "guinea"},
      {name: "Guinea-Bissau", slug: "guinea-bissau"},
      {name: "Guyana", slug: "guyana"},
      {name: "Haiti", slug: "haiti"},
      {name: "Honduras", slug: "honduras"},
      {name: "Hungary", slug: "hungary"},
      {name: "Iceland", slug: "iceland"},
      {name: "India", slug: "india"},
      {name: "Indonesia", slug: "indonesia"},
      {name: "Iran", slug: "iran"},
      {name: "Iraq", slug: "iraq"},
      {name: "Ireland", slug: "ireland"},
      {name: "Israel", slug: "israel"},
      {name: "Italy", slug: "italy"},
      {name: "Jamaica", slug: "jamaica"},
      {name: "Japan", slug: "japan"},
      {name: "Jordan", slug: "jordan"},
      {name: "Kazakhstan", slug: "kazakhstan"},
      {name: "Kenya", slug: "kenya"},
      {name: "Kingdom of eSwatini", slug: "kingdom_of_eswatini"},
      {name: "Kosovo", slug: "kosovo"},
      {name: "Kuwait", slug: "kuwait"},
      {name: "Kyrgyzstan", slug: "kyrgyzstan"},
      {name: "Lao PDR", slug: "lao_pdr"},
      {name: "Latvia", slug: "latvia"},
      {name: "Lebanon", slug: "lebanon"},
      {name: "Lesotho", slug: "lesotho"},
      {name: "Liberia", slug: "liberia"},
      {name: "Libya", slug: "libya"},
      {name: "Lithuania", slug: "lithuania"},
      {name: "Luxembourg", slug: "luxembourg"},
      {name: "Madagascar", slug: "madagascar"},
      {name: "Malawi", slug: "malawi"},
      {name: "Malaysia", slug: "malaysia"},
      {name: "Mali", slug: "mali"},
      {name: "Mauritania", slug: "mauritania"},
      {name: "Mexico", slug: "mexico"},
      {name: "Moldova", slug: "moldova"},
      {name: "Mongolia", slug: "mongolia"},
      {name: "Montenegro", slug: "montenegro"},
      {name: "Morocco", slug: "morocco"},
      {name: "Mozambique", slug: "mozambique"},
      {name: "Myanmar", slug: "myanmar"},
      {name: "Namibia", slug: "namibia"},
      {name: "Nepal", slug: "nepal"},
      {name: "Netherlands", slug: "netherlands"},
      {name: "New Caledonia", slug: "new_caledonia"},
      {name: "New Zealand", slug: "new_zealand"},
      {name: "Nicaragua", slug: "nicaragua"},
      {name: "Niger", slug: "niger"},
      {name: "Nigeria", slug: "nigeria"},
      {name: "North Macedonia", slug: "north_macedonia"},
      {name: "Northern Cyprus", slug: "northern_cyprus"},
      {name: "Norway", slug: "norway"},
      {name: "Oman", slug: "oman"},
      {name: "Pakistan", slug: "pakistan"},
      {name: "Palestine", slug: "palestine"},
      {name: "Panama", slug: "panama"},
      {name: "Papua New Guinea", slug: "papua_new_guinea"},
      {name: "Paraguay", slug: "paraguay"},
      {name: "Peru", slug: "peru"},
      {name: "Philippines", slug: "philippines"},
      {name: "Poland", slug: "poland"},
      {name: "Portugal", slug: "portugal"},
      {name: "Puerto Rico", slug: "puerto_rico"},
      {name: "Qatar", slug: "qatar"},
      {name: "Republic of Korea", slug: "republic_of_korea"},
      {name: "Republic of the Congo", slug: "republic_of_the_congo"},
      {name: "Romania", slug: "romania"},
      {name: "Russian Federation", slug: "russian_federation"},
      {name: "Rwanda", slug: "rwanda"},
      {name: "Saudi Arabia", slug: "saudi_arabia"},
      {name: "Senegal", slug: "senegal"},
      {name: "Serbia", slug: "serbia"},
      {name: "Sierra Leone", slug: "sierra_leone"},
      {name: "Slovakia", slug: "slovakia"},
      {name: "Slovenia", slug: "slovenia"},
      {name: "Solomon Islands", slug: "solomon_islands"},
      {name: "Somalia", slug: "somalia"},
      {name: "Somaliland", slug: "somaliland"},
      {name: "South Africa", slug: "south_africa"},
      {name: "South Sudan", slug: "south_sudan"},
      {name: "Spain", slug: "spain"},
      {name: "Sri Lanka", slug: "sri_lanka"},
      {name: "Sudan", slug: "sudan"},
      {name: "Suriname", slug: "suriname"},
      {name: "Sweden", slug: "sweden"},
      {name: "Switzerland", slug: "switzerland"},
      {name: "Syria", slug: "syria"},
      {name: "Taiwan", slug: "taiwan"},
      {name: "Tajikistan", slug: "tajikistan"},
      {name: "Tanzania", slug: "tanzania"},
      {name: "Thailand", slug: "thailand"},
      {name: "The Gambia", slug: "the_gambia"},
      {name: "Timor-Leste", slug: "timor-leste"},
      {name: "Togo", slug: "togo"},
      {name: "Trinidad and Tobago", slug: "trinidad_and_tobago"},
      {name: "Tunisia", slug: "tunisia"},
      {name: "Turkey", slug: "turkey"},
      {name: "Turkmenistan", slug: "turkmenistan"},
      {name: "Uganda", slug: "uganda"},
      {name: "Ukraine", slug: "ukraine"},
      {name: "United Arab Emirates", slug: "united_arab_emirates"},
      {name: "United Kingdom", slug: "united_kingdom"},
      {name: "United States", slug: "united_states"},
      {name: "Uruguay", slug: "uruguay"},
      {name: "Uzbekistan", slug: "uzbekistan"},
      {name: "Vanuatu", slug: "vanuatu"},
      {name: "Venezuela", slug: "venezuela"},
      {name: "Vietnam", slug: "vietnam"},
      {name: "Western Sahara", slug: "western_sahara"},
      {name: "Yemen", slug: "yemen"},
      {name: "Zambia", slug: "zambia"},
      {name: "Zimbabwe", slug: "zimbabwe"}
     ],
     regions: [
      {name: "Africa", slug: "africa"},
      {name: "Antarctic", slug: "antarctic"},
      {name: "Arctic", slug: "arctic"},
      {name: "Asia", slug: "asia"},
      {name: "Central Europe", slug: "central_europe"},
      {name: "Contiguous United States", slug: "contiguous_united_states"},
      {name: "Europe", slug: "europe"},
      {name: "Global", slug: "global"},
      {name: "Mediterranean", slug: "mediterranean"},
      {name: "North America", slug: "north_america"},
      {name: "North Atlantic", slug: "north_atlantic"},
      {name: "Northeast Europe", slug: "northeast_europe"},
      {name: "Northwest Europe", slug: "northwest_europe"},
      {name: "Oceania", slug: "oceania"},
      {name: "South America", slug: "south_america"},
      {name: "Southwest Europe", slug: "southwest_europe"},
      {name: "Svalbard", slug: "svalbard"},
      {name: "southeast Europe", slug: "southeast_europe"}
     ]
   };
   function ekPopulate(category) {
     var sel = document.getElementById('ek-domain-select');
     sel.innerHTML = '';
     EK_LISTS[category].forEach(function(item) {
       var opt = document.createElement('option');
       opt.value = item.name;
       opt.dataset.slug = item.slug;
       opt.textContent = item.name;
       sel.appendChild(opt);
     });
   }
   function ekDomainSwap(sel) {
     if (!sel || !sel.options.length) return;
     var slug = sel.options[sel.selectedIndex].dataset.slug;
     var name = sel.value;
     var img = document.getElementById('ek-domain-img');
     var err = document.getElementById('ek-domain-error');
     var code = document.getElementById('ek-domain-code');
     img.src = EK_DOMAIN_BASE + slug + '.png';
     img.alt = name;
     err.style.display = 'none';
     img.onerror = function() {
       err.textContent = 'Map preview unavailable for: ' + name;
       err.style.display = '';
     };
     var s = '<span class="ek-str">';
     var e = '</span>';
     var q = '<span class="ek-eq">=</span>';
     var esc = name.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
     code.innerHTML = 'import earthkit.plots as ekp\n\nchart ' + q + ' ekp.Map(domain' + q + s + '"' + esc + '"' + e + ')\nchart.standard_layers()\nchart.title(' + s + '"{domain} | {crs}"' + e + ')\nchart.show()';
   }
   function ekCopyCode() {
     var text = document.getElementById('ek-domain-code').textContent;
     navigator.clipboard.writeText(text).then(function() {
       var btn = document.getElementById('ek-domain-copy');
       btn.src = '_static/check.svg';
       btn.alt = 'Copied';
       setTimeout(function() { btn.src = '_static/copy.svg'; btn.alt = 'Copy'; }, 1500);
     });
   }
   function ekCatSwap(catSel) {
     ekPopulate(catSel.value);
     ekDomainSwap(document.getElementById('ek-domain-select'));
   }
   // Initialise on page load.
   (function() {
     ekPopulate('countries');
     ekDomainSwap(document.getElementById('ek-domain-select'));
   })();
   </script>


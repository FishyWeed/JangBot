// Danbi · JangBot art: rainy-night scenes and Danbi poses as SVG strings. Same source as components/bundle.js.
// Styling and animation come from jangbot.css (a-*, dn-*, pz-* classes).

  var J = {};

  // deterministic random so every render is identical
  function rng(seed) { var s = seed >>> 0; return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  function n(v) { return Math.round(v * 10) / 10; }

  /** rain(w, h, count, seed, opts): falling streaks; each streak loops on its own delay. */
  function rain(w, h, count, seed, opts) {
    opts = opts || {}; var r = rng(seed || 7), out = '<g class="a-rain" aria-hidden="true">';
    var len = opts.len || 18, slant = opts.slant == null ? -3 : opts.slant;
    for (var i = 0; i < count; i++) {
      var x = n(r() * w), y = n(r() * h - 40), l = n(len * (0.6 + r() * 0.8)), d = n(-r() * 1.4);
      out += '<line class="a-drop" x1="' + x + '" y1="' + y + '" x2="' + n(x + slant) + '" y2="' + n(y + l) + '" style="animation-delay:' + d + 's"/>';
    }
    return out + "</g>";
  }
  /** drips(points): golden drops falling from tile ends [[x,y],...] */
  function drips(points, fall, seed) {
    var r = rng(seed || 3), out = '<g class="a-drips" aria-hidden="true">';
    points.forEach(function (p) {
      var d = n(-r() * 2.6);
      out += '<path class="a-drip-trail" d="M' + p[0] + ' ' + p[1] + ' v' + n(4 + r() * 10) + '"/>' +
        '<circle class="a-drip" cx="' + p[0] + '" cy="' + (p[1] + 3) + '" r="1.8" style="--fall:' + (fall || 70) + 'px;animation-delay:' + d + 's"/>';
    });
    return out + "</g>";
  }
  function ripples(cx, cy, count, spread, seed) {
    var r = rng(seed || 11), out = '<g class="a-ripples" aria-hidden="true">';
    for (var i = 0; i < count; i++) {
      out += '<ellipse class="a-ripple" cx="' + n(cx + (r() - 0.5) * spread) + '" cy="' + n(cy + (r() - 0.5) * 8) + '" rx="10" ry="2.6" style="animation-delay:' + n(-r() * 2.6) + 's"/>';
    }
    return out + "</g>";
  }
  function svg(vb, cls, label, body) {
    return '<svg class="jb-art ' + cls + '" viewBox="' + vb + '" role="img" aria-label="' + label + '" preserveAspectRatio="xMidYMid slice">' + body + "</svg>";
  }

  // ---------- reusable pieces ----------
  /** curved hanok roof between x0..x1, eave line at y, ridge at ry; returns roof + tiles + tile ends */
  function roof(x0, x1, y, ry, lift, id) {
    var w = x1 - x0, inset = w * 0.2, out = "";
    var path = "M" + x0 + " " + (y - lift) + " Q" + (x0 + w * 0.06) + " " + (y + 4) + " " + (x0 + w * 0.16) + " " + y +
      " L" + (x1 - w * 0.16) + " " + y + " Q" + (x1 - w * 0.06) + " " + (y + 4) + " " + x1 + " " + (y - lift) +
      " Q" + (x1 - w * 0.08) + " " + (y - lift * 0.55) + " " + (x1 - w * 0.14) + " " + (y - lift * 0.7) +
      " Q" + (x1 - w * 0.25) + " " + (y - lift * 0.55 - (y - ry) * 0.12) + " " + (x1 - inset) + " " + ry + " L" + (x0 + inset) + " " + ry + " Q" + (x0 + w * 0.25) + " " + (y - lift * 0.55 - (y - ry) * 0.12) + " " + (x0 + w * 0.14) + " " + (y - lift * 0.7) +
      " Q" + (x0 + w * 0.08) + " " + (y - lift * 0.55) + " " + x0 + " " + (y - lift) + " Z";
    out += '<path class="a-roof a-ln" d="' + path + '"/>';
    // tile rows (giwa lines)
    var rows = Math.round(w / 22);
    for (var i = 1; i < rows; i++) {
      var t = i / rows, bx = x0 + w * 0.12 + (w * 0.76) * t, tx = x0 + inset + (w - 2 * inset) * t;
      out += '<path class="a-tile" d="M' + n(tx) + " " + (ry + 3) + " L" + n(bx) + " " + (y - 3) + '"/>';
    }
    // ridge
    out += '<path class="a-roof a-ln" d="M' + (x0 + inset - 14) + " " + (ry - 2) + " Q" + (x0 + inset - 20) + " " + (ry - 16) + " " + (x0 + inset - 6) + " " + (ry - 14) +
      " L" + (x1 - inset + 6) + " " + (ry - 14) + " Q" + (x1 - inset + 20) + " " + (ry - 16) + " " + (x1 - inset + 14) + " " + (ry - 2) + ' Z"/>';
    out += '<path class="a-roofhi-line" d="M' + (x0 + inset - 4) + " " + (ry - 11) + " L" + (x1 - inset + 4) + " " + (ry - 11) + '"/>';
    // round tile ends along the eave
    var ends = [], cnt = Math.round((w * 0.68) / 16);
    for (var k = 0; k <= cnt; k++) {
      var ex = n(x0 + w * 0.16 + (w * 0.68) * (k / cnt));
      out += '<circle class="a-roof a-tileend" cx="' + ex + '" cy="' + (y + 1) + '" r="5.2"/>';
      ends.push([ex, y + 6]);
    }
    return { svg: out, ends: ends };
  }
  function lanternHang(x, y, s, cls) { // hanging paper lantern (like a 등) with glow; pivot at top
    s = s || 1;
    return '<g transform="translate(' + x + " " + y + ") scale(" + s + ')"><g class="a-sway ' + (cls || "") + '">' +
      '<circle class="a-glowdisc" cx="0" cy="44" r="46"/>' +
      '<path class="a-cord" d="M0 0 V18"/>' +
      '<rect class="a-wood a-ln" x="-9" y="16" width="18" height="6" rx="2"/>' +
      '<rect class="a-paper a-ln a-flicker" x="-17" y="21" width="34" height="46" rx="15"/>' +
      '<path class="a-rib" d="M-16 31 H16 M-17 40 H17 M-17 49 H17 M-16 58 H16 M-6 22 V66 M6 22 V66"/>' +
      '<rect class="a-wood a-ln" x="-9" y="66" width="18" height="6" rx="2"/>' +
      '<path class="a-cord" d="M0 72 V80"/><circle class="a-glow" cx="0" cy="82" r="2.4"/>' +
      "</g></g>";
  }
  function windBell(x, y, s) { // 풍경: bell + fish plate; pivot top
    s = s || 1;
    return '<g transform="translate(' + x + " " + y + ") scale(" + s + ')"><g class="a-sway a-sway--slow">' +
      '<path class="a-cord" d="M0 0 V14"/>' +
      '<path class="a-stone a-ln" d="M-8 30 Q-8 14 0 14 Q8 14 8 30 L10 33 H-10 Z"/>' +
      '<path class="a-roofhi-line" d="M-5 22 H5 M-6 26 H6"/>' +
      '<path class="a-cord" d="M0 33 V42"/>' +
      '<path class="a-stone a-ln" d="M-10 48 Q0 40 10 48 Q0 56 -10 48 Z M10 48 L15 44 V52 Z"/>' +
      "</g></g>";
  }
  function pine(x, y, s) {
    s = s || 1;
    return '<g transform="translate(' + x + " " + y + ") scale(" + s + ')">' +
      '<path class="a-wood a-ln" d="M-4 0 Q-10 -40 4 -80 Q14 -110 6 -140 L12 -140 Q22 -108 10 -78 Q0 -40 6 0 Z"/>' +
      '<path class="a-pine a-ln" d="M-60 -92 Q-40 -116 -6 -108 Q20 -124 52 -108 Q74 -104 70 -92 Q40 -84 10 -90 Q-20 -82 -60 -92 Z"/>' +
      '<path class="a-pine a-ln" d="M-30 -132 Q-10 -150 16 -142 Q40 -152 58 -136 Q36 -126 14 -130 Q-6 -124 -30 -132 Z"/>' +
      '<path class="a-pine a-ln" d="M-44 -58 Q-24 -74 0 -66 Q24 -76 44 -62 Q22 -52 0 -56 Q-24 -50 -44 -58 Z"/>' +
      "</g>";
  }
  function stoneWall(x0, x1, y, h) {
    var out = '<rect class="a-stone a-ln" x="' + x0 + '" y="' + y + '" width="' + (x1 - x0) + '" height="' + h + '"/>';
    var r = rng(x0 + y), row = 0;
    for (var yy = y + 10; yy < y + h - 4; yy += 14, row++) {
      for (var xx = x0 + (row % 2 ? 6 : 16); xx < x1 - 14; xx += 26 + r() * 10) {
        out += '<rect class="a-stone-joint" x="' + n(xx) + '" y="' + (yy - 5) + '" width="' + n(18 + r() * 8) + '" height="9" rx="4"/>';
      }
    }
    // tiled cap
    out += '<path class="a-roof a-ln" d="M' + (x0 - 8) + " " + (y + 2) + " L" + (x0 + 4) + " " + (y - 12) + " L" + (x1 - 4) + " " + (y - 12) + " L" + (x1 + 8) + " " + (y + 2) + ' Z"/>';
    for (var t = x0 + 10; t < x1 - 4; t += 14) out += '<circle class="a-roof a-tileend" cx="' + t + '" cy="' + (y + 2) + '" r="4"/>';
    return out;
  }
  function bokeh(list) {
    return '<g class="a-bokehs" aria-hidden="true">' + list.map(function (b) { return '<circle class="a-bokeh" cx="' + b[0] + '" cy="' + b[1] + '" r="' + b[2] + '"/>'; }).join("") + "</g>";
  }
  function skyDefs(id) {
    return '<defs><linearGradient id="' + id + '-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--art-sky)"/><stop offset="1" style="stop-color:var(--art-sky-low)"/></linearGradient>' +
      '<radialGradient id="' + id + '-glow"><stop offset="0" style="stop-color:var(--art-glow);stop-opacity:.55"/><stop offset="1" style="stop-color:var(--art-glow);stop-opacity:0"/></radialGradient></defs>';
  }

  // ---------- scenes ----------
  var scenes = {};

  scenes.hanokNight = function () {
    var R = roof(560, 1130, 300, 200, 46);
    var body = skyDefs("hn") +
      '<rect width="1200" height="520" fill="url(#hn-sky)"/>' +
      '<circle class="a-moon" cx="930" cy="104" r="44"/>' +
      '<g class="a-drift"><rect class="a-mist" x="760" y="92" width="360" height="16" rx="8"/><rect class="a-mist" x="820" y="118" width="260" height="10" rx="5"/></g>' +
      '<path class="a-mtn-far" d="M0 318 C120 252 220 246 320 292 S520 226 640 274 S860 214 980 262 S1140 244 1200 270 V520 H0Z"/>' +
      '<path class="a-mtn-near" d="M0 372 C150 326 260 336 360 362 S560 318 700 352 S900 326 1040 352 S1160 344 1200 352 V520 H0Z"/>' +
      '<g class="a-drift a-drift--rev"><rect class="a-mist" x="-40" y="338" width="620" height="30" rx="15"/><rect class="a-mist" x="420" y="360" width="520" height="22" rx="11"/></g>' +
      bokeh([[120, 300, 9], [180, 312, 5], [470, 330, 7], [520, 318, 4], [1160, 330, 8]]) +
      pine(140, 412, 1.05) +
      stoneWall(0, 560, 410, 66) +
      // building
      '<rect class="a-stone a-ln" x="596" y="440" width="500" height="34"/><rect class="a-stone a-ln" x="780" y="474" width="140" height="10"/>' +
      '<rect class="a-wall a-ln" x="626" y="330" width="440" height="110"/>' +
      [654, 760, 864, 968].map(function (x) {
        return '<g class="a-flicker"><rect class="a-paper a-ln" x="' + (x + 8) + '" y="346" width="76" height="80"/>' +
          '<path class="a-lattice" d="M' + (x + 27) + ' 346 V426 M' + (x + 46) + ' 346 V426 M' + (x + 65) + ' 346 V426 M' + (x + 8) + ' 366 H' + (x + 84) + ' M' + (x + 8) + ' 386 H' + (x + 84) + ' M' + (x + 8) + ' 406 H' + (x + 84) + '"/></g>';
      }).join("") +
      [626, 742, 846, 950, 1052].map(function (x) { return '<rect class="a-pillar a-ln" x="' + x + '" y="318" width="14" height="122"/>'; }).join("") +
      '<rect class="a-wood a-ln" x="612" y="306" width="468" height="16"/>' +
      [640, 690, 740, 790, 840, 890, 940, 990, 1040].map(function (x) { return '<rect class="a-wood a-ln" x="' + (x - 7) + '" y="298" width="14" height="10"/>'; }).join("") +
      R.svg + drips(R.ends.filter(function (_, i) { return i % 2 === 0; }), 120, 5) +
      lanternHang(700, 306, 0.9) + lanternHang(1004, 306, 0.9, "a-sway--alt") + windBell(1124, 256, 0.9) +
      // ground + puddles
      '<rect class="a-ground" x="0" y="474" width="1200" height="46"/>' +
      '<ellipse class="a-water" cx="820" cy="498" rx="210" ry="12"/><rect class="a-reflect" x="672" y="488" width="296" height="6" rx="3"/>' +
      '<ellipse class="a-water" cx="250" cy="502" rx="140" ry="8"/>' +
      ripples(820, 498, 6, 360, 21) + ripples(250, 502, 3, 220, 4) +
      rain(1200, 520, 120, 42);
    return svg("0 0 1200 520", "art-scene art-hanok", "A hanok house on a rainy night, lanterns glowing under the eaves", body);
  };

  scenes.eavesRain = function () {
    // eave line: from lower-left rising to the right, then curling up at the corner (추녀)
    function eave(t) { var x = -10 + t * 560, y = 236 - t * 130 - (t > 0.78 ? Math.pow((t - 0.78) / 0.22, 2) * 70 : 0); return [n(x), n(y)]; }
    var pts = [], line = "", ends = "", drp = [];
    for (var i = 0; i <= 40; i++) { var p = eave(i / 40); pts.push(p); }
    line = pts.map(function (p, i) { return (i ? "L" : "M") + p[0] + " " + p[1]; }).join(" ");
    var mass = line + " L600 " + (pts[40][1] - 20) + " L600 0 L-10 0 Z";
    for (var k = 0; k <= 14; k++) {
      var e = eave(k / 14.6);
      ends += '<circle class="a-roof a-tileend" cx="' + e[0] + '" cy="' + e[1] + '" r="14"/><circle class="a-roofhi" cx="' + n(e[0] - 4) + '" cy="' + n(e[1] - 5) + '" r="3.4"/>';
      if (k % 2 === 1 && k < 13) drp.push([e[0], e[1] + 14]);
    }
    var rafters = "";
    for (var m = 0; m < 11; m++) {
      var a = eave(m / 12 + 0.02);
      rafters += '<path class="a-wood a-ln" d="M' + n(a[0] - 26) + " " + n(a[1] + 10) + " L" + n(a[0] + 8) + " " + n(a[1] + 18) + " L" + n(a[0] + 6) + " " + n(a[1] + 30) + " L" + n(a[0] - 28) + " " + n(a[1] + 22) + ' Z"/>' +
        '<rect class="a-glow" x="' + n(a[0] - 24) + '" y="' + n(a[1] + 22) + '" width="30" height="2.4" opacity=".55" transform="rotate(14 ' + a[0] + " " + a[1] + ')"/>';
    }
    var body = skyDefs("er") + '<rect width="600" height="420" fill="url(#er-sky)"/>' +
      bokeh([[420, 330, 26], [500, 370, 14], [560, 300, 18], [330, 390, 10]]) +
      '<path class="a-mtn-near" d="M0 372 C120 350 220 356 300 364 S480 344 600 356 V420 H0Z"/>' +
      '<path class="a-roof" d="' + mass + '"/>' +
      '<path class="a-roofhi-line" d="' + line + '" transform="translate(0 -16)" opacity=".5"/>' +
      '<path class="a-wood a-ln" d="M-10 262 L520 150 L522 166 L-10 280 Z"/><path class="a-wood a-ln" d="M-10 292 L360 214 L362 228 L-10 308 Z"/>' +
      rafters + ends + drips(drp, 220, 9) +
      '<rect class="a-pillar a-ln" x="24" y="290" width="34" height="140"/>' +
      '<g transform="translate(176 270)">' + lanternHang(0, 0, 1.45).replace(/^<g transform="translate\(0 0\) scale\(1.45\)">/, '<g transform="scale(1.45)">') + "</g>" +
      windBell(500, 160, 1.3) +
      rain(600, 420, 70, 8, { len: 22 });
    return svg("0 0 600 420", "art-scene art-eaves", "Rain dripping from hanok roof tiles beside a glowing lantern and a wind bell", body);
  };

  scenes.palaceGate = function () {
    var top = roof(250, 550, 158, 82, 30), low = roof(200, 600, 236, 186, 26);
    var body = skyDefs("pg") + '<rect width="800" height="500" fill="url(#pg-sky)"/>' +
      '<path class="a-mtn-far" d="M0 300 C140 250 260 262 380 286 S600 240 800 276 V500 H0Z"/>' +
      bokeh([[90, 340, 8], [710, 330, 10], [660, 352, 5]]) +
      stoneWall(0, 236, 330, 120) + stoneWall(564, 800, 330, 120) +
      // stone base with arch (홍예문)
      '<path class="a-stone a-ln" d="M220 300 H580 V450 H440 V392 Q400 340 360 392 V450 H220 Z"/>' +
      '<path class="a-arch-dark" d="M364 450 V394 Q400 348 436 394 V450 Z"/>' +
      '<rect class="a-wall a-ln" x="250" y="248" width="300" height="52"/>' +
      [262, 330, 400, 470, 532].map(function (x) { return '<rect class="a-pillar a-ln" x="' + (x - 6) + '" y="246" width="12" height="56"/>'; }).join("") +
      [296, 366, 436, 504].map(function (x) { return '<rect class="a-paper a-ln a-flicker" x="' + (x - 18) + '" y="258" width="36" height="30"/>'; }).join("") +
      low.svg + '<rect class="a-wall a-ln" x="300" y="174" width="200" height="30"/>' + top.svg +
      drips(low.ends.filter(function (_, i) { return i % 3 === 0; }), 70, 13) +
      lanternHang(330, 300, 0.8) + lanternHang(470, 300, 0.8, "a-sway--alt") +
      '<rect class="a-ground" x="0" y="450" width="800" height="50"/>' +
      '<ellipse class="a-water" cx="400" cy="474" rx="150" ry="10"/><rect class="a-reflect" x="330" y="468" width="140" height="5" rx="2.5"/>' +
      ripples(400, 474, 5, 260, 31) + rain(800, 500, 90, 77);
    return svg("0 0 800 500", "art-scene art-gate", "A palace gate with a stone arch in the rain", body);
  };

  scenes.pagodaCourtyard = function () {
    var tiers = "", y = 400;
    [[150, 26], [126, 22], [104, 20]].forEach(function (t, i) {
      var w = t[0], h = t[1], x = 400 - w / 2;
      tiers += '<rect class="a-stone a-ln" x="' + (x + 14) + '" y="' + (y - h - 18) + '" width="' + (w - 28) + '" height="' + (h + 4) + '"/>' +
        '<path class="a-stone a-ln" d="M' + (x - 6) + " " + (y - 18) + " Q400 " + (y - 30) + " " + (x + w + 6) + " " + (y - 18) + " L" + (x + w - 4) + " " + (y - 10) + " H" + (x + 4) + ' Z"/>';
      y -= h + 26;
    });
    var body = skyDefs("pc") + '<rect width="800" height="500" fill="url(#pc-sky)"/>' +
      '<circle class="a-moon" cx="610" cy="96" r="34"/>' +
      '<path class="a-mtn-far" d="M0 290 C160 236 300 250 420 276 S640 228 800 262 V500 H0Z"/>' +
      '<g class="a-drift"><rect class="a-mist" x="40" y="270" width="500" height="26" rx="13"/></g>' +
      stoneWall(0, 800, 372, 70) +
      pine(150, 440, 1.1) + pine(680, 446, 0.8) +
      '<rect class="a-stone a-ln" x="320" y="400" width="160" height="40"/><rect class="a-stone a-ln" x="300" y="436" width="200" height="14"/>' +
      tiers + '<path class="a-stone a-ln" d="M396 ' + (y + 6) + ' V' + (y - 30) + ' M388 ' + (y - 8) + ' H404 M390 ' + (y - 18) + ' H402"/>' +
      '<g class="a-flicker"><rect class="a-stone a-ln" x="560" y="404" width="30" height="40"/><rect class="a-paper a-ln" x="566" y="410" width="18" height="16"/><path class="a-stone a-ln" d="M552 404 L575 390 L598 404 Z"/></g>' +
      '<rect class="a-ground" x="0" y="450" width="800" height="50"/>' +
      '<ellipse class="a-water" cx="420" cy="476" rx="180" ry="10"/>' + ripples(420, 476, 6, 300, 61) +
      rain(800, 500, 90, 19);
    return svg("0 0 800 500", "art-scene art-pagoda", "A stone pagoda and pine trees in a rainy temple courtyard", body);
  };

  scenes.mountainMist = function () {
    var body = skyDefs("mm") + '<rect width="1200" height="240" fill="url(#mm-sky)"/>' +
      '<path class="a-mtn-far" d="M0 140 C140 70 260 80 360 120 S560 50 700 100 S920 40 1060 96 S1160 90 1200 100 V240 H0Z"/>' +
      '<g class="a-drift"><rect class="a-mist" x="60" y="112" width="540" height="22" rx="11"/><rect class="a-mist" x="700" y="100" width="420" height="18" rx="9"/></g>' +
      '<path class="a-mtn-near" d="M0 186 C160 140 300 150 420 172 S640 128 800 160 S1020 136 1200 158 V240 H0Z"/>' +
      pine(220, 236, 0.55) + pine(260, 240, 0.4) + pine(940, 236, 0.5) +
      '<g class="a-drift a-drift--rev"><rect class="a-mist" x="-20" y="176" width="700" height="26" rx="13"/><rect class="a-mist" x="640" y="190" width="600" height="20" rx="10"/></g>' +
      rain(1200, 240, 60, 90, { len: 14 });
    return svg("0 0 1200 240", "art-scene art-band", "Layered mountains and pines in drifting mist", body);
  };

  scenes.signboard = function () { // hanging lit signboard, like a teahouse sign in the rain
    var body = '<rect class="a-cord-bar" x="10" y="6" width="140" height="8" rx="4"/>' +
      '<path class="a-cord" d="M40 14 V36 M120 14 V36"/>' +
      '<g class="a-sway a-sway--slow" style="transform-origin:80px 14px"><circle class="a-glowdisc" cx="80" cy="200" r="120"/>' +
      '<rect class="a-wood a-ln" x="22" y="34" width="116" height="340" rx="6"/>' +
      '<rect class="a-paper a-ln a-flicker" x="32" y="44" width="96" height="320" rx="3"/>' +
      '<text class="a-sign-text" x="80" y="120" text-anchor="middle">장</text><text class="a-sign-text" x="80" y="200" text-anchor="middle">봇</text>' +
      '<text class="a-sign-small" x="80" y="250" text-anchor="middle">단 비</text>' +
      '<rect class="a-seal" x="68" y="300" width="24" height="24" rx="3"/><text class="a-seal-text" x="80" y="317" text-anchor="middle">雨</text>' +
      "</g>" + drips([[30, 374], [130, 374]], 40, 2);
    return '<svg class="jb-art art-sign" viewBox="0 0 160 430" role="img" aria-label="A glowing hanging signboard reading 장봇">' + body + "</svg>";
  };

  scenes.lantern = function () { // 청사초롱: blue top, red skirt
    var body = '<defs><radialGradient id="lt-glow"><stop offset="0" style="stop-color:var(--art-glow);stop-opacity:.6"/><stop offset="1" style="stop-color:var(--art-glow);stop-opacity:0"/></radialGradient></defs>' +
      '<g class="a-sway" style="transform-origin:60px 0px"><circle cx="60" cy="96" r="60" fill="url(#lt-glow)"/>' +
      '<path class="a-cord" d="M60 0 V30"/><rect class="a-wood a-ln" x="44" y="28" width="32" height="8" rx="2"/>' +
      '<path class="lt-blue a-ln" d="M30 40 Q60 30 90 40 L92 70 H28 Z"/>' +
      '<rect class="a-paper a-ln a-flicker" x="34" y="66" width="52" height="56" rx="10"/>' +
      '<path class="lt-red a-ln" d="M28 118 H92 L88 146 Q60 156 32 146 Z"/>' +
      '<path class="a-rib" d="M48 68 V120 M60 66 V122 M72 68 V120"/>' +
      '<rect class="a-wood a-ln" x="46" y="146" width="28" height="8" rx="2"/><path class="lt-red-line" d="M52 154 V172 M60 154 V176 M68 154 V172"/></g>';
    return '<svg class="jb-art art-lantern" viewBox="0 0 120 180" role="img" aria-label="A cheongsachorong lantern">' + body + "</svg>";
  };

  scenes.windBell = function () {
    return '<svg class="jb-art art-bell" viewBox="0 0 80 140" role="img" aria-label="A wind bell swaying in the rain">' + windBell(40, 0, 2.2) + rain(80, 140, 10, 5, { len: 10 }) + "</svg>";
  };

  scenes.giwaBand = function () { // row of roof-tile ends: a divider
    var out = '<rect class="a-roof" x="0" y="0" width="1200" height="14"/>';
    for (var x = 12; x < 1200; x += 24) out += '<circle class="a-roof a-tileend" cx="' + x + '" cy="16" r="10"/><circle class="a-roofhi" cx="' + (x - 2.5) + '" cy="13.5" r="2.6"/>';
    return '<svg class="jb-art art-giwa" viewBox="0 0 1200 30" preserveAspectRatio="xMidYMin slice" aria-hidden="true">' + out + "</svg>";
  };

  // ---------- Danbi poses ----------
  var FACES = {
    smile: '<g class="dn-eyes"><ellipse class="dn-eye" cx="24.6" cy="21.2" rx="2.7" ry="3.3"/><ellipse class="dn-eye" cx="39.4" cy="21.2" rx="2.7" ry="3.3"/><circle class="dn-glint" cx="25.6" cy="19.9" r="1"/><circle class="dn-glint" cx="40.4" cy="19.9" r="1"/></g><path class="dn-mouth" d="M28.6 25 Q32 28.8 35.4 25"/>',
    joy: '<path class="dn-mouth" d="M21.8 22.4 Q24.6 18.6 27.4 22.4 M36.6 22.4 Q39.4 18.6 42.2 22.4"/><path class="dn-mouth dn-mouth-fill" d="M28.4 24.6 Q32 31.4 35.6 24.6 Z"/>',
    calm: '<path class="dn-mouth" d="M21.8 21 Q24.6 23.6 27.4 21 M36.6 21 Q39.4 23.6 42.2 21"/><path class="dn-mouth" d="M29.6 25.6 Q32 27.6 34.4 25.6"/>',
    sleep: '<path class="dn-mouth" d="M21.8 21.6 Q24.6 23.4 27.4 21.6 M36.6 21.6 Q39.4 23.4 42.2 21.6"/><ellipse class="dn-mouth dn-mouth-fill" cx="32" cy="26.4" rx="1.4" ry="1.2"/>',
    focus: '<g class="dn-eyes"><ellipse class="dn-eye" cx="24.6" cy="21.6" rx="2.6" ry="3"/><ellipse class="dn-eye" cx="39.4" cy="21.6" rx="2.6" ry="3"/><circle class="dn-glint" cx="25.4" cy="20.4" r=".9"/><circle class="dn-glint" cx="40.2" cy="20.4" r=".9"/></g><path class="dn-mouth" d="M21.4 16.6 L27.2 17.8 M42.6 16.6 L36.8 17.8"/><path class="dn-mouth dn-mouth-fill" d="M29 24.8 Q32 30 35 24.8 Z"/>',
    down: '<g class="dn-eyes"><ellipse class="dn-eye" cx="24.6" cy="23" rx="2.6" ry="2.4"/><ellipse class="dn-eye" cx="39.4" cy="23" rx="2.6" ry="2.4"/></g><path class="dn-mouth" d="M30 27 Q32 28.4 34 27"/>',
    sad: '<g class="dn-eyes"><ellipse class="dn-eye" cx="24.6" cy="22" rx="2.4" ry="2.9"/><ellipse class="dn-eye" cx="39.4" cy="22" rx="2.4" ry="2.9"/><circle class="dn-glint" cx="25.4" cy="20.8" r=".9"/><circle class="dn-glint" cx="40.2" cy="20.8" r=".9"/></g><path class="dn-mouth" d="M21.2 17.6 L27 16.4 M42.8 17.6 L37 16.4 M29 27.6 Q32 24.8 35 27.6"/><path class="dn-tear" d="M43.6 24.4 Q45.2 27.4 43.6 28.6 Q42 27.4 43.6 24.4 Z"/>'
  };
  function body(face, feet) {
    return (feet ? '<ellipse class="dn-foot" cx="24" cy="59.6" rx="5.4" ry="2.8"/><ellipse class="dn-foot" cx="40" cy="59.6" rx="5.4" ry="2.8"/>' : "") +
      '<ellipse class="dn-hoop" cx="32" cy="52.5" rx="21.5" ry="6.5"/>' +
      '<path class="dn-body" d="M11.5 14.5 C13 25.5 23.5 28.5 26.5 33.5 C23.5 38.5 14 41.5 12.5 51.5 L51.5 51.5 C50 41.5 40.5 38.5 37.5 33.5 C40.5 28.5 51 25.5 52.5 14.5 Z"/>' +
      '<path class="dn-shade" d="M44.5 23.5 C47.5 21.5 50 18.5 51 15.5 L52.5 15 C51.5 22 47 25.5 41.5 28.5 Z"/><path class="dn-shade" d="M42 41.5 C46 43.5 49.5 46.5 50.5 50.5 L46.5 50.5 C45.5 47 43.5 44 40 42 Z"/>' +
      '<path class="dn-cord" d="M17.5 49 L29 37.5 M25 50.5 L30.5 37.5 M39 50.5 L33.5 37.5 M46.5 49 L35 37.5"/>' +
      '<rect class="dn-waist" x="25" y="31" width="14" height="5.5" rx="2.2"/>' +
      '<ellipse class="dn-hoop" cx="32" cy="13.5" rx="22" ry="7"/><ellipse class="dn-head" cx="32" cy="12.6" rx="16.5" ry="4.2"/>' +
      '<g transform="translate(0 1.9)"><ellipse class="dn-blush" cx="19" cy="24.6" rx="3.4" ry="2"/><ellipse class="dn-blush" cx="45" cy="24.6" rx="3.4" ry="2"/>' + FACES[face] + "</g>";
  }
  function arm(d) { return '<path class="dn-arm-o" d="' + d + '"/><path class="dn-arm" d="' + d + '"/>'; }
  function hand(x, y) { return '<circle class="dn-hand" cx="' + x + '" cy="' + y + '" r="3.2"/>'; }
  // sticks drawn from the grip at 0,0 toward a direction; gungchae = mallet with round head, yeolchae = thin bamboo
  function gungchae(dx, dy) { return '<path class="dn-stick-o" d="M' + (-dx * 0.18) + " " + (-dy * 0.18) + " L" + dx + " " + dy + '"/><path class="dn-stick" d="M' + (-dx * 0.18) + " " + (-dy * 0.18) + " L" + dx + " " + dy + '"/><circle class="dn-mallet" cx="' + n(dx * 1.12) + '" cy="' + n(dy * 1.12) + '" r="3.8"/>'; }
  function yeolchae(dx, dy) { return '<path class="dn-stick-o dn-stick-o--thin" d="M' + (-dx * 0.12) + " " + (-dy * 0.12) + " L" + dx + " " + dy + '"/><path class="dn-stick dn-stick--thin" d="M' + (-dx * 0.12) + " " + (-dy * 0.12) + " L" + dx + " " + dy + '"/>'; }
  function wrap(vb, cls, label, inner) {
    return '<svg class="jb-danbi-pose ' + cls + '" viewBox="' + vb + '" role="img" aria-label="' + label + '">' + inner + "</svg>";
  }
  var poses = {};
  var B = 'transform="translate(28 40)"';

  poses.drumming = function () {
    return wrap("4 2 112 108", "pz-drumming", "Danbi playing himself with a gungchae and a yeolchae",
      '<g class="pz-hit" transform="translate(60 52.6)"><ellipse class="pz-ring" rx="18" ry="5"/><ellipse class="pz-ring pz-ring--2" rx="18" ry="5"/></g>' +
      '<g class="pz-syl" aria-hidden="true"><text class="pz-syl-t pz-syl-1" x="14" y="24">덩</text><text class="pz-syl-t pz-syl-2" x="92" y="20">기덕</text><text class="pz-syl-t pz-syl-3" x="22" y="14">쿵</text></g>' +
      '<g ' + B + '><g class="pz-bob">' + arm("M15 23 Q4 22 2 11") + arm("M49 23 Q60 22 62 9") + body("focus", true) +
      '<g transform="translate(2 10)"><g class="pz-stick-l">' + gungchae(10, -16) + "</g></g>" + hand(2, 10) +
      '<g transform="translate(62 9)"><g class="pz-stick-r">' + yeolchae(-14, -19) + "</g></g>" + hand(62, 9) + "</g></g>");
  };
  poses.sticks = function () { // guide: both sticks presented
    return wrap("0 0 360 200", "pz-sticks", "Danbi holding the gungchae in his left hand and the yeolchae in his right",
      '<g transform="translate(124 46) scale(1.8)"><g class="pz-bob">' + arm("M15 23 Q2 26 -2 14") + arm("M49 23 Q62 26 66 14") + body("joy", true) +
      '<g transform="translate(-2 14)">' + gungchae(-2, -22) + "</g>" + hand(-2, 14) +
      '<g transform="translate(66 14)">' + yeolchae(4, -30) + "</g>" + hand(66, 14) + "</g></g>" +
      '<g class="pz-label"><path class="pz-leader" d="M114 30 L96 30"/><text class="pz-lt" x="92" y="36" text-anchor="end">궁채</text><text class="pz-ls" x="92" y="52" text-anchor="end">gungchae</text>' +
      '<text class="pz-lx" x="92" y="70" text-anchor="end">left hand</text><text class="pz-lx" x="92" y="84" text-anchor="end">round mallet</text><text class="pz-lx" x="92" y="98" text-anchor="end">deep 쿵</text></g>' +
      '<g class="pz-label"><path class="pz-leader" d="M252 16 L268 16"/><text class="pz-lt" x="272" y="22">열채</text><text class="pz-ls" x="272" y="38">yeolchae</text>' +
      '<text class="pz-lx" x="272" y="56">right hand</text><text class="pz-lx" x="272" y="70">thin bamboo</text><text class="pz-lx" x="272" y="84">sharp 덕 · 기덕</text></g>');
  };
  poses.umbrella = function () {
    return wrap("14 -2 132 142", "pz-umbrella", "Danbi walking under an oil-paper umbrella in the rain",
      rain(150, 140, 26, 14, { len: 10 }) +
      '<g transform="translate(28 66)"><g class="pz-bob">' + arm("M49 23 Q60 20 58 4") + arm("M15 23 Q8 30 10 38") + hand(10, 38) + body("calm", true) +
      '<g transform="translate(58 4)"><g class="pz-umb"><path class="dn-stick-o" d="M0 6 L0 -40"/><path class="dn-stick" d="M0 6 L0 -40"/>' +
      '<path class="pz-canopy a-ln" d="M-50 -30 Q-46 -62 0 -66 Q46 -62 50 -30 Q38 -36 25 -30 Q12 -36 0 -30 Q-12 -36 -25 -30 Q-38 -36 -50 -30 Z"/>' +
      '<path class="pz-rib" d="M0 -66 L-25 -30 M0 -66 L0 -30 M0 -66 L25 -30 M0 -66 L-44 -34 M0 -66 L44 -34"/><circle class="dn-mallet" cx="0" cy="-67" r="2.6"/>' +
      drips([[-50, -28], [-25, -28], [25, -28], [50, -28]], 50, 6) + "</g></g>" + hand(58, 4) + "</g></g>");
  };
  poses.wave = function () {
    return wrap("4 6 108 102", "pz-wave", "Danbi waving hello",
      '<g ' + B + '><g class="pz-bob">' + arm("M49 23 Q58 30 56 38") + hand(56, 38) + body("joy", true) +
      '<g transform="translate(15 23)"><g class="pz-wave-arm">' + arm("M0 0 Q-12 -4 -14 -18") + hand(-14, -18) + "</g></g></g></g>" +
      '<text class="pz-say" x="8" y="22">안녕!</text>');
  };
  poses.bow = function () {
    return wrap("6 22 108 92", "pz-bow", "Danbi bowing in greeting (insa)",
      '<g transform="translate(60 102)"><g class="pz-bowing"><g transform="translate(-32 -62)">' + arm("M15 23 Q16 34 24 40") + arm("M49 23 Q48 34 40 40") + body("calm", true) + hand(24, 40) + hand(40, 40) + "</g></g></g>");
  };
  poses.sleep = function () {
    return wrap("10 4 106 106", "pz-sleep", "Danbi napping while the rain falls",
      '<g transform="translate(26 44) rotate(-8 32 60)"><g class="pz-breathe">' + arm("M15 23 Q12 34 20 40") + arm("M49 23 Q52 34 44 40") + body("sleep", true) + hand(20, 40) + hand(44, 40) + "</g></g>" +
      '<g class="pz-z" aria-hidden="true"><text class="pz-z-t pz-z-1" x="84" y="40">z</text><text class="pz-z-t pz-z-2" x="92" y="28">z</text><text class="pz-z-t pz-z-3" x="100" y="16">Z</text></g>');
  };
  poses.read = function () {
    return wrap("14 28 92 80", "pz-read", "Danbi reading an old thread-bound book",
      '<g ' + B + ">" + arm("M15 23 Q8 36 18 44") + arm("M49 23 Q56 36 46 44") + body("down", true) +
      '<g class="pz-book"><path class="pz-cover a-ln" d="M8 40 L32 44 L56 40 L56 58 L32 62 L8 58 Z"/>' +
      '<path class="pz-page a-ln" d="M11 41 L31 44.6 L31 59 L11 56 Z"/><path class="pz-page a-ln" d="M53 41 L33 44.6 L33 59 L53 56 Z"/>' +
      '<path class="pz-text" d="M14 46 L28 48.4 M14 50 L28 52.4 M36 48.4 L50 46 M36 52.4 L50 50"/><path class="pz-flip a-ln" d="M33 44.6 Q42 40 52 41.6 L52 55 Q42 54 33 59 Z"/></g>' +
      hand(18, 44) + hand(46, 44) + "</g>");
  };
  poses.sad = function () {
    return wrap("12 0 96 108", "pz-sad", "Danbi under a little rain cloud: something went wrong",
      '<g class="pz-cloud"><path class="pz-cloud-b a-ln" d="M34 26 Q32 14 44 14 Q48 4 60 8 Q70 2 76 12 Q90 12 86 26 Z"/>' +
      drips([[44, 28], [56, 28], [68, 28], [78, 28]], 34, 31) + "</g>" +
      '<g ' + B + ">" + arm("M15 23 Q10 32 14 40") + arm("M49 23 Q54 32 50 40") + body("sad", true) + hand(14, 40) + hand(50, 40) + "</g>");
  };
  poses.lantern = function () {
    return wrap("8 18 118 104", "pz-lantern", "Danbi carrying a cheongsachorong lantern through the night",
      '<g transform="translate(18 48)"><g class="pz-bob">' + arm("M15 23 Q8 30 10 38") + hand(10, 38) + body("calm", true) + arm("M49 23 Q60 22 66 12") +
      '<g transform="translate(66 12)"><path class="dn-stick-o" d="M0 0 L22 -10"/><path class="dn-stick" d="M0 0 L22 -10"/>' +
      '<g transform="translate(22 -10)"><g class="a-sway"><circle class="a-glowdisc" cx="0" cy="22" r="26"/><path class="a-cord" d="M0 0 V6"/>' +
      '<path class="lt-blue a-ln" d="M-8 6 Q0 3 8 6 L9 13 H-9 Z"/><rect class="a-paper a-ln a-flicker" x="-7" y="12" width="14" height="14" rx="3"/><path class="lt-red a-ln" d="M-9 25 H9 L8 32 Q0 35 -8 32 Z"/></g></g></g>' +
      hand(66, 12) + "</g></g>");
  };

  function art(name) { return scenes[name] ? scenes[name]() : ""; }
  function danbi(pose) { return poses[pose] ? poses[pose]() : ""; }

  /** rainLayer(): a quiet full-bleed rain SVG for behind the chat feed. */
  function rainLayer() {
    return '<svg class="jb-rainfall" viewBox="0 0 1200 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">' + rain(1200, 900, 70, 99, { len: 26, slant: -2 }) + "</svg>";
  }
  J.rainLayer = rainLayer;
  J.art = art; J.danbi = danbi; J.sceneNames = Object.keys(scenes); J.poseNames = Object.keys(poses);

const SCENE_NAMES = J.sceneNames;
const POSE_NAMES = J.poseNames;
export { art, danbi, rainLayer, SCENE_NAMES, POSE_NAMES };

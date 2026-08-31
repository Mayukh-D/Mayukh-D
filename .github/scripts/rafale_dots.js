/* ---------- Rafale EH side profile, halftone render ----------
   The airframe is authored as shaded regions in metres (15.27 m long,
   5.34 m tall), then sampled on a grid: every sample that lands inside a
   region becomes a dot whose radius and colour follow that region's tone.
   No bitmap, no external asset; the shape is geometry, the dots are derived.
   x: +nose, y: +up, origin on the fuselage centreline. */
(function () {
  var canvas = document.getElementById('rafale');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var DPR = Math.min(window.devicePixelRatio || 1, 2);

  /* Regions are listed back to front: later entries win a sample.
     tone 0 = darkest, 1 = brightest. */
  var R = [];
  function reg(tone, pts) { R.push({ t: tone, p: pts }); }

  /* Stations derived from a side-elevation reference: canard at 42-53% of
     length, wing root LE at 49%, fin root LE at 72%, and the fin tip
     trailing edge overhanging the tail at 106%. Listed back to front. */

  // fin
  reg(0.72, [[-3.34, 0.58], [-6.45, 3.04], [-7.95, 2.98], [-8.20, 2.40],
             [-7.80, 0.40]]);
  reg(0.44, [[-6.60, 2.72], [-8.10, 2.66], [-7.80, 0.42], [-6.40, 0.52]]);
  // ECM fairing: a separate pod overhanging the fin tip, not part of the fin
  reg(0.95, [[-6.30, 3.20], [-8.58, 3.12], [-8.62, 2.90], [-6.34, 2.96]]);

  // fuselage
  reg(0.86, [
    [7.62, -0.02], [7.10, 0.20], [6.40, 0.40], [5.60, 0.58], [4.84, 0.73],
    [4.35, 1.05], [3.75, 1.27], [2.90, 1.22], [1.90, 1.02], [1.55, 0.88],
    [0.80, 0.80], [-0.60, 0.74], [-2.00, 0.66], [-3.34, 0.58], [-5.00, 0.48],
    [-6.40, 0.42], [-7.30, 0.38], [-7.66, 0.30],
    [-7.66, -0.29], [-7.20, -0.48], [-6.00, -0.58], [-4.50, -0.66],
    [-3.00, -0.72], [-1.50, -0.78], [0.00, -0.82], [1.26, -0.80],
    [2.50, -0.78], [3.20, -0.70], [4.20, -0.56], [5.20, -0.40], [6.30, -0.20]
  ]);
  // shaded underside
  reg(0.56, [[6.30, -0.20], [5.20, -0.40], [4.20, -0.56], [3.20, -0.70],
             [2.50, -0.78], [1.26, -0.80], [0.00, -0.82], [-1.50, -0.78],
             [-3.00, -0.72], [-4.50, -0.66], [-6.00, -0.58], [-7.20, -0.48],
             [-7.66, -0.29], [-7.40, -0.06], [-3.00, -0.30], [1.00, -0.42],
             [4.00, -0.26]]);

  // panel tones, breaking up the flank the way the real scheme does
  reg(0.70, [[4.20, 0.62], [1.60, 0.86], [-1.60, 0.70], [-3.20, 0.60],
             [-3.20, 0.30], [-1.60, 0.40], [1.60, 0.52], [4.10, 0.40]]);
  reg(0.62, [[-3.40, 0.58], [-5.80, 0.46], [-7.20, 0.38], [-7.20, 0.10],
             [-5.60, 0.18], [-3.40, 0.28]]);

  // conformal tank along the belly
  reg(0.66, [[1.90, -0.78], [1.00, -1.02], [-0.60, -1.22], [-2.60, -1.30],
             [-4.30, -1.24], [-5.50, -1.00], [-5.95, -0.76]]);

  // side intake, no splitter plate
  reg(0.42, [[2.55, -0.52], [2.50, -1.02], [1.90, -1.10], [1.20, -1.06],
             [0.92, -0.90], [0.95, -0.58]]);
  reg(0.95, [[2.55, -0.55], [2.50, -0.98], [2.30, -1.00], [2.35, -0.57]]);

  // delta wing, edge-on, running aft almost to the nozzles
  reg(0.32, [[0.30, -0.14], [-6.71, -0.28], [-6.71, -0.60], [-0.30, -0.50]]);
  // close-coupled canard
  reg(0.46, [[1.45, 0.62], [0.10, 0.50], [-0.62, 0.38], [-0.30, 0.18],
             [0.75, 0.26], [1.42, 0.40]]);

  // canopy glazing: the brightest mass on the airframe
  reg(1.00, [[4.84, 0.73], [4.35, 1.05], [3.75, 1.27], [2.90, 1.22],
             [1.90, 1.02], [1.58, 0.88]]);

  // nozzle
  reg(0.30, [[-7.00, 0.34], [-7.66, 0.28], [-7.66, -0.28], [-7.00, -0.40]]);

  // fixed refuelling probe and nose pitot
  reg(0.62, [[6.52, 0.56], [5.05, 0.82], [4.98, 0.62], [6.46, 0.36]]);
  reg(0.58, [[7.62, 0.04], [8.62, 0.09], [8.62, -0.05], [7.62, -0.12]]);

  var MINX = -9.0, MAXX = 8.8, MINY = -1.65, MAXY = 3.45;

  function inside(px, py, poly) {
    var c = false;
    for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      var xi = poly[i][0], yi = poly[i][1], xj = poly[j][0], yj = poly[j][1];
      if (((yi > py) !== (yj > py)) &&
          (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) c = !c;
    }
    return c;
  }

  /* ---- build the dot field ---- */
  var dots = [], W, H, S, ox, oy, step;

  function build() {
    dots = [];
    var spanX = MAXX - MINX, spanY = MAXY - MINY;
    S = Math.min(W / spanX, H / spanY) * 0.97;
    ox = W / 2 - ((MINX + MAXX) / 2) * S;
    oy = H / 2 + ((MINY + MAXY) / 2) * S;
    step = Math.max(2.6, Math.min(4.6, W / 190));   // screen px between samples

    var g = step / S;                                // grid pitch in metres
    for (var y = MINY; y <= MAXY; y += g) {
      // offset alternate rows: a hex lattice reads smoother than a square one
      var odd = Math.round((y - MINY) / g) % 2;
      for (var x = MINX + (odd ? g / 2 : 0); x <= MAXX; x += g) {
        var tone = -1;
        for (var i = R.length - 1; i >= 0; i--) {
          if (inside(x, y, R[i].p)) { tone = R[i].t; break; }
        }
        if (tone < 0) continue;
        // a soft top-down gradient, so the airframe is lit from above
        var lit = 0.80 + 0.34 * ((y - MINY) / spanY);
        var v = Math.max(0.10, Math.min(1, 0.16 + 0.86 * tone * lit));
        dots.push([ox + x * S, oy - y * S, v]);
      }
    }
  }

  function resize() {
    W = canvas.clientWidth; H = canvas.clientHeight;
    if (!W || !H) return;
    canvas.width = W * DPR; canvas.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    build();
  }

  /* ---- air and cloud lines, drifting aft ---- */
  var air = [];
  for (var i = 0; i < 30; i++) {
    air.push({ y: Math.random(), x: Math.random(), len: 0.04 + Math.random() * 0.17,
               v: 0.02 + Math.random() * 0.055, a: 0.04 + Math.random() * 0.11 });
  }
  var clouds = [];
  for (i = 0; i < 6; i++) {
    clouds.push({ y: Math.random(), x: Math.random(), w: 0.22 + Math.random() * 0.3,
                  v: 0.008 + Math.random() * 0.012, a: 0.05 + Math.random() * 0.05 });
  }

  var mq = window.matchMedia('(prefers-reduced-motion: reduce)');

  function draw(t) {
    ctx.clearRect(0, 0, W, H);

    ctx.lineCap = 'round';
    ctx.lineWidth = 1;
    for (var i = 0; i < air.length; i++) {
      var a = air[i];
      var x = ((a.x - t * a.v) % 1.3 + 1.3) % 1.3 - 0.15;
      ctx.strokeStyle = 'rgba(0,255,65,' + a.a.toFixed(3) + ')';
      ctx.beginPath();
      ctx.moveTo(x * W, a.y * H);
      ctx.lineTo((x + a.len) * W, a.y * H);
      ctx.stroke();
    }
    ctx.lineWidth = 1.4;
    for (i = 0; i < clouds.length; i++) {
      var c = clouds[i];
      var cxp = ((c.x - t * c.v) % 1.5 + 1.5) % 1.5 - 0.25;
      ctx.strokeStyle = 'rgba(0,255,65,' + c.a.toFixed(3) + ')';
      ctx.beginPath();
      var x0 = cxp * W, yy = c.y * H, w = c.w * W;
      ctx.moveTo(x0, yy);
      ctx.bezierCurveTo(x0 + w * 0.3, yy - 11, x0 + w * 0.6, yy - 14, x0 + w, yy - 3);
      ctx.stroke();
    }

    // the airframe, as dots. A slow highlight sweeps nose to tail.
    var sweep = ((t * 0.14) % 1.5) - 0.25;
    var maxR = step * 0.50;
    for (i = 0; i < dots.length; i++) {
      var d = dots[i], v = d[2];
      var rel = d[0] / W;
      var boost = 1 - Math.min(1, Math.abs(rel - sweep) / 0.16);
      var vv = Math.min(1, v + boost * 0.45);
      var r = maxR * (0.38 + 0.62 * vv);
      // cyan in the lit areas, deep blue in the shadows
      var g = Math.round(150 + 95 * vv);
      var b = Math.round(180 + 72 * vv);
      ctx.fillStyle = 'rgba(0,' + g + ',' + b + ',' + (0.42 + 0.58 * vv).toFixed(3) + ')';
      ctx.beginPath();
      ctx.arc(d[0], d[1], r, 0, 6.2832);
      ctx.fill();
    }
  }

  var t0 = null;
  function frame(ts) {
    if (t0 === null) t0 = ts;
    draw((ts - t0) / 1000);
    requestAnimationFrame(frame);
  }

  resize();
  window.addEventListener('resize', function () { resize(); if (mq.matches) draw(0); });
  if (mq.matches) draw(0); else requestAnimationFrame(frame);
})();

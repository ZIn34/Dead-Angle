# -*- coding: utf-8 -*-
import io, sys, re
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

start = s.index('  function makeFlash() {')
end = s.index('  // Wall impact:')
new = '''  function makeFlash() {
    var n = 8, W = 72, H = 52;
    var c = document.createElement('canvas');
    c.width = W * n; c.height = H;
    var g = c.getContext('2d');
    // fixed puff layout so the smoke grows out of one burst rather than
    // flickering into a new shape every frame
    var puffs = [];
    for (var q = 0; q < 14; q++) {
      puffs.push({ a: rr(-0.75, 0.75), d: rr(0.25, 1), r: rr(2.2, 6.4), warm: Math.random() });
    }
    for (var f = 0; f < n; f++) {
      var t = f / (n - 1);
      var heat = Math.sin(Math.min(1, t * 1.35) * Math.PI);
      var ox = f * W, cy = H / 2, bx = ox + 4;
      g.save();
      g.beginPath(); g.rect(ox, 0, W, H); g.clip();

      if (heat > 0.02) {
        // the hot core, thrown forward from the muzzle
        var len = 8 + heat * 40, wid = 3 + heat * 13;
        var lg = g.createLinearGradient(bx, cy, bx + len, cy);
        lg.addColorStop(0, 'rgba(255,255,246,' + (0.98 * heat).toFixed(3) + ')');
        lg.addColorStop(0.28, 'rgba(255,226,130,' + (0.95 * heat).toFixed(3) + ')');
        lg.addColorStop(0.7, 'rgba(246,158,40,' + (0.7 * heat).toFixed(3) + ')');
        lg.addColorStop(1, 'rgba(214,110,20,0)');
        g.fillStyle = lg;
        g.beginPath();
        g.moveTo(bx, cy - wid * 0.5);
        g.quadraticCurveTo(bx + len * 0.5, cy - wid, bx + len, cy);
        g.quadraticCurveTo(bx + len * 0.5, cy + wid, bx, cy + wid * 0.5);
        g.closePath(); g.fill();

        // spikes: two long down the barrel line, four short across it
        g.strokeStyle = 'rgba(255,248,214,' + (0.9 * heat).toFixed(3) + ')';
        g.lineCap = 'round';
        g.lineWidth = 2.6 * heat;
        var spikes = [[1, 0, 1.25], [-1, 0, 0.3], [0, -1, 0.55], [0, 1, 0.55], [0.7, -0.7, 0.7], [0.7, 0.7, 0.7]];
        for (var k = 0; k < spikes.length; k++) {
          var sp = spikes[k];
          g.beginPath();
          g.moveTo(bx, cy);
          g.lineTo(bx + sp[0] * len * sp[2], cy + sp[1] * len * sp[2] * 0.62);
          g.stroke();
        }
        g.fillStyle = 'rgba(255,255,255,' + (0.95 * heat).toFixed(3) + ')';
        g.beginPath(); g.arc(bx + 2, cy, 2 + heat * 3.5, 0, 6.2832); g.fill();
      }

      // rolling smoke, opening up as the flash dies back
      var smoke = Math.max(0, (t - 0.12) / 0.88);
      if (smoke > 0) {
        for (var i = 0; i < puffs.length; i++) {
          var pf = puffs[i];
          if (pf.d > smoke * 1.15) continue;
          var dd = 10 + pf.d * smoke * 46;
          var fade = (1 - smoke * 0.72) * (pf.warm > 0.45 ? 0.85 : 0.6);
          g.fillStyle = pf.warm > 0.45
            ? 'rgba(214,116,36,' + fade.toFixed(3) + ')'
            : 'rgba(158,86,30,' + fade.toFixed(3) + ')';
          g.beginPath();
          g.arc(bx + Math.cos(pf.a) * dd, cy + Math.sin(pf.a) * dd * 0.8,
                pf.r * (0.55 + smoke * 0.8), 0, 6.2832);
          g.fill();
        }
      }
      g.restore();
    }
    FX.flash = fxSheet(c, n, 1, 44, 0);
  }

'''
s = s[:start] + new + s[end:]
assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p35 applied - flash redrawn')

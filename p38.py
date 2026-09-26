# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

start = s.index('  function renderAllies() {')
end = s.index('  // Objectives are map knowledge')
new = '''  function renderAllies() {
    if (!player.alive) return;
    // Everyone on your side, nearest first. Marking a forty-strong horde
    // would be useless, so only the closest handful get one.
    var mates = [];
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (a === player || !a.alive || a.team !== player.team) continue;
      mates.push(a);
    }
    if (!mates.length) return;
    mates.sort(function (x, y) { return dist(x, player) - dist(y, player); });
    if (mates.length > 8) mates.length = 8;

    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (var m = 0; m < mates.length; m++) {
      var t = mates[m];
      var sx = (t.x - cam.x) * zoom + cw / 2;
      var sy = (t.y - cam.y) * zoom + ch / 2;
      var pad = 26;
      var off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
      var ang = Math.atan2(t.y - player.y, t.x - player.x);
      var d = Math.round(dist(t, player));
      sx = clamp(sx, pad, cw - pad);
      sy = clamp(sy, pad, ch - pad);

      ctx.strokeStyle = t.down ? 'rgba(255,77,141,.95)' : 'rgba(124,231,216,.9)';
      ctx.fillStyle = t.down ? 'rgba(255,77,141,.95)' : 'rgba(124,231,216,.9)';
      ctx.lineWidth = 2;

      if (off) {
        ctx.save();
        ctx.translate(sx, sy);
        ctx.rotate(ang);
        ctx.beginPath();
        ctx.moveTo(-5, -6); ctx.lineTo(5, 0); ctx.lineTo(-5, 6);
        ctx.stroke();
        ctx.restore();
        ctx.font = '600 8.5px "IBM Plex Mono", monospace';
        ctx.fillText(d + 'u', sx, sy + 17);
      } else {
        // a chevron and a name, sat above their head
        ctx.beginPath();
        ctx.moveTo(sx - 6, sy - 26); ctx.lineTo(sx, sy - 18); ctx.lineTo(sx + 6, sy - 26);
        ctx.stroke();
        ctx.font = '600 8.5px "IBM Plex Mono", monospace';
        ctx.globalAlpha = 0.85;
        ctx.fillText(t.down ? t.name + ' DOWN' : t.name, sx, sy - 34);
        ctx.globalAlpha = 1;
      }
    }
    ctx.textAlign = 'left';
    ctx.restore();
  }

'''
s = s[:start] + new + s[end:]
assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p38 applied - teammate markers')

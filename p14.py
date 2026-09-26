# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ------------------------------------------------ 1. allied bots stay close -
sub("""          var want = null;
          if (MODE.loot) {
            if (e.hp < 65 && e.meds === 0) want = nearestLoot(e, 'med', 800);
            if (!want && e.reserve < 40) want = nearestLoot(e, 'ammo', 700);
          }""",
"""          var want = null, following = false;
          if (MODE.loot) {
            if (e.hp < 65 && e.meds === 0) want = nearestLoot(e, 'med', 800);
            if (!want && e.reserve < 40) want = nearestLoot(e, 'ammo', 700);
          }
          // squadmates regroup on you instead of wandering off alone
          if (!want && player.alive && e.team === player.team && dist(e, player) > 230) {
            want = { x: player.x, y: player.y };
            following = true;
          }""")

sub("""        pathTo(e, goal.x, goal.y, e.alertT > 0 ? 1.2 : 3.4);""",
    """        pathTo(e, goal.x, goal.y, following ? 0.9 : (e.alertT > 0 ? 1.2 : 3.4));""")

# ------------------------------------------------ 2. ally markers -----------
sub("""  function renderDamage() {""",
"""  // Squadmates are the one thing the dark does not hide - you would be on
  // comms with them. Enemies stay unmarked.
  function renderAllies() {
    if (!player.alive) return;
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (a === player || !a.alive || a.team !== player.team) continue;
      var sx = (a.x - cam.x) * zoom + cw / 2;
      var sy = (a.y - cam.y) * zoom + ch / 2;
      var pad = 26;
      var off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
      var ang = Math.atan2(a.y - player.y, a.x - player.x);
      if (off) {
        sx = clamp(sx, pad, cw - pad);
        sy = clamp(sy, pad, ch - pad);
      }
      ctx.save();
      ctx.translate(sx, sy);
      ctx.globalAlpha = off ? 0.85 : 0.6;
      ctx.strokeStyle = '#7ce7d8';
      ctx.lineWidth = 2;
      if (off) {
        ctx.rotate(ang);
        ctx.beginPath();
        ctx.moveTo(-5, -6); ctx.lineTo(5, 0); ctx.lineTo(-5, 6);
        ctx.stroke();
        ctx.rotate(-ang);
        ctx.fillStyle = 'rgba(124,231,216,.85)';
        ctx.font = '600 9px "IBM Plex Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText(Math.round(dist(a, player)) + 'u', 0, 18);
      } else {
        ctx.beginPath();
        ctx.moveTo(-5, -20); ctx.lineTo(0, -13); ctx.lineTo(5, -20);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      ctx.restore();
    }
    ctx.textAlign = 'left';
  }

  // ---- minimap: only ground you have actually seen ------------------------
  var mini = null, miniAge = 0;
  function drawMinimap() {
    if (!mini) mini = document.createElement('canvas');
    if (mini.width !== MAP_W || mini.height !== MAP_H) {
      mini.width = MAP_W; mini.height = MAP_H; miniAge = 0;
    }
    if (miniAge <= 0) {
      miniAge = 20;                       // a repaint every 20 frames is plenty
      var g = mini.getContext('2d');
      var img = g.createImageData(MAP_W, MAP_H);
      var d = img.data;
      for (var y = 0; y < MAP_H; y++) for (var x = 0; x < MAP_W; x++) {
        var o4 = (y * MAP_W + x) * 4, gi = y * STRIDE + x;
        if (!explored[gi]) { d[o4 + 3] = 0; continue; }
        var wall = grid[gi] === 1;
        d[o4] = wall ? 62 : 20;
        d[o4 + 1] = wall ? 82 : 30;
        d[o4 + 2] = wall ? 106 : 42;
        d[o4 + 3] = wall ? 240 : 190;
      }
      g.putImageData(img, 0, 0);
    }
    miniAge--;

    var S = Math.round(Math.min(148, Math.min(cw, ch) * 0.30));
    var bx = 16, by = 16;
    var span = MAP_W * TILE;
    function mx(wx) { return bx + (wx / span) * S; }
    function my(wy) { return by + (wy / (MAP_H * TILE)) * S; }

    ctx.save();
    ctx.fillStyle = 'rgba(8,12,18,.78)';
    ctx.fillRect(bx, by, S, S);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(mini, bx, by, S, S);
    ctx.imageSmoothingEnabled = true;

    if (zone) {
      ctx.strokeStyle = 'rgba(255,77,141,.75)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.arc(mx(zone.cx), my(zone.cy), zone.r / span * S, 0, 6.2832);
      ctx.stroke();
      if (!zone.closing && zone.nr) {
        ctx.strokeStyle = 'rgba(210,222,236,.4)';
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(mx(zone.nx), my(zone.ny), zone.nr / span * S, 0, 6.2832);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a.alive || a === player || a.team !== player.team) continue;
      ctx.fillStyle = '#7ce7d8';
      ctx.beginPath(); ctx.arc(mx(a.x), my(a.y), 2.4, 0, 6.2832); ctx.fill();
    }
    if (player.alive) {
      ctx.fillStyle = '#eaf4ff';
      ctx.beginPath(); ctx.arc(mx(player.x), my(player.y), 2.8, 0, 6.2832); ctx.fill();
      ctx.strokeStyle = '#eaf4ff';
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(mx(player.x), my(player.y));
      ctx.lineTo(mx(player.x) + Math.cos(player.ang) * 8, my(player.y) + Math.sin(player.ang) * 8);
      ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(146,170,196,.35)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, S - 1, S - 1);
    ctx.restore();
  }

  function renderDamage() {""")

sub("""    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    renderPrompt();
    renderDamage();""",
"""    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    renderAllies();
    drawMinimap();
    renderPrompt();
    renderDamage();""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p14 applied')

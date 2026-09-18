# -*- coding: utf-8 -*-
"""Split screen: two local players, two viewports, two input devices."""
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

# ---------------------------------------------------------------- state ----
sub("""  var player = null, zone = null;""",
"""  var player = null, zone = null;
  // Local players (one or two) and, during a draw, whose eyes we are using.
  var players = [], viewer = null, splitOn = false;
  var VX = 0, VY = 0, VW = 0, VH = 0;      // the viewport being drawn into""")

# sight is always from whoever is being drawn for
sub("""  function visibleToPlayer(x, y) {
    var dx = x - player.x, dy = y - player.y;
    return dx * dx + dy * dy < VIEW_R * VIEW_R && sightClear(player.x, player.y, x, y);
  }
  function litVisible(x, y, reach) {
    var dx = x - player.x, dy = y - player.y;
    return dx * dx + dy * dy < reach * reach && sightClear(player.x, player.y, x, y);
  }""",
"""  function visibleToPlayer(x, y) {
    var v = viewer || player;
    var dx = x - v.x, dy = y - v.y;
    return dx * dx + dy * dy < VIEW_R * VIEW_R && sightClear(v.x, v.y, x, y);
  }
  function litVisible(x, y, reach) {
    var v = viewer || player;
    var dx = x - v.x, dy = y - v.y;
    return dx * dx + dy * dy < reach * reach && sightClear(v.x, v.y, x, y);
  }""")

# ---------------------------------------------------------------- pads -----
sub("""  var pad = null, padPrev = {}, padSeen = false, padLast = -1e9;""",
"""  function getPad(i) {
    var l = navigator.getGamepads ? navigator.getGamepads() : null;
    return (l && l[i] && l[i].connected) ? l[i] : null;
  }
  function padCount() {
    var l = navigator.getGamepads ? navigator.getGamepads() : null, n = 0;
    if (l) for (var i = 0; i < l.length; i++) if (l[i] && l[i].connected) n++;
    return n;
  }
  function axOf(g, i) {
    if (!g || !g.axes || g.axes.length <= i) return 0;
    var v = g.axes[i], dz = SET.dead / 100;
    if (v > -dz && v < dz) return 0;
    return (v - (v > 0 ? dz : -dz)) / (1 - dz);
  }
  function downOf(g, i) { return !!(g && g.buttons && g.buttons[i] && g.buttons[i].pressed); }
  function hitOf(g, prev, i) {
    var now = downOf(g, i), was = prev[i];
    prev[i] = now;
    return now && !was;
  }

  var pad = null, padPrev = {}, padSeen = false, padLast = -1e9;""")

# ---------------------------------------------------------------- camera ---
sub("""    e.hp = (MODE.zombies && e.team === 1) ? 38 : 100;
    e.alive = true; e.respawnT = 0;""",
"""    e.hp = (MODE.zombies && e.team === 1) ? 38 : 100;
    e.alive = true; e.respawnT = 0;
    e.camX = e.x; e.camY = e.y;""")

sub("""    var tx = player.x, ty = player.y;
    if (!touchMode) {
      tx += clamp(mouse.wx - player.x, -110, 110) * 0.2;
      ty += clamp(mouse.wy - player.y, -110, 110) * 0.2;
    }
    var lerp = 1 - Math.pow(0.0001, dt);
    cam.x += (tx - cam.x) * lerp;
    cam.y += (ty - cam.y) * lerp;""",
"""    var lerp = 1 - Math.pow(0.0001, dt);
    for (i = 0; i < players.length; i++) {
      var pl = players[i];
      var tx = pl.x, ty = pl.y;
      if (pl.padIndex < 0 && !touchMode) {          // the mouse leads the camera
        tx += clamp(mouse.wx - pl.x, -110, 110) * 0.2;
        ty += clamp(mouse.wy - pl.y, -110, 110) * 0.2;
      }
      pl.camX += (tx - pl.camX) * lerp;
      pl.camY += (ty - pl.camY) * lerp;
    }""")

sub("""  function setCamTransform() {
    var sk = SET.shake ? shake : 0;
    var sx = sk ? rr(-sk, sk) : 0;
    var sy = sk ? rr(-sk, sk) : 0;
    ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom,
      dpr * (cw / 2 - cam.x * zoom + sx), dpr * (ch / 2 - cam.y * zoom + sy));
  }""",
"""  function setCamTransform() {
    var sk = SET.shake ? shake : 0;
    var sx = sk ? rr(-sk, sk) : 0;
    var sy = sk ? rr(-sk, sk) : 0;
    ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom,
      dpr * (VX + VW / 2 - cam.x * zoom + sx), dpr * (VY + VH / 2 - cam.y * zoom + sy));
  }""")

# ---------------------------------------------------------------- render ---
sub("""  function render() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#04060a';
    ctx.fillRect(0, 0, cw, ch);
    if (state === 'menu' || state === 'over') { renderAmbient(); return; }

    var halfW = cw / (2 * zoom), halfH = ch / (2 * zoom);""",
"""  function render() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#04060a';
    ctx.fillRect(0, 0, cw, ch);
    if (state === 'menu' || state === 'over') { renderAmbient(); return; }
    if (!players.length) return;

    if (players.length < 2) {
      VX = 0; VY = 0; VW = cw; VH = ch;
      players[0].vx = VX; players[0].vy = VY; players[0].vw = VW; players[0].vh = VH;
      renderView(players[0]);
      return;
    }

    // side by side on a wide screen, stacked on a tall one
    var side = cw >= ch;
    for (var pi = 0; pi < 2; pi++) {
      if (side) { VX = pi * (cw / 2); VY = 0; VW = cw / 2; VH = ch; }
      else { VX = 0; VY = pi * (ch / 2); VW = cw; VH = ch / 2; }
      var pl2 = players[pi];
      pl2.vx = VX; pl2.vy = VY; pl2.vw = VW; pl2.vh = VH;
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.beginPath(); ctx.rect(VX, VY, VW, VH); ctx.clip();
      renderView(pl2);
      ctx.restore();
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.strokeStyle = 'rgba(146,170,196,.4)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (side) { ctx.moveTo(cw / 2, 0); ctx.lineTo(cw / 2, ch); }
    else { ctx.moveTo(0, ch / 2); ctx.lineTo(cw, ch / 2); }
    ctx.stroke();
  }

  function renderView(self) {
    viewer = self;
    cam.x = self.camX; cam.y = self.camY;

    var halfW = VW / (2 * zoom), halfH = VH / (2 * zoom);""")

sub("""    computeVisibility(player.x, player.y, VIEW_R);
    exploreTick++;
    if (exploreTick % 3 === 0) markExplored(player.x, player.y);""",
"""    computeVisibility(self.x, self.y, VIEW_R);
    exploreTick++;
    if (exploreTick % 3 === 0) markExplored(self.x, self.y);""")

sub("""    for (i = 0; i < visPts.length; i += 2) {
      var ox = visPts[i] - player.x, oy = visPts[i + 1] - player.y;""",
"""    for (i = 0; i < visPts.length; i += 2) {
      var ox = visPts[i] - self.x, oy = visPts[i + 1] - self.y;""")

sub("""      if (!en.alive || en === player) continue;
      if (!visibleToPlayer(en.x, en.y)) continue;
      drawUnit(en, en.team === player.team ? '#8ff0e4' : '#ff7a4d');""",
"""      if (!en.alive || en === self) continue;
      if (!visibleToPlayer(en.x, en.y)) continue;
      drawUnit(en, en.team === self.team ? '#8ff0e4' : '#ff7a4d');""")

sub("""    var g = ctx.createRadialGradient(player.x, player.y, VIEW_R * 0.18, player.x, player.y, VIEW_R);""",
    """    var g = ctx.createRadialGradient(self.x, self.y, VIEW_R * 0.18, self.x, self.y, VIEW_R);""")
sub("""    ctx.fillRect(player.x - VIEW_R, player.y - VIEW_R, VIEW_R * 2, VIEW_R * 2);""",
    """    ctx.fillRect(self.x - VIEW_R, self.y - VIEW_R, VIEW_R * 2, VIEW_R * 2);""")

sub("""      var own = s.owner === player.id;""", """      var own = s.owner === self.id;""")

sub("""    if (player.alive) drawUnit(player, curW(player) ? '#8ff0e4' : '#5d7288');

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    renderAllies();
    renderObjectives();
    if (SET.minimap) drawMinimap();
    renderReticle();
    renderDowned();
    renderPrompt();
    renderDamage();
    if (touchMode) renderSticks();
  }""",
"""    if (self.alive) drawUnit(self, curW(self) ? '#8ff0e4' : '#5d7288');

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    renderAllies();
    renderObjectives();
    if (SET.minimap) drawMinimap();
    renderReticle();
    renderDowned();
    renderPrompt();
    renderDamage();
    if (splitOn) drawSplitHud(self);
    if (touchMode && self === player) renderSticks();
    viewer = null;
  }""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p40 applied - viewports and viewer indirection')

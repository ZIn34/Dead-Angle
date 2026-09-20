# -*- coding: utf-8 -*-
"""A sniper in your hands sees twice as far, and the camera pulls back to match."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b, n=1):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, n)

# ---- how far the one we are drawing for can see ---------------------------------
sub("""  var cw = 0, ch = 0, dpr = 1, zoom = 1;""",
"""  var cw = 0, ch = 0, dpr = 1, zoom = 1, zoom0 = 1;
  // The sniper is the long-range gun, so holding one opens the view up: twice
  // the sight, and the camera pulls back by the same amount so you can use it.
  var SNIPE_SIGHT = 2, VIEW_MUL = 1;
  function sightR() { return VIEW_R * VIEW_MUL; }
  function sightWant(e) {
    var sl = e && e.alive && !e.air ? curSlot(e) : null;
    return sl && sl.key === 'rifle' ? SNIPE_SIGHT : 1;
  }
  function sightTick(dt) {
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i];
      if (L.sightM === undefined) L.sightM = 1;
      L.sightM += (sightWant(L) - L.sightM) * Math.min(1, dt * 4);
    }
  }""")
sub("""    zoom = Math.max(0.55, Math.min(2.4, Math.min(cw, ch) / (VIEW_BASE * 2 + 60)));""",
    """    zoom = zoom0 = Math.max(0.55, Math.min(2.4, Math.min(cw, ch) / (VIEW_BASE * 2 + 60)));""")

# ---- everything that asks how far you can see ------------------------------------
sub("""    return dx * dx + dy * dy < VIEW_R * VIEW_R && sightClear(player.x, player.y, x, y);""",
    """    var sr = sightR();
    return dx * dx + dy * dy < sr * sr && sightClear(player.x, player.y, x, y);""")
sub("""    computeVisibility(player.x, player.y, VIEW_R);""",
    """    var VR = sightR();
    computeVisibility(player.x, player.y, VR);""")
sub("""      var push = od < VIEW_R - 2 ? TILE * 0.95 : 0;""",
    """      var push = od < VR - 2 ? TILE * 0.95 : 0;""")
sub("""    var cone = new Path2D(), cR = VIEW_R + TILE * 3;""",
    """    var cone = new Path2D(), cR = VR + TILE * 3;""")
sub("""    var g = ctx.createRadialGradient(player.x, player.y, VIEW_R * 0.18, player.x, player.y, VIEW_R);""",
    """    var g = ctx.createRadialGradient(player.x, player.y, VR * 0.18, player.x, player.y, VR);""")
sub("""    ctx.fillRect(player.x - VIEW_R, player.y - VIEW_R, VIEW_R * 2, VIEW_R * 2);""",
    """    ctx.fillRect(player.x - VR, player.y - VR, VR * 2, VR * 2);""")
sub("""    var reach = blackout ? FLASH_REACH : VIEW_R;""",
    """    var reach = blackout ? FLASH_REACH : VR;""")

# ---- the camera, so the extra sight is actually on screen --------------------------
sub("""      VX = 0; VY = 0; VW = cw; VH = ch;
      player.viewX = 0; player.viewY = 0; player.viewW = cw; player.viewH = ch; player.zoom = zoom;""",
"""      VX = 0; VY = 0; VW = cw; VH = ch;
      zoom = Math.max(0.45, zoom0 / (player.sightM || 1));
      VIEW_MUL = zoom0 / zoom;
      player.viewX = 0; player.viewY = 0; player.viewW = cw; player.viewH = ch; player.zoom = zoom;""")
sub("""      L.zoom = Math.max(0.5, Math.min(2.4, Math.min(VW, VH) / (VIEW_BASE * 2 + 60)));""",
"""      var zBase = Math.max(0.5, Math.min(2.4, Math.min(VW, VH) / (VIEW_BASE * 2 + 60)));
      L.zoom = Math.max(0.45, zBase / (L.sightM || 1));
      VIEW_MUL = zBase / L.zoom;""")
# a kill cam or a spectated teammate is seen through their eyes, at their reach
sub("""    cw = fullW; ch = fullH; zoom = z0; player = p0; cam = cam0; promptItem = pr0;""",
    """    cw = fullW; ch = fullH; zoom = z0; player = p0; cam = cam0; promptItem = pr0; VIEW_MUL = 1;""")

# ---- keep it ticking, here and on someone else's host --------------------------------
sub("""    pingTick(dt);
    specTick();""", """    pingTick(dt);
    sightTick(dt);
    specTick();""")
sub("""    killcamTick(dt);
    specTick();""", """    killcamTick(dt);
    sightTick(dt);
    specTick();""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p70 applied')

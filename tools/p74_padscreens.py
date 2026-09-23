# -*- coding: utf-8 -*-
"""The kit and the map have to close from inside them: on a pad the button that
opened them was only read further down, past the point those screens return."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- read the screen buttons before the screens swallow the frame ---------------
sub("""    if (e.invOpen && I.pad && I.padOn) {
      // the stick walks the list, so you are not also walking into a wall""",
"""    // These come first: while the kit or the map is up the rest of this
    // function returns early, so anything read later could never close them.
    if (I.pad) {
      if (I.hit(PAD.map)) { e.mapOpen = !e.mapOpen; e.mapCur = null; }
      if (I.hit(PAD.inv)) { e.invOpen = !e.invOpen; e.invSel = 0; }
      if ((e.invOpen || e.mapOpen) && I.hit(PAD.pause)) { pause(); return; }
    }
    if (e.invOpen && I.pad && I.padOn) {
      // the stick walks the list, so you are not also walking into a wall""")
# B closes the kit as well as dropping, since B is "back" everywhere else
sub("""      if (I.hit(PAD.drop)) invDrop(e);
      e._spd = 0; e.moving = false; e.prompt = null;""",
"""      if (I.hit(PAD.drop)) invDrop(e);
      if (I.hit(PAD.pickup)) { e.invOpen = false; }      // X backs out
      e._spd = 0; e.moving = false; e.prompt = null;""")
sub("""      e.mapCur.y = clamp(e.mapCur.y + I.ax(1) * mtall * 0.4 * dt, 0, mtall);
      e._spd = 0; e.moving = false; e.prompt = null;""",
"""      e.mapCur.y = clamp(e.mapCur.y + I.ax(1) * mtall * 0.4 * dt, 0, mtall);
      if (I.hit(PAD.ping)) pingAt(e, e.mapCur.x, e.mapCur.y);
      if (I.hit(PAD.drop)) e.mapOpen = false;            // B backs out
      e._spd = 0; e.moving = false; e.prompt = null;""")
# they were read down here, too late to ever matter
sub("""      if (I.hit(PAD.map)) { e.mapOpen = !e.mapOpen; e.mapCur = null; }
      if (I.hit(PAD.inv)) { e.invOpen = !e.invOpen; e.invSel = 0; }
      if (I.hit(PAD.ping)) { if (e.mapOpen && e.mapCur) pingAt(e, e.mapCur.x, e.mapCur.y); else pingAhead(e); }""",
"""      if (I.hit(PAD.ping)) pingAhead(e);""")

# ---- the same screens for a pad on someone else's host ---------------------------
sub("""    if (player && !player.alive && player.spec && pad && !netGuestPaused) {
      if (padHit(PAD.swapL)) specCycle(player, -1);
      if (padHit(PAD.swapR)) specCycle(player, 1);
    }""",
"""    if (player && !player.alive && player.spec && pad && !netGuestPaused) {
      if (padHit(PAD.swapL)) specCycle(player, -1);
      if (padHit(PAD.swapR)) specCycle(player, 1);
    }
    // the kit and the map are drawn on this machine, so they open and close here
    if (player && pad && !netGuestPaused && state === 'play') {
      if (padHit(PAD.inv)) { player.invOpen = !player.invOpen; player.invSel = 0; }
      if (padHit(PAD.map)) { player.mapOpen = !player.mapOpen; player.mapCur = null; }
      if (player.invOpen) {
        var giy = padAxis(1);
        player.invT = Math.max(0, (player.invT || 0) - dt);
        if (Math.abs(giy) > 0.55 && player.invT <= 0) { invMove(player, giy > 0 ? 1 : -1); player.invT = 0.18; }
        if (padHit(PAD.drop)) invDrop(player);
        if (padHit(PAD.pickup)) player.invOpen = false;
      } else if (player.mapOpen) {
        var gspan = MAP_W * TILE, gtall = MAP_H * TILE;
        if (!player.mapCur) player.mapCur = { x: player.x, y: player.y };
        player.mapCur.x = clamp(player.mapCur.x + padAxis(0) * gspan * 0.4 * dt, 0, gspan);
        player.mapCur.y = clamp(player.mapCur.y + padAxis(1) * gtall * 0.4 * dt, 0, gtall);
        if (padHit(PAD.ping)) pingAt(player, player.mapCur.x, player.mapCur.y);
        if (padHit(PAD.drop)) player.mapOpen = false;
      } else if (padHit(PAD.ping)) pingAhead(player);
    }""")
# and a guest reading their kit does not walk off while they read it
sub("""      if (!mx && !my) {
        if (keys['a']) mx -= 1; if (keys['d']) mx += 1;
        if (keys['w']) my -= 1; if (keys['s']) my += 1;
        var ml = Math.sqrt(mx * mx + my * my);
        if (ml > 1) { mx /= ml; my /= ml; }
      }""",
"""      if (!mx && !my) {
        if (keys['a']) mx -= 1; if (keys['d']) mx += 1;
        if (keys['w']) my -= 1; if (keys['s']) my += 1;
        var ml = Math.sqrt(mx * mx + my * my);
        if (ml > 1) { mx /= ml; my /= ml; }
      }
      if (padActive() && (player.invOpen || player.mapOpen)) { mx = 0; my = 0; }""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p74 applied')

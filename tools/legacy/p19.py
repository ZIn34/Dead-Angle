# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ============================================================ tactical wall ==
# Step up to the end of a wall and you snap onto a peek line running past the
# corner. Sliding along it moves you physically, so how much you can see and
# how much they can see of you are the same number - the geometry already
# decides it. Space breaks the lock; holding Space stops it ever grabbing.
sub("""  var promptItem = null;""",
"""  var promptItem = null;
  var lean = { on: false, x0: 0, y0: 0, dx: 0, dy: 0, len: 0, peek: 0, cx: 0, cy: 0, cool: 0 };

  function breakLean() {
    lean.on = false;
    lean.cool = 0.45;          // don't re-grab the moment you step away
  }

  // The end of a wall run you could actually shoot around.
  function findCorner(e) {
    var best = null, bestD = 36 * 36;
    var ax = Math.cos(e.ang), ay = Math.sin(e.ang);
    for (var i = 0; i < segs.length; i++) {
      var sg = segs[i];
      for (var k = 0; k < 2; k++) {
        var ex = k ? sg.bx : sg.ax, ey = k ? sg.by : sg.ay;
        var ox = k ? sg.ax : sg.bx, oy = k ? sg.ay : sg.by;
        var ddx = ex - e.x, ddy = ey - e.y;
        var d2 = ddx * ddx + ddy * ddy;
        if (d2 > bestD) continue;

        var vx = ex - ox, vy = ey - oy;
        var vl = Math.sqrt(vx * vx + vy * vy) || 1;
        vx /= vl; vy /= vl;                       // peek direction, past the corner
        if (ax * vx + ay * vy < 0.15) continue;   // must be facing that way

        // whichever side of the wall is open is the side you stand on
        var mx = (ex + ox) / 2, my = (ey + oy) / 2;
        var px = -vy, py = vx;
        if (wallAt(mx + px * TILE * 0.6, my + py * TILE * 0.6)) { px = -px; py = -py; }
        if (wallAt(mx + px * TILE * 0.6, my + py * TILE * 0.6)) continue;   // not a wall face

        var offx = px * (e.r + 3), offy = py * (e.r + 3);
        var back = e.r + 13, out = e.r + 11;
        var x0 = ex - vx * back + offx, y0 = ey - vy * back + offy;
        if (solid(x0, y0, e.r)) continue;
        if (solid(ex + vx * out + offx, ey + vy * out + offy, e.r)) continue;  // nothing to lean into

        bestD = d2;
        best = { x0: x0, y0: y0, dx: vx, dy: vy, len: back + out, cx: ex, cy: ey };
      }
    }
    return best;
  }

  function updateLean(e, dt, ix, iy) {
    if (lean.cool > 0) lean.cool -= dt;
    var held = !!keys[' '];

    if (lean.on) {
      if (held || !e.alive) { breakLean(); return false; }
      var along = ix * lean.dx + iy * lean.dy;
      if (along) {
        lean.peek += along * 150 * dt / lean.len;
        if (lean.peek < -0.03 || lean.peek > 1.03) { breakLean(); return false; }
        lean.peek = clamp(lean.peek, 0, 1);
        e.stepT -= dt;
        if (e.stepT <= 0) { e.stepT = 0.62; emit(e.x, e.y, MOVE_SND.walk, e.id, 'walk'); }
      }
      var nx = lean.x0 + lean.dx * lean.len * lean.peek;
      var ny = lean.y0 + lean.dy * lean.len * lean.peek;
      if (solid(nx, ny, e.r)) { breakLean(); return false; }
      e.x = nx; e.y = ny;
      e._spd = 0;                               // braced
      return true;
    }

    if (held || lean.cool > 0 || !e.alive) return false;
    var c = findCorner(e);
    if (!c) return false;
    // start from wherever along the line you already are, biased to cover
    var t = ((e.x - c.x0) * c.dx + (e.y - c.y0) * c.dy) / c.len;
    lean.on = true;
    lean.x0 = c.x0; lean.y0 = c.y0; lean.dx = c.dx; lean.dy = c.dy;
    lean.len = c.len; lean.cx = c.cx; lean.cy = c.cy;
    lean.peek = clamp(t, 0.10, 0.55);
    return true;
  }""")

# hook it into the player's movement
sub("""    var sprinting = !!keys['shift'] && (ix || iy);
    var base = curW(e) ? 168 : 190;""",
"""    if (updateLean(e, dt, ix, iy)) {
      // locked to the corner: aim and fire still work, feet do not
      if (sticks.aim) {
        var ladx = sticks.aim.x - sticks.aim.ox, lady = sticks.aim.y - sticks.aim.oy;
        if (Math.sqrt(ladx * ladx + lady * lady) > 10) e.ang = Math.atan2(lady, ladx);
      } else e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
      e.fireT -= dt;
      if (e.reloadT > 0) {
        e.reloadT -= dt;
        if (e.reloadT <= 0) finishReload(e);
      }
      var lfire = mouse.down || (sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
      if (lfire && curW(e)) {
        if (curSlot(e).ammo <= 0) startReload(e);
        else fire(e);
      }
      return;
    }
    var sprinting = !!keys['shift'] && (ix || iy);
    var base = curW(e) ? 168 : 190;""")

# bracing against cover steadies the shot
sub("""    var spread = w.spread + (e.bot ? DIFF[difficulty].spread : (e._spd > 200 ? 0.055 : (e._spd > 0 ? 0.022 : 0)));""",
"""    var spread = w.spread + (e.bot ? DIFF[difficulty].spread : (e._spd > 200 ? 0.055 : (e._spd > 0 ? 0.022 : 0)));
    if (!e.bot && lean.on) spread *= 0.5;      // braced on the corner""")

sub("""    dmgMarks = []; shake = 0; promptItem = null;""",
    """    dmgMarks = []; shake = 0; promptItem = null;
    lean.on = false; lean.cool = 0;""")

# ---- what the player sees while locked -----------------------------------
sub("""  function renderPrompt() {""",
"""  function renderLean() {
    if (!lean.on || !player.alive) return;
    // the peek line and the corner it pivots on, drawn in world space
    ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom,
      dpr * (cw / 2 - cam.x * zoom), dpr * (ch / 2 - cam.y * zoom));
    ctx.strokeStyle = 'rgba(242,189,29,.35)';
    ctx.lineWidth = 1.6 / zoom;
    ctx.beginPath();
    ctx.moveTo(lean.x0, lean.y0);
    ctx.lineTo(lean.x0 + lean.dx * lean.len, lean.y0 + lean.dy * lean.len);
    ctx.stroke();
    ctx.fillStyle = 'rgba(242,189,29,.85)';
    ctx.beginPath(); ctx.arc(lean.cx, lean.cy, 3.2, 0, 6.2832); ctx.fill();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // exposure read-out and the way out
    var label = 'SPACE  \\u00b7  BREAK COVER';
    ctx.font = '600 11px "IBM Plex Mono", monospace';
    var tw = ctx.measureText(label).width;
    var boxW = tw + 30, boxH = 26;
    var bx = cw / 2 - boxW / 2, by = ch * 0.76;
    ctx.fillStyle = 'rgba(10,15,22,.85)';
    ctx.fillRect(bx, by, boxW, boxH);
    ctx.strokeStyle = 'rgba(242,189,29,.6)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, boxW - 1, boxH - 1);
    ctx.fillStyle = '#f2bd1d';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, bx + 15, by + boxH / 2 + 1);

    var mw = boxW, mh = 3, my2 = by - 9;
    ctx.fillStyle = 'rgba(44,61,82,.7)';
    ctx.fillRect(bx, my2, mw, mh);
    ctx.fillStyle = '#f2bd1d';
    ctx.fillRect(bx, my2, mw * lean.peek, mh);
    ctx.fillStyle = 'rgba(198,212,227,.5)';
    ctx.font = '600 8.5px "IBM Plex Mono", monospace';
    ctx.fillText('COVER', bx, my2 - 8);
    ctx.textAlign = 'right';
    ctx.fillText('EXPOSED', bx + mw, my2 - 8);
    ctx.textAlign = 'left';
  }

  function renderPrompt() {""")

sub("""    renderAllies();
    drawMinimap();
    renderPrompt();""",
"""    renderAllies();
    drawMinimap();
    renderLean();
    renderPrompt();""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p19 applied')

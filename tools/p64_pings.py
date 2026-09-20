# -*- coding: utf-8 -*-
"""Map marks you can drop for your team, and the map itself, full screen."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- buttons -------------------------------------------------------------------
sub("""  var PAD = { reload: 0, jump: 0, drop: 1, giveup: 1, pickup: 2, stim: 3, swapL: 4, swapR: 5,
              sprint: 6, fire: 7, pause: 9, melee2: 11, melee: 12, frag: 14, smoke: 15 };""",
"""  var PAD = { reload: 0, jump: 0, drop: 1, giveup: 1, pickup: 2, stim: 3, swapL: 4, swapR: 5,
              sprint: 6, fire: 7, map: 8, pause: 9, inv: 10, melee2: 11, melee: 12, ping: 13,
              frag: 14, smoke: 15 };""")

# ---- the marks themselves -------------------------------------------------------
sub("""  // ---- minimap: only ground you have actually seen ------------------------""",
"""  // ---- map marks: point at a spot and your side sees it ----------------------
  var pings = [], PING_LIFE = 18;
  function addPing(by, x, y) {
    if (!by) return;
    for (var i = pings.length - 1; i >= 0; i--) if (pings[i].by === by.id) pings.splice(i, 1);
    pings.push({ x: Math.round(x), y: Math.round(y), team: by.team, by: by.id, name: by.name || '', t: 0 });
    if (player && by.team === player.team) audioEmit(by.x, by.y, PICK_SND, by.id);
  }
  // A guest asks the host, so everyone's map agrees.
  function pingAt(e, x, y) {
    if (!e) return;
    x = clamp(x, 0, MAP_W * TILE); y = clamp(y, 0, MAP_H * TILE);
    if (netGuest) { netSend({ t: 'pg', x: Math.round(x), y: Math.round(y) }); return; }
    addPing(e, x, y);
  }
  function pingAhead(e) { pingAt(e, e.x + Math.cos(e.ang) * 700, e.y + Math.sin(e.ang) * 700); }
  function pingTick(dt) {
    for (var i = pings.length - 1; i >= 0; i--) { pings[i].t += dt; if (pings[i].t > PING_LIFE) pings.splice(i, 1); }
  }
  function myPings() {
    var out = [];
    for (var i = 0; i < pings.length; i++) if (pings[i].team === player.team) out.push(pings[i]);
    return out;
  }
  // a mark stands out in the world too, wherever you are looking
  function renderPings() {
    if (noOverlay) return;
    var list = myPings();
    if (!list.length) return;
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    for (var i = 0; i < list.length; i++) {
      var p = list[i];
      var fade = Math.min(1, (PING_LIFE - p.t) / 2.5);
      var sx = (p.x - cam.x) * zoom + cw / 2, sy = (p.y - cam.y) * zoom + ch / 2;
      var pd = 30, off = sx < pd || sx > cw - pd || sy < pd || sy > ch - pd;
      sx = clamp(sx, pd, cw - pd); sy = clamp(sy, pd, ch - pd);
      var pulse = 1 + Math.sin(performance.now() / 200 + i) * 0.14;
      ctx.globalAlpha = fade;
      ctx.strokeStyle = '#0d0f12'; ctx.fillStyle = '#f2bd1d';
      ctx.shadowColor = '#f2bd1d'; ctx.shadowBlur = 10;
      ctx.save();
      ctx.translate(sx, sy - (off ? 0 : 16));
      ctx.scale(pulse, pulse);
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(0, -13); ctx.lineTo(9, 0); ctx.lineTo(0, 13); ctx.lineTo(-9, 0); ctx.closePath();
      ctx.stroke(); ctx.fill();
      ctx.restore();
      ctx.shadowBlur = 0;
      ctx.font = '700 10px "IBM Plex Mono", monospace';
      pill(Math.round(dist(p, player)) + 'u', sx, sy + (off ? 24 : 6), '#f2bd1d');
    }
    ctx.restore();
  }

  // ---- minimap: only ground you have actually seen ------------------------""")

# ---- one map drawing routine, small in the corner or filling the screen ----------
sub("""  function drawMinimap() {
    if (!mini) mini = document.createElement('canvas');""",
"""  var mapRect = null;
  function drawMinimap() {
    var S = Math.round(Math.min(148, Math.min(cw, ch) * 0.30));
    drawMapInto(16, Math.max(60, ch - S - (splitOn ? 78 : 158)), S, false);
  }
  // The whole map, for reading the ground and dropping a mark on it.
  function drawBigMap() {
    ctx.save();
    ctx.fillStyle = 'rgba(4,6,10,.74)';
    ctx.fillRect(0, 0, cw, ch);
    var S = Math.round(Math.min(cw, ch) * 0.78);
    var bx = Math.round((cw - S) / 2), by = Math.round((ch - S) / 2);
    drawMapInto(bx, by, S, true);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '400 15px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillStyle = '#f1e7d0';
    ctx.fillText('MAP', cw / 2, by - 22);
    ctx.font = '600 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(241,231,208,.75)';
    ctx.fillText(usingPad(player)
      ? 'LEFT STICK MOVES THE CURSOR  \\u00b7  D-PAD DOWN MARKS  \\u00b7  BACK CLOSES'
      : 'CLICK TO MARK  \\u00b7  M CLOSES', cw / 2, by + S + 20);
    ctx.restore();
  }
  function drawMapInto(bx, by, S, big) {
    if (!mini) mini = document.createElement('canvas');""")
sub("""    var S = Math.round(Math.min(148, Math.min(cw, ch) * 0.30));
    // bottom left, above your health and kit
    var bx = 16, by = Math.max(60, ch - S - (splitOn ? 78 : 158));
    var span = MAP_W * TILE;""",
"""    var span = MAP_W * TILE;""")
# marks, the pad cursor, and where a click lands
sub("""    ctx.strokeStyle = 'rgba(146,170,196,.35)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, S - 1, S - 1);
    ctx.restore();
  }""",
"""    var mp = myPings(), sc = big ? 1.9 : 1;
    for (var pq = 0; pq < mp.length; pq++) {
      var pk = mp[pq], pz = (3.6 + Math.sin(performance.now() / 200 + pq) * 0.7) * sc;
      ctx.globalAlpha = Math.min(1, (PING_LIFE - pk.t) / 2.5);
      ctx.fillStyle = '#f2bd1d'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 2 * sc;
      ctx.beginPath();
      ctx.moveTo(mx(pk.x), my(pk.y) - pz); ctx.lineTo(mx(pk.x) + pz, my(pk.y));
      ctx.lineTo(mx(pk.x), my(pk.y) + pz); ctx.lineTo(mx(pk.x) - pz, my(pk.y));
      ctx.closePath(); ctx.stroke(); ctx.fill();
      ctx.globalAlpha = 1;
    }
    if (big && player.mapCur) {
      var cx2 = mx(player.mapCur.x), cy2 = my(player.mapCur.y);
      ctx.strokeStyle = '#eaf4ff'; ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(cx2 - 9, cy2); ctx.lineTo(cx2 + 9, cy2);
      ctx.moveTo(cx2, cy2 - 9); ctx.lineTo(cx2, cy2 + 9);
      ctx.stroke();
      ctx.beginPath(); ctx.arc(cx2, cy2, 5, 0, 6.2832); ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(146,170,196,.35)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, S - 1, S - 1);
    ctx.restore();
    // where the mouse has to be for a click to land on this map
    if (player === kbPlayer()) mapRect = { x: VX + bx, y: VY + by, s: S };
  }
  function mapClick(sx, sy) {
    var r = mapRect;
    if (!r || state !== 'play') return false;
    if (sx < r.x || sx > r.x + r.s || sy < r.y || sy > r.y + r.s) return false;
    var kp = kbPlayer();
    pingAt(kp, (sx - r.x) / r.s * (MAP_W * TILE), (sy - r.y) / r.s * (MAP_H * TILE));
    return true;
  }""")

# ---- keys and buttons -----------------------------------------------------------
sub("""      else if (k === 'z') dropWeapon(kp);""",
"""      else if (k === 'z') dropWeapon(kp);
      else if (k === 'm') { kp.mapOpen = !kp.mapOpen; kp.mapCur = null; }
      else if (k === 'c') pingAt(kp, mouse.wx, mouse.wy);""")
sub("""      else if (k === 'escape') pause();
    } else if (k === 'escape' && state === 'paused')""",
"""      else if (k === 'escape') { if (kp.mapOpen) kp.mapOpen = false; else pause(); }
    } else if (k === 'escape' && state === 'paused')""")
sub("""      if (I.hit(PAD.pause)) { pause(); return; }""",
"""      if (I.hit(PAD.map)) { e.mapOpen = !e.mapOpen; e.mapCur = null; }
      if (I.hit(PAD.ping)) { if (e.mapOpen && e.mapCur) pingAt(e, e.mapCur.x, e.mapCur.y); else pingAhead(e); }
      if (I.hit(PAD.pause)) { pause(); return; }""")
# the stick drives the cursor while the map is up, so you read it standing still
sub("""    if (e.down) {
      e._spd = 0; e.prompt = null;""",
"""    if (e.mapOpen && I.pad && I.padOn) {
      var mspan = MAP_W * TILE, mtall = MAP_H * TILE;
      if (!e.mapCur) e.mapCur = { x: e.x, y: e.y };
      e.mapCur.x = clamp(e.mapCur.x + I.ax(0) * mspan * 0.4 * dt, 0, mspan);
      e.mapCur.y = clamp(e.mapCur.y + I.ax(1) * mtall * 0.4 * dt, 0, mtall);
      e._spd = 0; e.moving = false; e.prompt = null;
      if (e === player) promptItem = null;
      return;
    }
    if (e.down) {
      e._spd = 0; e.prompt = null;""")
# a click on either map drops a mark instead of firing
sub("""    } else {
      initAudio();
      mouse.down = true;
    }
    ev.preventDefault();""",
"""    } else {
      initAudio();
      var r2 = canvas.getBoundingClientRect();
      if (!mapClick(ev.clientX - r2.left, ev.clientY - r2.top)) mouse.down = true;
    }
    ev.preventDefault();""")

# ---- draw it --------------------------------------------------------------------
sub("""    renderAllies();
    renderObjectives();
    if (SET.minimap && !splitVs()) drawMinimap();""",
"""    renderAllies();
    renderPings();
    renderObjectives();
    if (player.mapOpen && !noOverlay) drawBigMap();
    else if (SET.minimap && !splitVs()) drawMinimap();""")

# ---- keep them ticking, and share them online -----------------------------------
sub("""    if (mode === 'tut') tutTick(dt);""", """    pingTick(dt);
    if (mode === 'tut') tutTick(dt);""")
sub("""    } else if (m.t === 'pchat') {""",
"""    } else if (m.t === 'pg') {
      addPing(g.ent, m.x, m.y);
    } else if (m.t === 'pchat') {""")
sub("""      x.f = flashes.filter(function (q) { return nearGuest(g, q.x, q.y); });""",
"""      x.pg = pings.filter(function (q) { return q.team === g.ent.team; });
      x.f = flashes.filter(function (q) { return nearGuest(g, q.x, q.y); });""")
sub("""    dmgMarks = m.dm || [];""", """    dmgMarks = m.dm || [];
    pings = m.pg || [];""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p64 applied')

# -*- coding: utf-8 -*-
"""Online: send far less, and let a guest move and aim without waiting for the host."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- send less -------------------------------------------------------------------
sub("""  function packEnt(e) {""",
"""  var NET_SEE = 1500;                       // how far a guest is told about
  function nearGuest(g, x, y) {
    var ge = g.ent;
    if (!ge) return true;
    var dx = x - ge.x, dy = y - ge.y;
    return dx * dx + dy * dy < NET_SEE * NET_SEE;
  }
  function packEnt(e) {""")
sub("""    return [e.id, e.x, e.y, e.ang, e.team, e.skin, bits, e.animT || 0, e.animFire || 0, e.swingT || 0,""",
    """    return [e.id, Math.round(e.x), Math.round(e.y), e.ang, e.team, e.skin, bits, e.animT || 0, e.animFire || 0, e.swingT || 0,""")
# the shared part loses the entity list; each guest gets their own slice
sub("""    var shared = netStr({
      t: 's', hold: state === 'paused',
      e: ents.map(packEnt),
      b: bullets.map(function (b) { return [b.x, b.y, b.vx, b.vy, b.owner]; }),
      f: flashes, im: impacts, sm: smokes,""",
"""    var shared = netStr({
      t: 's', hold: state === 'paused',""")
sub("""      h: [alive, score[0], score[1], round, roundClock, roundBreak, zombClock, matchTime, fieldN],
      ev: netEv
    });""",
"""      h: [alive, score[0], score[1], round, roundClock, roundBreak, zombClock, matchTime, fieldN],
      ev: netEv
    });
    var seSm = sectors, zSm = zone, pSm = plane;""")
sub("""      var x = { dm: dmgMarks.filter(function (m) { return m.who === g.ent.id; }) };""",
"""      // only what is near this guest: 48 people at 20 a second was a flood
      var x = { dm: dmgMarks.filter(function (m) { return m.who === g.ent.id; }) };
      x.e = [];
      for (var ei = 0; ei < ents.length; ei++) {
        var en = ents[ei];
        if (en === g.ent || en.team === g.ent.team || nearGuest(g, en.x, en.y)) x.e.push(packEnt(en));
      }
      x.b = [];
      for (var bi = 0; bi < bullets.length; bi++) {
        var bu = bullets[bi];
        if (nearGuest(g, bu.x, bu.y)) x.b.push([Math.round(bu.x), Math.round(bu.y), Math.round(bu.vx), Math.round(bu.vy), bu.owner]);
      }
      x.f = flashes.filter(function (q) { return nearGuest(g, q.x, q.y); });
      x.im = impacts.filter(function (q) { return nearGuest(g, q.x, q.y); });
      x.sm = smokes.filter(function (q) { return nearGuest(g, q.x, q.y); });
      x.n = nades.filter(function (q) { return nearGuest(g, q.x, q.y); }).map(function (gn) {
        return { x: Math.round(gn.x), y: Math.round(gn.y), spin: gn.spin, kind: gn.kind, fuse: gn.fuse, owner: gn.owner };
      });""")
# the guest fills in from its own slice, and hides anyone not mentioned
sub("""  function applySnap(m) {
    var i;
    for (i = 0; i < m.e.length; i++) netEnt(m.e[i]);""",
"""  function applySnap(m) {
    var i;
    var seen = {};
    for (i = 0; i < m.e.length; i++) { netEnt(m.e[i]); seen[m.e[i][0]] = 1; }
    for (i = 0; i < ents.length; i++) if (ents[i]) ents[i].hidden = !seen[i];""")
sub("""    bullets = m.b.map(function (b) { return { x: b[0], y: b[1], vx: b[2], vy: b[3], owner: b[4], life: 1 }; });""",
    """    bullets = (m.b || []).map(function (b) { return { x: b[0], y: b[1], vx: b[2], vy: b[3], owner: b[4], life: 1 }; });""")
# nobody out of the guest's slice is drawn or marked
sub("""      if (!en.alive || en === player || en.air === 'plane') continue;""",
    """      if (!en.alive || en.hidden || en === player || en.air === 'plane') continue;""")
sub("""      if (a === player || !a.alive || a.air === 'plane' || a.team !== player.team) continue;""",
    """      if (a === player || !a.alive || a.hidden || a.air === 'plane' || a.team !== player.team) continue;""")

# ---- a guest moves and aims on its own machine -----------------------------------
sub("""    if (Math.abs(a[1] - e.x) + Math.abs(a[2] - e.y) > 90) { e.x = a[1]; e.y = a[2]; }
    e.tx = a[1]; e.ty = a[2];
    e.ang = a[3];""",
"""    var mine = e.id === guestYou;
    if (Math.abs(a[1] - e.x) + Math.abs(a[2] - e.y) > 90) { e.x = a[1]; e.y = a[2]; }
    e.tx = a[1]; e.ty = a[2];
    // your own body: you steer it here and now; the host's word only nudges
    // it back if the two drift apart
    if (!mine) e.ang = a[3];""")
sub("""    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e || e.tx === undefined) continue;
      e.x += (e.tx - e.x) * kk; e.y += (e.ty - e.y) * kk;
    }""",
"""    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e || e.tx === undefined) continue;
      if (e === player) {
        // gentle correction only, so your own movement never stutters
        var ex = e.tx - e.x, ey = e.ty - e.y, ed = Math.sqrt(ex * ex + ey * ey);
        if (ed > 120) { e.x = e.tx; e.y = e.ty; }
        else if (ed > 3) { e.x += ex * Math.min(1, dt * 2.5); e.y += ey * Math.min(1, dt * 2.5); }
        continue;
      }
      e.x += (e.tx - e.x) * kk; e.y += (e.ty - e.y) * kk;
    }
    guestPredict(dt);""")
sub("""  function guestTick(dt) {""",
"""  // The guest walks and turns its own player straight away, exactly as the
  // host will a moment later. Without this every step waited on the network.
  function guestPredict(dt) {
    var e = player;
    if (!e || !e.alive || e.down || e.air || netGuestPaused) return;
    var mx = 0, my = 0;
    if (pad) { mx = padAxis(0); my = padAxis(1); }
    if (!mx && !my) {
      if (keys['a']) mx -= 1; if (keys['d']) mx += 1;
      if (keys['w']) my -= 1; if (keys['s']) my += 1;
    }
    var ml = Math.sqrt(mx * mx + my * my);
    if (ml > 1) { mx /= ml; my /= ml; }
    var sprint = (!!keys['shift'] || (pad && padDown(PAD.sprint))) && (mx || my);
    var base = curW(e) ? 168 : 190;
    var sp = sprint ? base * 1.45 : base;
    if (mx || my) { moveEnt(e, mx * sp * dt, my * sp * dt); e.moving = true; e._spd = sp; }
    else { e.moving = false; e._spd = 0; }
    // aim where this player is pointing, now
    if (pad) {
      var rx = pad.axes[2] || 0, ry = pad.axes[3] || 0, dz = SET.dead / 100;
      if (rx * rx + ry * ry >= (dz + 0.1) * (dz + 0.1)) e.ang = Math.atan2(ry, rx);
    }
    if (!padActive() && mouse.sx !== undefined) e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
  }

  function guestTick(dt) {""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p61 applied')

# -*- coding: utf-8 -*-
"""Battle royale starts in a plane: jump, steer the chute, land. Bigger BR map."""
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

# ---- a bigger island (STRIDE caps a map at 168 tiles) ---------------------
sub("""duel: 52, gun: 96, team: 118, war: 156, ctf: 126, sect: 122, zomb: 112, br: 130""",
    """duel: 52, gun: 96, team: 118, war: 156, ctf: 126, sect: 122, zomb: 112, br: 164""")

# ---- state ----------------------------------------------------------------
sub("""  var locals = [], splitOn = false, splitWant = false;""",
"""  var locals = [], splitOn = false, splitWant = false;
  // The drop plane: a straight run across the map. Everyone rides it at the
  // start of a battle royale and bails out somewhere along the way.
  var plane = null;
  var PLANE_SPEED = 360, GLIDE_SPEED = 235, CHUTE_TIME = 3.2;""")

# ---- boarding --------------------------------------------------------------
sub("""    spawnLoot(sp);
    elFeed.innerHTML = '';""",
"""    spawnLoot(sp);
    plane = null;
    if (mode === 'br') boardPlane();
    elFeed.innerHTML = '';""")

sub("""  function newRound() {""",
"""  function boardPlane() {
    // a line through the middle third of the map, edge to edge and beyond
    var a = Math.random() * Math.PI * 2;
    var dx = Math.cos(a), dy = Math.sin(a);
    var cx = WORLD_W / 2 + rr(-0.16, 0.16) * WORLD_W, cy = WORLD_H / 2 + rr(-0.16, 0.16) * WORLD_H;
    var half = Math.max(WORLD_W, WORLD_H) * 0.62;
    plane = { x0: cx - dx * half, y0: cy - dy * half, dx: dx, dy: dy, len: half * 2, t: 0, x: 0, y: 0 };
    plane.dur = plane.len / PLANE_SPEED;
    plane.x = plane.x0; plane.y = plane.y0;
    // Squads leave together; strangers spread along the whole run. A bot
    // flying with a person waits for them.
    var teamAt = {};
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      e.air = 'plane'; e.airT = 0;
      e.x = plane.x; e.y = plane.y;
      if (!e.bot) continue;
      if (teamAt[e.team] === undefined) teamAt[e.team] = rr(0.1, 0.9) * plane.dur;
      e.dropAt = teamAt[e.team] + rr(0, 0.4);
      e.follow = false;
      for (var j = 0; j < locals.length; j++) if (locals[j].team === e.team) e.follow = true;
    }
  }

  function jumpOut(e) {
    if (e.air !== 'plane' || !plane) return;
    e.air = 'chute'; e.airT = 0;
    e.x = clamp(plane.x, TILE * 2, WORLD_W - TILE * 2);
    e.y = clamp(plane.y, TILE * 2, WORLD_H - TILE * 2);
    e.ang = Math.atan2(plane.dy, plane.dx);
    if (e.bot) {
      // pick a spot off to one side of the line to glide for
      var side = rr(-1, 1) * GLIDE_SPEED * CHUTE_TIME * 0.95, ahead = rr(0, 0.5) * GLIDE_SPEED * CHUTE_TIME;
      e.landX = clamp(e.x - plane.dy * side + plane.dx * ahead, TILE * 3, WORLD_W - TILE * 3);
      e.landY = clamp(e.y + plane.dx * side + plane.dy * ahead, TILE * 3, WORLD_H - TILE * 3);
    }
    if (e.local) audioEmit(e.x, e.y, PICK_SND, e.id);
    // a partner bot bails out right behind you
    if (e.local) for (var i = 0; i < ents.length; i++) {
      var m = ents[i];
      if (m.bot && m.air === 'plane' && m.team === e.team) m.dropAt = Math.min(m.dropAt, plane.t + 0.35), m.follow = false;
    }
  }

  function land(e) {
    // down on the nearest open ground
    var tx = clamp(Math.floor(e.x / TILE), 1, MAP_W - 2), ty = clamp(Math.floor(e.y / TILE), 1, MAP_H - 2);
    var spot = null;
    for (var r = 0; r < 40 && !spot; r++) {
      for (var oy = -r; oy <= r && !spot; oy++) for (var ox = -r; ox <= r; ox++) {
        if (Math.max(Math.abs(ox), Math.abs(oy)) !== r) continue;
        var x = tx + ox, y = ty + oy;
        if (x < 1 || y < 1 || x >= MAP_W - 1 || y >= MAP_H - 1) continue;
        if (!isWall(x, y)) { spot = { x: x, y: y }; break; }
      }
    }
    if (spot) { e.x = spot.x * TILE + TILE / 2; e.y = spot.y * TILE + TILE / 2; }
    e.air = null; e.airT = 0;
    e.path = null; e.pathI = 0; e.repathT = 0; e.lootGoal = null; e.target = null;
    e.lastX = e.x; e.lastY = e.y; e.stuckT = 0;
    spark(e.x, e.y, 6, '210,190,150', 90);
  }

  function updateDrop(dt) {
    if (!plane) return;
    plane.t += dt;
    var k = Math.min(plane.t, plane.dur) * PLANE_SPEED;
    plane.x = plane.x0 + plane.dx * k; plane.y = plane.y0 + plane.dy * k;
    var inWorld = plane.x > TILE * 2 && plane.y > TILE * 2 && plane.x < WORLD_W - TILE * 2 && plane.y < WORLD_H - TILE * 2;
    var riders = 0;
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive) continue;
      if (e.air === 'plane') {
        e.x = plane.x; e.y = plane.y;
        var late = plane.t >= plane.dur * 0.93 || (!inWorld && plane.t > plane.dur * 0.5);
        if (inWorld && (late || (e.bot && !e.follow && plane.t >= e.dropAt))) jumpOut(e);
        else if (late && !inWorld) {
          // flew past the edge: tip them out over the last stretch of land
          plane.x = clamp(plane.x, TILE * 3, WORLD_W - TILE * 3);
          plane.y = clamp(plane.y, TILE * 3, WORLD_H - TILE * 3);
          jumpOut(e);
        }
        if (e.air === 'plane') riders++;
      } else if (e.air === 'chute') {
        e.airT += dt;
        if (e.bot) {
          var gx = e.landX - e.x, gy = e.landY - e.y, gl = Math.sqrt(gx * gx + gy * gy);
          if (gl > 4) {
            var st = Math.min(gl, GLIDE_SPEED * dt);
            e.x += gx / gl * st; e.y += gy / gl * st;
            e.ang = Math.atan2(gy, gx);
          }
        }
        if (e.airT >= CHUTE_TIME) land(e);
      }
    }
    plane.riders = riders;
    if (plane.t > plane.dur + 2 && !riders) {
      var still = false;
      for (i = 0; i < ents.length; i++) if (ents[i].air) { still = true; break; }
      if (!still) plane = null;
    }
  }

  // Your own hands in the air: jump from the plane, then steer the chute.
  function airControl(e, I, dt) {
    if (e.air === 'plane') {
      if (I.pad && I.hit(0)) jumpOut(e);
      if (I.kb && e.jumpReq) jumpOut(e);
      e.jumpReq = false;
      return;
    }
    var ix = 0, iy = 0;
    if (I.pad) { ix = I.ax(0); iy = I.ax(1); }
    if (!ix && !iy && I.kb) {
      if (keys['a']) ix -= 1; if (keys['d']) ix += 1;
      if (keys['w']) iy -= 1; if (keys['s']) iy += 1;
    }
    if (!ix && !iy && I.touch && sticks.move) {
      ix = sticks.move.x - sticks.move.ox; iy = sticks.move.y - sticks.move.oy;
      if (Math.abs(ix) + Math.abs(iy) < 8) ix = iy = 0;
    }
    var l = Math.sqrt(ix * ix + iy * iy);
    if (l > 0) {
      ix /= Math.max(1, l); iy /= Math.max(1, l);
      e.x = clamp(e.x + ix * GLIDE_SPEED * dt, TILE * 2, WORLD_W - TILE * 2);
      e.y = clamp(e.y + iy * GLIDE_SPEED * dt, TILE * 2, WORLD_H - TILE * 2);
      e.ang = Math.atan2(iy, ix);
    }
  }

  function newRound() {""")

# ---- update order: the plane first, then people ---------------------------
sub("""    pollPad();
    updateMouseWorld();
    for (i = 0; i < locals.length; i++) updateLocal(locals[i], dt);""",
"""    pollPad();
    updateMouseWorld();
    updateDrop(dt);
    for (i = 0; i < locals.length; i++) updateLocal(locals[i], dt);""")

sub("""      if (e.bot && e.alive && !e.down) botThink(e, dt);""",
    """      if (e.bot && e.alive && !e.down && !e.air) botThink(e, dt);""")

sub("""  function updateLocal(e, dt) {
    var I = inputFor(e);
    if (!e.alive) { if (I.pad && I.hit(9)) pause(); return; }""",
"""  function updateLocal(e, dt) {
    var I = inputFor(e);
    if (!e.alive) { if (I.pad && I.hit(9)) pause(); return; }
    if (e.air) {
      e._spd = 0; e.prompt = null;
      if (e === player) promptItem = null;
      if (I.pad && I.hit(9)) { pause(); return; }
      airControl(e, I, dt);
      return;
    }""")

# keyboard jump: E or space
sub("""      var kp = kbPlayer();
      if (k === 'r') startReload(kp);""",
"""      var kp = kbPlayer();
      if (kp.air === 'plane' && (k === 'e' || k === ' ')) kp.jumpReq = true;
      if (kp.air) { if (k === 'escape') pause(); if (k === 'm') { muted = !muted; } return; }
      if (k === 'r') startReload(kp);""")

# ---- nobody in the air can be seen, shot, blown up, hit or burned ---------
sub("""        if (o === e || !o.alive || !foes(e, o)) continue;
        var d = dist(e, o);
        // In a free-for-all every face is an enemy.""",
"""        if (o === e || !o.alive || o.air || !foes(e, o)) continue;
        var d = dist(e, o);
        // In a free-for-all every face is an enemy.""")
sub("""          if (!e.alive || e.id === b.owner) continue;""",
    """          if (!e.alive || e.air || e.id === b.owner) continue;""")
sub("""      if (o === e || !o.alive || !foes(e, o)) continue;
      var dx = o.x - e.x, dy = o.y - e.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d > 40) continue;""",
"""      if (o === e || !o.alive || o.air || !foes(e, o)) continue;
      var dx = o.x - e.x, dy = o.y - e.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d > 40) continue;""")
sub("""      var e = ents[i];
      if (!e.alive) continue;
      var d = Math.sqrt((e.x - g.x) * (e.x - g.x) + (e.y - g.y) * (e.y - g.y));""",
"""      var e = ents[i];
      if (!e.alive || e.air) continue;
      var d = Math.sqrt((e.x - g.x) * (e.x - g.x) + (e.y - g.y) * (e.y - g.y));""")
sub("""        if (m2 === e || !m2.alive || m2.down || m2.team !== e.team) continue;""",
    """        if (m2 === e || !m2.alive || m2.down || m2.air || m2.team !== e.team) continue;""")
sub("""          if (!want && player.alive && e.team === player.team && dist(e, player) > 230) {""",
    """          if (!want && player.alive && !player.air && e.team === player.team && dist(e, player) > 230) {""")

# the zone does not burn people still in the sky
a = s.index("  function updateZone(dt) {")
b = s.index("if (!e.alive) continue;", a)
s = s[:b] + "if (!e.alive || e.air) continue;" + s[b + len("if (!e.alive) continue;"):]

# ---- drawing ---------------------------------------------------------------
sub("""      if (!en.alive || en === player) continue;""",
    """      if (!en.alive || en === player || en.air === 'plane') continue;""")
sub("""    if (player.alive) drawUnit(player, curW(player) ? '#8ff0e4' : '#5d7288');

    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);""",
"""    if (player.alive && player.air !== 'plane') drawUnit(player, curW(player) ? '#8ff0e4' : '#5d7288');
    if (plane && plane.t < plane.dur + 2) drawPlane();

    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    renderDropHint();""")
sub("""  function drawUnit(e, color) {
    var spr = SPRITES[e === player ? 'player' : 'enemy'];""",
"""  function drawUnit(e, color) {
    if (e.air === 'chute') { drawChute(e); return; }
    var spr = SPRITES[e === player ? 'player' : 'enemy'];""")
sub("""      if (a === player || !a.alive || a.team !== player.team) continue;""",
    """      if (a === player || !a.alive || a.air === 'plane' || a.team !== player.team) continue;""")

sub("""  // ---- minimap: only ground you have actually seen ------------------------""",
"""  // The drop plane, top down: a chunky transport in the pack's colours.
  function drawPlane() {
    var a = Math.atan2(plane.dy, plane.dx);
    function body(ox, oy, fill, line) {
      ctx.save();
      ctx.translate(plane.x + ox, plane.y + oy);
      ctx.rotate(a);
      ctx.lineJoin = 'round';
      ctx.lineWidth = line ? 3.5 : 0;
      ctx.strokeStyle = '#0d0f12';
      ctx.fillStyle = fill;
      // wings
      ctx.beginPath();
      ctx.moveTo(8, 0); ctx.lineTo(-14, -78); ctx.lineTo(-34, -78); ctx.lineTo(-26, 0);
      ctx.lineTo(-34, 78); ctx.lineTo(-14, 78); ctx.closePath();
      ctx.fill(); if (line) ctx.stroke();
      // tail
      ctx.beginPath();
      ctx.moveTo(-60, 0); ctx.lineTo(-76, -28); ctx.lineTo(-86, -28); ctx.lineTo(-82, 0);
      ctx.lineTo(-86, 28); ctx.lineTo(-76, 28); ctx.closePath();
      ctx.fill(); if (line) ctx.stroke();
      // fuselage
      ctx.beginPath();
      ctx.moveTo(62, 0); ctx.quadraticCurveTo(58, -14, 30, -14); ctx.lineTo(-80, -9);
      ctx.lineTo(-80, 9); ctx.lineTo(30, 14); ctx.quadraticCurveTo(58, 14, 62, 0);
      ctx.fill(); if (line) ctx.stroke();
      if (line) {
        ctx.fillStyle = '#f2bd1d';
        ctx.fillRect(-40, -3, 60, 6);                     // gold stripe
        ctx.fillStyle = '#9fd3e8';
        ctx.beginPath(); ctx.ellipse(46, 0, 7, 9, 0, 0, 6.2832); ctx.fill(); ctx.stroke();
        // engines
        ctx.fillStyle = '#1d2d3b';
        ctx.fillRect(-12, -52, 22, 11); ctx.strokeRect(-12, -52, 22, 11);
        ctx.fillRect(-12, 41, 22, 11); ctx.strokeRect(-12, 41, 22, 11);
      }
      ctx.restore();
    }
    body(46, 58, 'rgba(0,0,0,.28)', false);                // shadow on the ground
    body(0, 0, '#2e4559', true);
  }

  function drawChute(e) {
    var k = clamp(e.airT / CHUTE_TIME, 0, 1);              // 0 just out, 1 on the ground
    var hgt = (1 - k) * 34;
    // shadow shrinks toward you as you come down
    ctx.fillStyle = 'rgba(0,0,0,.3)';
    ctx.beginPath(); ctx.ellipse(e.x + hgt * 0.8, e.y + hgt, 10, 7, 0, 0, 6.2832); ctx.fill();
    var R = 24 + (1 - k) * 8;
    var tint = e.team === player.team ? '#f2bd1d' : '#e0643a';
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(e.ang);
    ctx.lineWidth = 2.5; ctx.strokeStyle = '#0d0f12';
    for (var i = 0; i < 6; i++) {                          // panels
      ctx.fillStyle = i % 2 ? tint : '#f1e7d0';
      ctx.beginPath(); ctx.moveTo(0, 0);
      ctx.arc(0, 0, R, i * Math.PI / 3, (i + 1) * Math.PI / 3);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
    ctx.fillStyle = '#0d0f12';
    ctx.beginPath(); ctx.arc(0, 0, 4, 0, 6.2832); ctx.fill();
    ctx.restore();
  }

  function renderDropHint() {
    if (!player.alive || !player.air) return;
    var txt, sub2 = null;
    if (player.air === 'plane') {
      txt = promptKey('SPACE', 'A') + '  JUMP';
      var left = Math.max(0, plane.dur * 0.93 - plane.t);
      sub2 = 'THE PLANE DROPS EVERYONE IN ' + Math.ceil(left) + 's';
    } else {
      txt = 'STEER YOUR LANDING';
      sub2 = promptKey('WASD', 'LEFT STICK');
    }
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '400 18px "Russo One", "Chakra Petch", sans-serif';
    var tw = ctx.measureText(txt).width + 40, bx = cw / 2 - tw / 2, by = ch * 0.7;
    ctx.fillStyle = '#f2bd1d'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(bx, by, tw, 36); ctx.strokeRect(bx, by, tw, 36);
    ctx.fillStyle = '#0d0f12';
    ctx.fillText(txt, cw / 2, by + 19);
    ctx.font = '500 10px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#f1e7d0';
    ctx.fillText(sub2, cw / 2, by + 52);
    ctx.restore();
  }

  // ---- minimap: only ground you have actually seen ------------------------""")

# from the plane you can see the whole island on the map, and the route
sub("""        if (!explored[gi]) { d[o4 + 3] = 0; continue; }""",
    """        if (!explored[gi] && !miniReveal) { d[o4 + 3] = 0; continue; }""")
sub("""  var mini = null, miniAge = 0;""", """  var mini = null, miniAge = 0, miniReveal = false;""")
sub("""  function drawMinimap() {
    if (!mini) mini = document.createElement('canvas');""",
"""  function drawMinimap() {
    if (!mini) mini = document.createElement('canvas');
    var rev = false;
    for (var lq = 0; lq < locals.length; lq++) if (locals[lq].air) rev = true;
    if (rev !== miniReveal) { miniReveal = rev; miniAge = 0; }""")
sub("""    if (zone) {
      ctx.strokeStyle = 'rgba(255,77,141,.75)';
      ctx.lineWidth = 1.2;""",
"""    if (plane && miniReveal) {
      ctx.strokeStyle = 'rgba(242,189,29,.8)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(mx(plane.x0), my(plane.y0));
      ctx.lineTo(mx(plane.x0 + plane.dx * plane.len), my(plane.y0 + plane.dy * plane.len));
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#f2bd1d';
      ctx.beginPath(); ctx.arc(mx(plane.x), my(plane.y), 3.2, 0, 6.2832); ctx.fill();
    }
    if (zone) {
      ctx.strokeStyle = 'rgba(255,77,141,.75)';
      ctx.lineWidth = 1.2;""")

assert s != o
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('p46 applied')

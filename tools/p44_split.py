# -*- coding: utf-8 -*-
"""Split screen: two local players, each with a device, a camera, a view and a HUD.

Supersedes the unapplied p40_split.py.
"""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b, n=1):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, n)

# ================================================================ state =====
sub("""  var player = null, zone = null;""",
"""  var player = null, zone = null;
  // Everyone playing on this machine. One normally; two in split screen, where
  // each owns a device and a slice of the screen.
  var locals = [], splitOn = false, splitWant = false;
  var VX = 0, VY = 0, VW = 0, VH = 0;       // the viewport being drawn into
  function anyLocalAlive() {
    for (var i = 0; i < locals.length; i++) if (locals[i].alive) return true;
    return false;
  }
  function kbPlayer() {
    for (var i = 0; i < locals.length; i++) if (locals[i].ctl && locals[i].ctl.kb) return locals[i];
    return player;
  }
  function nearestLocal(x, y) {
    var best = player, bd = 1e18;
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i], d = (L.x - x) * (L.x - x) + (L.y - y) * (L.y - y);
      if (d < bd) { bd = d; best = L; }
    }
    return best;
  }
  // Which pads to hand out: two pads -> one each; one pad -> P1 keeps the
  // keyboard and mouse, P2 takes the pad. No pads, no split.
  function padIndices() {
    var l = navigator.getGamepads ? navigator.getGamepads() : null, out = [];
    if (l) for (var i = 0; i < l.length; i++) if (l[i] && l[i].connected) out.push(i);
    return out;
  }
  function splitControls() {
    var p = padIndices();
    if (p.length >= 2) return { p1: p[0], p2: p[1] };
    if (p.length === 1) return { p1: -1, p2: p[0] };
    return null;
  }""")

# ================================================================ pads ======
sub("""  var pad = null, padPrev = {}, padSeen = false, padLast = -1e9;""",
"""  function getPad(i) {
    var l = navigator.getGamepads ? navigator.getGamepads() : null;
    return (i >= 0 && l && l[i] && l[i].connected) ? l[i] : null;
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
  // Is this player on a pad right now? Drives the button labels and the aim dot.
  function usingPad(e) {
    var c = e && e.ctl;
    if (!c || c.any) return padActive();
    if (c.pad < 0) return false;
    if (!c.kb) return true;
    return (performance.now() - (e.padLast || -1e9)) < 10000;
  }

  var pad = null, padPrev = {}, padSeen = false, padLast = -1e9;""")

sub("""  function promptKey(keyLabel, padLabel) { return padActive() ? padLabel : keyLabel; }""",
    """  function promptKey(keyLabel, padLabel) { return usingPad(player) ? padLabel : keyLabel; }""")

# ================================================================ match =====
sub("""    player = makeEnt(sp[0], true, 'YOU');
    ents.push(player);
    for (var i = 1; i < fieldN; i++) ents.push(makeEnt(sp[i % sp.length], false, NAMES[i - 1]));""",
"""    player = makeEnt(sp[0], true, 'YOU');
    player.local = true; player.ctl = { any: true, kb: true }; player.cam = cam;
    ents.push(player);
    locals = [player]; splitOn = false;
    var sc = splitWant ? splitControls() : null;
    if (splitWant && !sc) feed('split screen needs a <b>controller</b> for player 2', true);
    if (sc) {
      var p2 = makeEnt(sp[1 % sp.length], true, 'P2');
      p2.local = true; p2.ctl = { pad: sc.p2, kb: false }; p2.cam = { x: 0, y: 0 }; p2.padPrev = {};
      player.name = 'P1'; player.ctl = { pad: sc.p1, kb: true }; player.padPrev = {};
      ents.push(p2); locals.push(p2);
      splitOn = true;
    }
    for (var i = ents.length; i < fieldN; i++) ents.push(makeEnt(sp[i % sp.length], false, NAMES[i - 1]));""")

sub("""        var patient = 1 + rnd(Math.max(1, fieldN - 1));   // never the player""",
    """        var patient = locals.length + rnd(Math.max(1, fieldN - locals.length));   // never a local player""")

sub("""    player.skin = WALLET.skin;
    charCache = {};""",
"""    player.skin = WALLET.skin;
    if (splitOn && !MODE.teams && !MODE.zombies && locals[1].skin === player.skin) locals[1].skin = (player.skin + 5) % 16;
    elHud.classList.toggle('split', splitOn);
    charCache = {};""")

sub("""    if (e === player) {
      cam.x = e.x; cam.y = e.y;
      mouse.wx = e.x + Math.cos(e.ang) * 100;
      mouse.wy = e.y + Math.sin(e.ang) * 100;
    }""",
"""    if (e.local && e.cam) { e.cam.x = e.x; e.cam.y = e.y; }
    if (e === player) {
      cam.x = e.x; cam.y = e.y;
      mouse.wx = e.x + Math.cos(e.ang) * 100;
      mouse.wy = e.y + Math.sin(e.ang) * 100;
    }""")

# ================================================================ input =====
a = s.index("  function updatePlayer(dt) {")
b = s.index("  function playerPickup() {")
s = s[:a] + r"""  // One set of controls, read from whatever device this player owns. A lone
  // player takes whichever is in use; in split screen each has their own.
  function inputFor(e) {
    var c = e.ctl || { any: true, kb: true };
    if (c.any) {
      return { any: true, pad: pad, hit: padHit, down: padDown, ax: padAxis,
               kb: true, touch: true, padOn: padActive() };
    }
    var g = getPad(c.pad);
    if (!e.padPrev) e.padPrev = {};
    if (g) {
      var busy = false, j;
      for (j = 0; j < g.buttons.length; j++) if (g.buttons[j] && g.buttons[j].pressed) { busy = true; break; }
      if (!busy) for (j = 0; j < g.axes.length; j++) if (Math.abs(g.axes[j]) > 0.45) { busy = true; break; }
      if (busy) e.padLast = performance.now();
    }
    return {
      any: false, pad: g,
      hit: function (i) { return hitOf(g, e.padPrev, i); },
      down: function (i) { return downOf(g, i); },
      ax: function (i) { return axOf(g, i); },
      kb: !!c.kb, touch: false, padOn: usingPad(e)
    };
  }

  function updateLocal(e, dt) {
    var I = inputFor(e);
    if (!e.alive) { if (I.pad && I.hit(9)) pause(); return; }
    if (e.down) {
      e._spd = 0; e.prompt = null;
      if (e === player) promptItem = null;
      if (I.pad && I.hit(1)) { e.hp = 0; kill(e, -1); }        // B gives up
      if (I.pad && I.hit(9)) pause();
      return;
    }
    autoPickup(e);

    e.prompt = null;
    var bestD = 26 * 26;
    for (var i = 0; i < loot.length; i++) {
      var it = loot[i];
      if (it.type !== 'gun') continue;
      var ddx = it.x - e.x, ddy = it.y - e.y, d2 = ddx * ddx + ddy * ddy;
      if (d2 < bestD) { bestD = d2; e.prompt = it; }
    }
    if (e === player) promptItem = e.prompt;

    if (e.useT > 0) {
      e.useT -= dt;
      if (e.useT <= 0) e.hp = Math.min(100, e.hp + 45);
    }

    var ix = 0, iy = 0;
    var padMove = false;
    if (I.pad) {
      var lx = I.ax(0), ly = I.ax(1);
      if (lx || ly) {
        var ll = Math.sqrt(lx * lx + ly * ly);
        ix = lx / (ll > 1 ? ll : 1); iy = ly / (ll > 1 ? ll : 1);
        padMove = true;
      }
      if (I.hit(0)) playerPickup(e);
      if (I.hit(1)) melee(e);
      if (I.hit(2)) startReload(e);
      if (I.hit(3)) useMed(e);
      if (I.hit(14) || I.hit(15)) swapSlot(undefined, e);
      if (I.hit(5)) throwNade(e, 'smoke');
      if (I.hit(6)) throwNade(e, 'frag');
      if (I.hit(12)) useMed(e);
      if (I.hit(9)) { pause(); return; }
    }
    if (!padMove && I.touch && sticks.move) {
      var sdx = sticks.move.x - sticks.move.ox, sdy = sticks.move.y - sticks.move.oy;
      var sl = Math.sqrt(sdx * sdx + sdy * sdy);
      if (sl > 8) { ix = sdx / sl; iy = sdy / sl; }
    } else if (!padMove && I.kb) {
      if (keys['a']) ix -= 1; if (keys['d']) ix += 1;
      if (keys['w']) iy -= 1; if (keys['s']) iy += 1;
      var l = Math.sqrt(ix * ix + iy * iy);
      if (l > 0) { ix /= l; iy /= l; }
    }
    var sprinting = ((I.kb && !!keys['shift']) || (!!I.pad && I.down(4))) && (ix || iy);
    var base = curW(e) ? 168 : (MODE.zombies && e.team === 1 ? 168 : 190);
    var speed = sprinting ? base * 1.45 : base;
    e._spd = (ix || iy) ? speed : 0;
    if (ix || iy) { moveEnt(e, ix * speed * dt, iy * speed * dt); footstep(e, dt, sprinting); }
    else e.stepT = 0.14;

    // Face the right stick if it is pushed; otherwise where you are walking on
    // a pad; otherwise the cursor. Never left pointing at nothing.
    var rx = I.pad ? I.ax(2) : 0, ry = I.pad ? I.ax(3) : 0;
    if (rx || ry) {
      e.ang = aimAssist(e, Math.atan2(ry, rx));
    } else if (I.touch && sticks.aim) {
      var adx = sticks.aim.x - sticks.aim.ox, ady = sticks.aim.y - sticks.aim.oy;
      if (Math.sqrt(adx * adx + ady * ady) > 10) e.ang = Math.atan2(ady, adx);
    } else if (I.padOn && (ix || iy)) {
      e.ang = Math.atan2(iy, ix);
    } else if (I.kb && (I.any || !I.padOn)) {
      e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
    }

    e.fireT -= dt;
    if (e.reloadT > 0) {
      e.reloadT -= dt;
      if (e.reloadT <= 0) finishReload(e);
    }
    var firing = (I.kb && mouse.down) || (!!I.pad && I.down(7)) ||
      (I.touch && sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
    if (firing) {
      var cw2 = curW(e), cs2 = curSlot(e);
      if (!cw2 || (cs2.ammo <= 0 && e.reserve <= 0)) melee(e);   // nothing to shoot with
      else if (cs2.ammo <= 0) startReload(e);
      else fire(e);
    }
  }

""" + s[b:]

sub("""  function playerPickup() {
    if (!promptItem) return;
    var idx = loot.indexOf(promptItem);
    if (idx >= 0) takeGun(player, promptItem, idx);
    promptItem = null;
  }
  function swapSlot(n) {
    if (n === undefined) n = player.slot === 0 ? 1 : 0;
    if (!player.slots[n] || n === player.slot) return;
    player.slot = n; player.reloadT = 0;
  }""",
"""  function playerPickup(e) {
    e = e || kbPlayer();
    var it = e.prompt;
    if (!it) return;
    var idx = loot.indexOf(it);
    if (idx >= 0) takeGun(e, it, idx);
    e.prompt = null;
    if (e === player) promptItem = null;
  }
  function swapSlot(n, e) {
    e = e || kbPlayer();
    if (n === undefined) n = e.slot === 0 ? 1 : 0;
    if (!e.slots[n] || n === e.slot) return;
    e.slot = n; e.reloadT = 0;
  }""")

sub("""    updatePlayer(dt);
    for (i = 0; i < ents.length; i++) {""",
"""    pollPad();
    updateMouseWorld();
    for (i = 0; i < locals.length; i++) updateLocal(locals[i], dt);
    if (state !== 'play') return;
    for (i = 0; i < ents.length; i++) {""")

sub("""    if (state === 'play') {
      if (k === 'r') startReload(player);
      else if (k === 'e') playerPickup();
      else if (k === 'q') swapSlot();
      else if (k === '1') swapSlot(0);
      else if (k === '2') swapSlot(1);
      else if (k === 'f') useMed(player);
      else if (k === 'g') throwNade(player, 'frag');
      else if (k === 'h') throwNade(player, 'smoke');
      else if (k === 'v') melee(player);
      else if (k === 'x' && player.down) { player.hp = 0; kill(player, -1); }""",
"""    if (state === 'play') {
      var kp = kbPlayer();
      if (k === 'r') startReload(kp);
      else if (k === 'e') playerPickup(kp);
      else if (k === 'q') swapSlot(undefined, kp);
      else if (k === '1') swapSlot(0, kp);
      else if (k === '2') swapSlot(1, kp);
      else if (k === 'f') useMed(kp);
      else if (k === 'g') throwNade(kp, 'frag');
      else if (k === 'h') throwNade(kp, 'smoke');
      else if (k === 'v') melee(kp);
      else if (k === 'x' && kp.down) { kp.hp = 0; kill(kp, -1); }""")

# mouse -> world through whichever view the mouse player is in
sub("""  function screenToWorld(sx, sy) {
    mouse.wx = (sx - cw / 2) / zoom + cam.x;
    mouse.wy = (sy - ch / 2) / zoom + cam.y;
  }""",
"""  function screenToWorld(sx, sy) {
    mouse.sx = sx; mouse.sy = sy;
    updateMouseWorld();
  }
  // The cursor has to be re-projected every frame, not only when it moves:
  // the camera slides underneath a still mouse.
  function updateMouseWorld() {
    if (mouse.sx === undefined || !player) return;
    var L = kbPlayer(), c = L.cam || cam;
    var vx = L.vw ? L.vx : 0, vy = L.vh ? L.vy : 0, vw = L.vw || cw, vh = L.vh || ch, z = L.zoom || zoom;
    mouse.wx = (mouse.sx - vx - vw / 2) / z + c.x;
    mouse.wy = (mouse.sy - vy - vh / 2) / z + c.y;
  }""")

# ================================================================ camera ====
sub("""    var tx = player.x, ty = player.y;
    if (!touchMode) {
      tx += clamp(mouse.wx - player.x, -110, 110) * 0.2;
      ty += clamp(mouse.wy - player.y, -110, 110) * 0.2;
    }
    var lerp = 1 - Math.pow(0.0001, dt);
    cam.x += (tx - cam.x) * lerp;
    cam.y += (ty - cam.y) * lerp;""",
"""    var lerp = 1 - Math.pow(0.0001, dt);
    for (var li = 0; li < locals.length; li++) {
      var L = locals[li], lc = L.cam || cam;
      var tx = L.x, ty = L.y;
      // the mouse leads the camera for whoever is on it
      if (!touchMode && L.ctl && L.ctl.kb && (L.ctl.any || !usingPad(L))) {
        tx += clamp(mouse.wx - L.x, -110, 110) * 0.2;
        ty += clamp(mouse.wy - L.y, -110, 110) * 0.2;
      }
      lc.x += (tx - lc.x) * lerp;
      lc.y += (ty - lc.y) * lerp;
    }""")

# ================================================================ render ====
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
    if (!player) return;

    if (!splitOn) {
      VX = 0; VY = 0; VW = cw; VH = ch;
      player.vx = 0; player.vy = 0; player.vw = cw; player.vh = ch; player.zoom = zoom;
      renderScene();
      return;
    }

    // Each local player gets a slice: side by side on a wide screen, stacked
    // on a tall one. Everything below draws as if its slice were the screen.
    var fullW = cw, fullH = ch, z0 = zoom, p0 = player, cam0 = cam, pr0 = promptItem;
    var side = fullW >= fullH;
    for (var pi = 0; pi < locals.length; pi++) {
      var L = locals[pi];
      if (side) { VX = Math.round(pi * fullW / 2); VY = 0; VW = Math.round(fullW / 2); VH = fullH; }
      else { VX = 0; VY = Math.round(pi * fullH / 2); VW = fullW; VH = Math.round(fullH / 2); }
      L.vx = VX; L.vy = VY; L.vw = VW; L.vh = VH;
      L.zoom = Math.max(0.5, Math.min(2.4, Math.min(VW, VH) / (VIEW_BASE * 2 + 60)));
      cw = VW; ch = VH; zoom = L.zoom; player = L; cam = L.cam; promptItem = L.prompt;
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.beginPath(); ctx.rect(VX, VY, VW, VH); ctx.clip();
      renderScene();
      drawSplitHud(L);
      ctx.restore();
    }
    cw = fullW; ch = fullH; zoom = z0; player = p0; cam = cam0; promptItem = pr0;
    VX = 0; VY = 0; VW = cw; VH = ch;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#0d0f12';
    if (side) ctx.fillRect(Math.round(cw / 2) - 2, 0, 4, ch);
    else ctx.fillRect(0, Math.round(ch / 2) - 2, cw, 4);
    ctx.fillStyle = 'rgba(242,189,29,.55)';
    if (side) ctx.fillRect(Math.round(cw / 2) - 0.5, 0, 1, ch);
    else ctx.fillRect(0, Math.round(ch / 2) - 0.5, cw, 1);
  }

  // Your own numbers, drawn into your own slice of a split screen.
  function drawSplitHud(L) {
    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    ctx.save();
    ctx.textBaseline = 'alphabetic';
    var pad2 = 14, by = VH - pad2;
    // who is who, top right
    ctx.font = '400 15px "Russo One", "Chakra Petch", sans-serif';
    ctx.textAlign = 'right';
    ctx.fillStyle = '#0d0f12';
    ctx.fillText(L.name, VW - pad2 + 2, 30 + 2);
    ctx.fillStyle = L === locals[0] ? '#f2bd1d' : '#7ce7d8';
    ctx.fillText(L.name, VW - pad2, 30);
    ctx.font = '500 9px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    ctx.fillText(L.ctl && L.ctl.pad >= 0 && !L.ctl.kb ? 'CONTROLLER' : (usingPad(L) ? 'CONTROLLER' : 'KEYBOARD'), VW - pad2, 44);

    if (!L.alive) {
      ctx.textAlign = 'center';
      ctx.font = '400 22px "Russo One", "Chakra Petch", sans-serif';
      ctx.fillStyle = '#f1e7d0';
      var msg = L.respawnT > 0 ? 'RESPAWNING ' + Math.ceil(L.respawnT) : 'OUT';
      ctx.fillText(msg, VW / 2, VH / 2);
      ctx.restore();
      return;
    }

    // health, bottom left
    var hp = Math.max(0, Math.round(L.hp)), bw = Math.min(170, VW * 0.34);
    ctx.fillStyle = 'rgba(44,61,82,.7)';
    ctx.fillRect(pad2, by - 34, bw, 5);
    ctx.fillStyle = hp <= 35 ? '#ff4d8d' : '#7ce7d8';
    ctx.fillRect(pad2, by - 34, bw * hp / 100, 5);
    ctx.textAlign = 'left';
    ctx.font = '700 20px "Chakra Petch", sans-serif';
    ctx.fillStyle = '#c6d4e3';
    ctx.fillText(String(hp), pad2, by - 10);
    ctx.font = '500 9px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    var kit = 'STIM ' + L.meds + '  FRAG ' + L.nades + '  SMOKE ' + L.smokes;
    ctx.fillText(kit, pad2, by + 2);

    // weapon, bottom right
    var w = curW(L), sl = curSlot(L);
    ctx.textAlign = 'right';
    ctx.font = '500 9px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    ctx.fillText(w ? w.name : 'UNARMED', VW - pad2, by - 30);
    ctx.font = '700 24px "Chakra Petch", sans-serif';
    ctx.fillStyle = w && sl.ammo <= 0 ? '#ff4d8d' : '#c6d4e3';
    var res = L.reserve >= 9000 ? '\\u221e' : String(L.reserve);
    var ammoTxt = w ? String(sl.ammo) : '--';
    ctx.fillText(ammoTxt, VW - pad2 - 40, by - 6);
    ctx.font = '500 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    ctx.fillText('/ ' + res, VW - pad2, by - 6);
    if (w && (L.reloadT > 0 || L.useT > 0)) {
      var k = L.reloadT > 0 ? 1 - L.reloadT / w.reload : 1 - L.useT / 1.6;
      ctx.fillStyle = 'rgba(44,61,82,.7)';
      ctx.fillRect(VW - pad2 - 78, by + 1, 78, 3);
      ctx.fillStyle = '#ffc95e';
      ctx.fillRect(VW - pad2 - 78, by + 1, 78 * clamp(k, 0, 1), 3);
    }
    ctx.restore();
  }

  function renderScene() {
    var halfW = cw / (2 * zoom), halfH = ch / (2 * zoom);""")

sub("""    if (player.alive) drawUnit(player, curW(player) ? '#8ff0e4' : '#5d7288');

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);""",
"""    if (player.alive) drawUnit(player, curW(player) ? '#8ff0e4' : '#5d7288');

    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);""")

sub("""    if (touchMode) renderSticks();
  }""", """    if (touchMode && !splitOn) renderSticks();
  }""")

sub("""    ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom,
      dpr * (cw / 2 - cam.x * zoom + sx), dpr * (ch / 2 - cam.y * zoom + sy));""",
"""    ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom,
      dpr * (VX + cw / 2 - cam.x * zoom + sx), dpr * (VY + ch / 2 - cam.y * zoom + sy));""")

# the aim dot and cursor follow each player's own device
sub("""    var on = padActive();
    if (cursorHidden !== on) {
      cursorHidden = on;
      canvas.style.cursor = on ? 'none' : 'crosshair';
    }""",
"""    var on = usingPad(player);
    var hideC = splitOn ? usingPad(kbPlayer()) : on;
    if (cursorHidden !== hideC) {
      cursorHidden = hideC;
      canvas.style.cursor = hideC ? 'none' : 'crosshair';
    }""")

# damage marks belong to whoever took the hit
sub("""    if (e === player) { shake = Math.min(shake + 3, 9); dmgMarks.push({ ang: ang, t: 1.1 }); }""",
    """    if (e === player) shake = Math.min(shake + 3, 9);
    if (e.local) dmgMarks.push({ ang: ang, t: 1.1, who: e.id });""")
sub("""        else if (e === player && Math.random() < dt * 3) dmgMarks.push({ ang: Math.atan2(dy, dx), t: 0.5 });""",
    """        else if (e.local && Math.random() < dt * 3) dmgMarks.push({ ang: Math.atan2(dy, dx), t: 0.5, who: e.id });""")
sub("""      var m = dmgMarks[i];
      var a = clamp(m.t / 1.1, 0, 1) * 0.6;""",
"""      var m = dmgMarks[i];
      if (m.who !== undefined && m.who !== player.id) continue;
      var a = clamp(m.t / 1.1, 0, 1) * 0.6;""")

# ================================================================ audio =====
sub("""    if (!actx || muted || !player) return;
    if (!def.aud && !def.sample) return;
    var dx = x - player.x, dy = y - player.y;
    var d = Math.sqrt(dx * dx + dy * dy);
    if (d > def.maxR) return;
    var mine = owner === player.id;""",
"""    if (!actx || muted || !player) return;
    if (!def.aud && !def.sample) return;
    // heard from your own spot if it is yours, else from the nearer player
    var oe = owner >= 0 ? ents[owner] : null;
    var lis = (oe && oe.local) ? oe : nearestLocal(x, y);
    var dx = x - lis.x, dy = y - lis.y;
    var d = Math.sqrt(dx * dx + dy * dy);
    if (d > def.maxR) return;
    var mine = !!(oe && oe.local);""")
sub("""    if (!mine && d > 4 && !lineClear(player.x, player.y, x, y)) muffle *= 0.4;""",
    """    if (!mine && d > 4 && !lineClear(lis.x, lis.y, x, y)) muffle *= 0.4;""")

# ================================================================ stats =====
sub("""            if (b.owner === player.id) hits++;""",
    """            if (ents[b.owner] && ents[b.owner].local) hits++;""")
sub("""    if (e === player) { shots++; shake""", """    if (e.local) shots++;
    if (e === player) { shake""")

# ================================================================ endings ===
sub("""    if (killer === player) { kills++; feed('<b>YOU</b> eliminated ' + e.name, true); }
    else if (e === player) { feed('<b>' + kn + '</b> eliminated YOU', true); }""",
"""    if (killer && killer.local && killer !== e) {
      kills++;
      feed('<b>' + (splitOn ? killer.name : 'YOU') + '</b> eliminated ' + e.name, true);
    }
    else if (e.local) { feed('<b>' + kn + '</b> eliminated ' + (splitOn ? e.name : 'YOU'), true); }""")

sub("""          finish(killer === player, killer === player
            ? 'You took it ' + score[0] + '\\u2013' + score[1] + '.'""",
"""          finish(!!killer.local, killer.local
            ? (splitOn ? killer.name + ' took it ' + score[killer.id] + '\\u2013' + score[e.id] + '.'
                       : 'You took it ' + score[0] + '\\u2013' + score[1] + '.')""")
sub("""          finish(killer === player, killer === player
            ? 'You ran the whole ladder and closed it out with the rifle.'""",
"""          finish(!!killer.local, killer.local
            ? (splitOn ? killer.name + ' ran the whole ladder first.' : 'You ran the whole ladder and closed it out with the rifle.')""")
sub("""        if (killer === player) feed('promoted to <b>' + WEAPONS[LADDER[killer.level]].name + '</b>', true);""",
    """        if (killer.local) feed((splitOn ? '<b>' + killer.name + '</b> ' : '') + 'promoted to <b>' + WEAPONS[LADDER[killer.level]].name + '</b>', true);""")

sub("""    if (e === player) {
      finish(false, killer && killer !== e
        ? kn + ' put you down at ' + Math.round(dist(e, killer)) + ' units.'
        : 'The zone closed over you.', alive + 1);
    } else if (player.alive) {
      var live = {}, nTeams = 0;
      for (var q = 0; q < ents.length; q++) {
        if (ents[q].alive && !live[ents[q].team]) { live[ents[q].team] = 1; nTeams++; }
      }
      if (nTeams === 1) {
        finish(true, squad > 1 ? 'Your squad is the last one moving.'
                               : 'Last one standing. Nothing left to hear.', 1);
      }
    }""",
"""    if (e.local && !anyLocalAlive()) {
      finish(false, killer && killer !== e
        ? kn + ' put ' + (splitOn ? e.name : 'you') + ' down at ' + Math.round(dist(e, killer)) + ' units.'
        : 'The zone closed over ' + (splitOn ? e.name : 'you') + '.', alive + 1);
    } else if (anyLocalAlive()) {
      var live = {}, nTeams = 0;
      for (var q = 0; q < ents.length; q++) {
        if (ents[q].alive && !live[ents[q].team]) { live[ents[q].team] = 1; nTeams++; }
      }
      if (nTeams === 1) {
        var champ = null;
        for (var q2 = 0; q2 < locals.length; q2++) if (locals[q2].alive) champ = locals[q2];
        finish(true, squad > 1 ? 'Your squad is the last one moving.'
                   : (splitOn ? champ.name + ' is the last one standing.' : 'Last one standing. Nothing left to hear.'), 1);
      }
    }""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ================================================================ menu ======
h = io.open(H, encoding='utf-8').read(); ho = h
def hsub(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)
hsub("""        <div class="pick">
          <p>LIGHTING</p>""",
"""        <div class="pick">
          <p>PLAYERS</p>
          <div class="row" id="playersRow">
            <button type="button" data-n="1" aria-pressed="true">1 PLAYER</button>
            <button type="button" data-n="2" aria-pressed="false">2P SPLIT SCREEN</button>
          </div>
        </div>

        <div class="pick">
          <p>LIGHTING</p>""")
hsub(""".hud-bot{position:absolute;""", """.hud.split .hud-bot{display:none}
.hud-bot{position:absolute;""")
io.open(H, 'w', encoding='utf-8', newline='').write(h)

print('p44 applied')

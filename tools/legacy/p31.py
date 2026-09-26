# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== settings ===============
sub("""  function skinPrice(i) { return i === BASE_SKIN ? 0 : (i >= 12 ? 500 : 200); }""",
"""  function skinPrice(i) { return i === BASE_SKIN ? 0 : (i >= 12 ? 500 : 200); }

  var SET = { vol: 66, dead: 18, assist: true, shake: true, minimap: true };
  function loadSettings() {
    try {
      var raw = localStorage.getItem('earshot.settings');
      if (raw) {
        var v = JSON.parse(raw);
        if (v) for (var k in SET) if (v[k] !== undefined) SET[k] = v[k];
      }
    } catch (err) { /* blocked storage: keep the defaults */ }
  }
  function saveSettings() {
    try { localStorage.setItem('earshot.settings', JSON.stringify(SET)); } catch (err) {}
    if (master) master.gain.value = SET.vol / 100;
  }""")

sub("""      master.gain.value = 0.66;""", """      master.gain.value = SET.vol / 100;""")

sub("""    var sx = shake ? rr(-shake, shake) : 0;
    var sy = shake ? rr(-shake, shake) : 0;""",
"""    var sk = SET.shake ? shake : 0;
    var sx = sk ? rr(-sk, sk) : 0;
    var sy = sk ? rr(-sk, sk) : 0;""")

sub("""    renderAllies();
    drawMinimap();""",
"""    renderAllies();
    if (SET.minimap) drawMinimap();""")

# ==================================================== gamepad ================
sub("""  function screenToWorld(sx, sy) {""",
"""  // ---- controller ---------------------------------------------------------
  var pad = null, padPrev = {}, padSeen = false;
  function pollPad() {
    var list = navigator.getGamepads ? navigator.getGamepads() : null;
    pad = null;
    if (!list) return;
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].connected) { pad = list[i]; padSeen = true; break; }
    }
  }
  function padAxis(i) {
    if (!pad || !pad.axes || pad.axes.length <= i) return 0;
    var v = pad.axes[i];
    var dz = SET.dead / 100;
    if (v > -dz && v < dz) return 0;
    // rescale so the stick starts moving right at the edge of the deadzone
    return (v - (v > 0 ? dz : -dz)) / (1 - dz);
  }
  function padDown(i) { return !!(pad && pad.buttons && pad.buttons[i] && pad.buttons[i].pressed); }
  function padHit(i) {                       // pressed this frame only
    var now = padDown(i), was = padPrev[i];
    padPrev[i] = now;
    return now && !was;
  }

  // Nudge the aim toward whoever is closest to where you are already pointing.
  function aimAssist(e, ang) {
    if (!SET.assist) return ang;
    var best = ang, bestOff = 0.26;
    for (var i = 0; i < ents.length; i++) {
      var o = ents[i];
      if (o === e || !o.alive || !foes(e, o)) continue;
      var d = dist(e, o);
      if (d > 460 || !sightClear(e.x, e.y, o.x, o.y)) continue;
      var want = Math.atan2(o.y - e.y, o.x - e.x);
      var off = Math.abs(((want - ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
      if (off < bestOff) { bestOff = off; best = want; }
    }
    return best;
  }

  function screenToWorld(sx, sy) {""")

# --- wire it into the player ---------------------------------------------
sub("""    var ix = 0, iy = 0;
    if (sticks.move) {""",
"""    pollPad();
    var ix = 0, iy = 0;
    var padMove = false;
    if (pad) {
      var lx = padAxis(0), ly = padAxis(1);
      if (lx || ly) {
        var ll = Math.sqrt(lx * lx + ly * ly);
        ix = lx / (ll > 1 ? ll : 1); iy = ly / (ll > 1 ? ll : 1);
        padMove = true;
      }
      if (padHit(0)) playerPickup();
      if (padHit(1)) melee(e);
      if (padHit(2)) startReload(e);
      if (padHit(3)) swapSlot();
      if (padHit(5)) throwNade(e, 'smoke');
      if (padHit(6)) throwNade(e, 'frag');
      if (padHit(12)) useMed(e);
      if (padHit(9)) { pause(); return; }
    }
    if (!padMove && sticks.move) {""")

sub("""    var sprinting = !!keys['shift'] && (ix || iy);""",
    """    var sprinting = (!!keys['shift'] || padDown(4)) && (ix || iy);""")

sub("""    if (sticks.aim) {
      var adx = sticks.aim.x - sticks.aim.ox, ady = sticks.aim.y - sticks.aim.oy;
      if (Math.sqrt(adx * adx + ady * ady) > 10) e.ang = Math.atan2(ady, adx);
    } else e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);""",
"""    var rx = pad ? padAxis(2) : 0, ry = pad ? padAxis(3) : 0;
    if (rx || ry) {
      e.ang = aimAssist(e, Math.atan2(ry, rx));
    } else if (sticks.aim) {
      var adx = sticks.aim.x - sticks.aim.ox, ady = sticks.aim.y - sticks.aim.oy;
      if (Math.sqrt(adx * adx + ady * ady) > 10) e.ang = Math.atan2(ady, adx);
    } else if (!pad) e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);""")

sub("""    var firing = mouse.down || (sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
    if (firing) {""",
"""    var firing = mouse.down || padDown(7) ||
      (sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
    if (firing) {""")

# ==================================================== settings screen ========
sub("""  $('shopBtn').addEventListener('click', function () {""",
"""  function syncSettings() {
    $('setVol').value = SET.vol; $('setVolV').textContent = SET.vol;
    $('setDead').value = SET.dead; $('setDeadV').textContent = SET.dead;
    [['setAssist', 'assist'], ['setShake', 'shake'], ['setMap', 'minimap']].forEach(function (pair) {
      var b = $(pair[0]);
      b.textContent = SET[pair[1]] ? 'ON' : 'OFF';
      b.className = 'tgl' + (SET[pair[1]] ? ' on' : '');
    });
    pollPad();
    $('padTag').textContent = pad ? ('controller: ' + String(pad.id).slice(0, 38))
                                  : (padSeen ? 'controller disconnected' : 'no controller detected');
  }
  $('setVol').addEventListener('input', function () {
    SET.vol = parseInt(this.value, 10); $('setVolV').textContent = SET.vol; saveSettings();
  });
  $('setDead').addEventListener('input', function () {
    SET.dead = parseInt(this.value, 10); $('setDeadV').textContent = SET.dead; saveSettings();
  });
  [['setAssist', 'assist'], ['setShake', 'shake'], ['setMap', 'minimap']].forEach(function (pair) {
    $(pair[0]).addEventListener('click', function () {
      SET[pair[1]] = !SET[pair[1]];
      saveSettings();
      syncSettings();
    });
  });
  $('setBtn').addEventListener('click', function () {
    syncSettings();
    elMenu.hidden = true;
    $('settings').hidden = false;
  });
  $('setBack').addEventListener('click', function () {
    $('settings').hidden = true;
    elMenu.hidden = false;
  });
  window.addEventListener('gamepadconnected', function () { padSeen = true; syncSettings(); });

  $('shopBtn').addEventListener('click', function () {""")

sub("""    $('shop').hidden = true;
    elMenu.hidden = false;
    refreshCoins();
  }""",
"""    $('shop').hidden = true;
    $('settings').hidden = true;
    elMenu.hidden = false;
    refreshCoins();
  }""")

sub("""  loadWallet();
  refreshCoins();""",
"""  loadWallet();
  loadSettings();
  refreshCoins();""")

# ============================================ map choice on every mode =======
# Each mode has its own footprint; the CQB/WORLD switch picks which generator
# lays it out, so every mode can be fought indoors or in the open.
sub("""    if (mode === 'duel') genArena();
    else if (mode === 'gun') genRooms(96, 96, 6, 13, 52, 2, true);
    else if (mode === 'team') genRooms(118, 118, 7, 15, 66, 2, true);
    else if (mode === 'war') genRooms(156, 156, 8, 18, 110, 2, true);
    else if (mode === 'ctf') genRooms(126, 126, 7, 15, 74, 2, true);
    else if (mode === 'sect') genRooms(122, 122, 7, 15, 70, 2, true);
    else if (mode === 'zomb') genRooms(112, 112, 7, 15, 62, 2, true);
    else if (mapKind === 'world') genWorld();
    else genRooms(130, 130, 5, 13, 118, 1, true);""",
"""    var FOOTPRINT = {
      duel: 52, gun: 96, team: 118, war: 156, ctf: 126, sect: 122, zomb: 112, br: 130
    };
    var span = FOOTPRINT[mode] || 118;
    if (mapKind === 'world') genWorld(span);
    else if (mode === 'duel') genArena();
    else genRooms(span, span, mode === 'br' ? 5 : 7, mode === 'war' ? 18 : 15,
                  Math.round(span * span / 230), mode === 'br' ? 1 : 2, true);""")

sub("""  function genWorld() {
    MAP_W = 158; MAP_H = 158;""",
"""  function genWorld(span) {
    span = Math.max(56, span || 158);
    MAP_W = span; MAP_H = span;""")

sub("""    for (i = 0; i < 1400 && builds.length < 78; i++) {""",
    """    var wantBuilds = Math.max(8, Math.round(span * span / 320));
    for (i = 0; i < 1400 && builds.length < wantBuilds; i++) {""")

sub("""    for (i = 0; i < 820; i++) {
      var cxx = 3 + rnd(MAP_W - 6), cyy = 3 + rnd(MAP_H - 6);""",
"""    var wantCover = Math.max(60, Math.round(span * span / 30));
    for (i = 0; i < wantCover; i++) {
      var cxx = 3 + rnd(MAP_W - 6), cyy = 3 + rnd(MAP_H - 6);""")

# the map switch is no longer battle-royale only
sub("""    $('mapPick').hidden = mode !== 'br';""",
    """    $('mapPick').hidden = (mode === 'duel');""")

sub("""    var t = mode === 'br' ? MODE_TEXT['br_' + mapKind] : MODE_TEXT[mode];""",
"""    var t = mode === 'br' ? MODE_TEXT['br_' + mapKind] : MODE_TEXT[mode];
    if (mode !== 'br' && mode !== 'duel') {
      t += mapKind === 'world'
        ? '  \\u2014  WORLD: open ground and scattered buildings, with long sightlines between them.'
        : '  \\u2014  CQB: a dense warren of rooms and corridors.';
    }""")

# world keeps its own ground in every mode now
sub("""    var grassy = (mode === 'br' && mapKind === 'world');""",
    """    var grassy = (mapKind === 'world' && mode !== 'duel');""")

sub("""    var counts = {""",
"""    var counts = {""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p31 applied')

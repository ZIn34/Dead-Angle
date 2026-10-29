# -*- coding: utf-8 -*-
"""Most of a snapshot was decimal places. An angle of 0.8414709848078965 costs
eighteen characters and nobody can see the difference past two."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""  function packEnt(e) {
    var s0 = e.slots[0], s1 = e.slots[1];
    var bits = (e.alive ? 1 : 0) | (e.down ? 2 : 0) | (e.moving ? 4 : 0) |
               (e.air === 'plane' ? 8 : 0) | (e.air === 'chute' ? 16 : 0) | (e.bot ? 32 : 0) | (e.bleeding ? 64 : 0);
    return [e.id, Math.round(e.x), Math.round(e.y), e.ang, e.team, e.skin, bits, e.animT || 0, e.animFire || 0, e.swingT || 0,
            e.throwT || 0, e.meleeT || 0, Math.round(e.hp), e.revT || 0, e.downT || 0, e.respawnT || 0,
            e.level || 0, e.airT || 0, e.name, e.slot,""",
"""  // two decimals is finer than a pixel at this zoom, and a tenth of a second
  // is finer than a frame: the rest was just characters on the wire
  function r2(v) { return Math.round((v || 0) * 100) / 100; }
  function r1(v) { return Math.round((v || 0) * 10) / 10; }
  function packEnt(e) {
    var s0 = e.slots[0], s1 = e.slots[1];
    var bits = (e.alive ? 1 : 0) | (e.down ? 2 : 0) | (e.moving ? 4 : 0) |
               (e.air === 'plane' ? 8 : 0) | (e.air === 'chute' ? 16 : 0) | (e.bot ? 32 : 0) | (e.bleeding ? 64 : 0);
    return [e.id, Math.round(e.x), Math.round(e.y), r2(e.ang), e.team, e.skin, bits, r2(e.animT), r2(e.animFire), r2(e.swingT),
            r2(e.throwT), r2(e.meleeT), Math.round(e.hp), r1(e.revT), r1(e.downT), r1(e.respawnT),
            e.level || 0, r1(e.airT), e.name, e.slot,""")
sub("""            e.reserve, e.meds, e.nades, e.smokes, e.reloadT || 0, e.useT || 0, e.kills || 0];""",
    """            e.reserve, e.meds, e.nades, e.smokes, r2(e.reloadT), r2(e.useT), e.kills || 0];""")

# bullets, flashes and impacts carry long decimals too
sub("""      x.f = flashes.filter(function (q) { return nearGuest(g, q.x, q.y); });""",
"""      x.f = flashes.filter(function (q) { return nearGuest(g, q.x, q.y); }).map(function (q) {
        return { x: Math.round(q.x), y: Math.round(q.y), ang: r2(q.ang), t: r2(q.t), max: r2(q.max), tint: q.tint, scale: r2(q.scale) };
      });""")
sub("""      x.im = impacts.filter(function (q) { return nearGuest(g, q.x, q.y); });""",
"""      x.im = impacts.filter(function (q) { return nearGuest(g, q.x, q.y); }).map(function (q) {
        return { x: Math.round(q.x), y: Math.round(q.y), ang: r2(q.ang), t: r2(q.t), scale: r2(q.scale), fx: q.fx };
      });""")

# the floor only matters where you could actually walk onto it
sub("""  function nearOnly(g, arr) {
    var out = [];
    for (var i = 0; i < arr.length; i++) if (nearGuest(g, arr[i].x, arr[i].y)) out.push(arr[i]);
    return out;
  }""",
"""  function nearOnly(g, arr, radius) {
    var out = [], eye = guestEye(g);
    if (!eye) return arr.slice();
    var r = radius || seeRadius();
    for (var i = 0; i < arr.length; i++) {
      var dx = arr[i].x - eye.x, dy = arr[i].y - eye.y;
      if (dx * dx + dy * dy < r * r) out.push(arr[i]);
    }
    return out;
  }
  // loot is only any use within reach of it, so it travels a shorter way
  var LOOT_SEE = 640;""")
sub("""        var near = nearOnly(g, loot), sg = listSig(near);""",
    """        var near = nearOnly(g, loot, LOOT_SEE), sg = listSig(near);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p80 applied')

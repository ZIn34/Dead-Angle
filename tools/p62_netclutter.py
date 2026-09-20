# -*- coding: utf-8 -*-
"""Online: stop resending the whole floor twenty times a second."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- small packing for everything lying on the ground ---------------------------
sub("""  function nearOnly(g, arr) {""",
"""  var LTYPE = ['gun', 'ammo', 'med', 'nade', 'smoke'];
  function packLoot(it) {
    return [it.x | 0, it.y | 0, LTYPE.indexOf(it.type), it.key ? WKEYS.indexOf(it.key) : -1,
            it.ammo | 0, it.n | 0, (it.spin * 100) | 0, it.seen ? 1 : 0];
  }
  function unpackLoot(a) {
    return { x: a[0], y: a[1], type: LTYPE[a[2]], key: a[3] >= 0 ? WKEYS[a[3]] : null,
             ammo: a[4], n: a[5], spin: a[6] / 100, seen: !!a[7] };
  }
  function packMark(m) {
    return [m.x | 0, m.y | 0, +(m.ang || 0).toFixed(2), +(m.scale || 1).toFixed(2), +(m.t || 0).toFixed(2)];
  }
  function unpackMark(a) {
    return { x: a[0], y: a[1], ang: a[2], scale: a[3], t: a[4] };
  }
  function nearOnly(g, arr) {""")

# ---- nobody in the plane is ever drawn, so nobody in the plane is ever sent -----
sub("""        if (en === g.ent || en.team === g.ent.team || nearGuest(g, en.x, en.y)) x.e.push(packEnt(en));""",
"""        var ownSide = en === g.ent || en.team === g.ent.team;
        if (!ownSide && (en.air === 'plane' || !nearGuest(g, en.x, en.y))) continue;
        x.e.push(packEnt(en));""")

# ---- the floor: only while they can act on it, and only a few times a second ----
sub("""      // ground clutter near this guest only, and only when it changes for them
      var near = nearOnly(g, loot), sg = listSig(near);
      if (g.sigs.lo !== sg) { g.sigs.lo = sg; x.lo = near; }
      near = nearOnly(g, decals); sg = listSig(near);
      if (g.sigs.dc !== sg) { g.sigs.dc = sg; x.dc = near; }
      near = nearOnly(g, deaths); sg = listSig(near);
      if (g.sigs.de !== sg) { g.sigs.de = sg; x.de = near; }
      near = nearOnly(g, corpses); sg = listSig(near);
      if (g.sigs.co !== sg) { g.sigs.co = sg; x.co = near; }""",
"""      // The floor near this guest, four times a second instead of twenty, and
      // not at all while they are still in the plane - a guest crossing the
      // map re-enters this set constantly, and resending it was most of the
      // traffic in a full battle royale.
      g.clut = (g.clut || 0) + 1;
      if (!g.ent.air && g.clut % 5 === 0) {
        var near = nearOnly(g, loot), sg = listSig(near);
        if (g.sigs.lo !== sg) { g.sigs.lo = sg; x.lo = near.map(packLoot); }
        near = nearOnly(g, decals); sg = listSig(near);
        if (g.sigs.dc !== sg) { g.sigs.dc = sg; x.dc = near.map(packMark); }
        near = nearOnly(g, deaths); sg = listSig(near);
        if (g.sigs.de !== sg) { g.sigs.de = sg; x.de = near.map(packMark); }
        near = nearOnly(g, corpses); sg = listSig(near);
        if (g.sigs.co !== sg) { g.sigs.co = sg; x.co = near.map(packMark); }
      }""")

sub("""    if (m.lo) loot = m.lo;
    if (m.dc) decals = m.dc;
    if (m.de) deaths = m.de;
    if (m.co) corpses = m.co;""",
"""    if (m.lo) loot = m.lo.map(unpackLoot);
    if (m.dc) decals = m.dc.map(unpackMark);
    if (m.de) deaths = m.de.map(unpackMark);
    if (m.co) corpses = m.co.map(unpackMark);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p62 applied')

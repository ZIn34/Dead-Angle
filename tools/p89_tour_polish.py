# -*- coding: utf-8 -*-
"""Tourney: a results line that belongs to this mode, and the round reaching
everyone online rather than only the host."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- the results screen -------------------------------------------------------------
sub("""    if (mode === 'br') { big = '#' + place; small = 'OF ' + fieldN; }""",
"""    if (MODE.tourney) {
      big = won ? 'CHAMPION' : 'OUT';
      small = 'ROUND ' + Math.max(1, tour.round);
    }
    else if (mode === 'br') { big = '#' + place; small = 'OF ' + fieldN; }""")

# ---- everyone online sees the round and who is left ------------------------------------
sub("""      x.pg = pings.filter(function (q) { return q.team === g.ent.team; });""",
"""      if (MODE.tourney) {
        x.tr = [tour.round, tour.left.filter(function (e) { return e.alive || e.tourBye; }).length];
      }
      x.pg = pings.filter(function (q) { return q.team === g.ent.team; });""")
sub("""    pings = m.pg || [];""",
"""    pings = m.pg || [];
    if (m.tr) { tour.round = m.tr[0]; tourLeft = m.tr[1]; }""")
sub("""  var tour = { round: 0, left: [], waiting: false, champion: null, clock: 0 };""",
"""  var tour = { round: 0, left: [], waiting: false, champion: null, clock: 0 };
  var tourLeft = 0;                  // how many are still in, as told by the host""")
sub("""    var standing = tour.left.filter(function (e) { return e.alive || e.tourBye; });
    ctx.save();""",
"""    var standing = tour.left.filter(function (e) { return e.alive || e.tourBye; });
    var leftN = netGuest ? tourLeft : standing.length;
    ctx.save();""")
sub("""    ctx.fillText(standing.length + ' LEFT', cw / 2, y0 + 32);""",
    """    ctx.fillText(leftN + ' LEFT', cw / 2, y0 + 32);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p89 applied')

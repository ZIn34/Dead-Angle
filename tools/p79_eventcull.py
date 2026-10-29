# -*- coding: utf-8 -*-
"""Every spark, splash and gunshot anywhere on the map was going to everyone,
every tick. They carry a place, so they can be culled like everything else."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# out of the part everybody gets...
sub("""      h: [alive, score[0], score[1], round, roundClock, roundBreak, zombClock, matchTime, fieldN],
      ev: netEv
    });""",
"""      h: [alive, score[0], score[1], round, roundClock, roundBreak, zombClock, matchTime, fieldN]
    });""")

# ...and into each person's own slice, trimmed to what they could notice
sub("""      x.pg = pings.filter(function (q) { return q.team === g.ent.team; });""",
"""      // a shot on the far side of the map is nobody's business here, but
      // sound carries much further than sparks do, and the kill feed is for
      // everyone
      x.ev = [];
      var eye = guestEye(g), sr = seeRadius();
      for (var vi = 0; vi < netEv.length; vi++) {
        var q = netEv[vi], kind = q[0];
        if (kind === 'f') { x.ev.push(q); continue; }
        if (kind === 'c') { if (q[1] === g.ent.id) x.ev.push(q); continue; }
        if (!eye) { x.ev.push(q); continue; }
        var reach = kind === 'a' ? 2600 : sr;
        var edx = q[1] - eye.x, edy = q[2] - eye.y;
        if (edx * edx + edy * edy <= reach * reach) x.ev.push(q);
      }
      x.pg = pings.filter(function (q) { return q.team === g.ent.team; });""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p79 applied')

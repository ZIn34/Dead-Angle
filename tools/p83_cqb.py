# -*- coding: utf-8 -*-
"""CQB: still close quarters, but with room to move and a different shape every
time - wider and more varied corridors, the odd hall, and more loops so you are
not forever backing out of dead ends."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- rooms: mostly small, with the occasional hall --------------------------------
sub("""      var rw = rmin + rnd(rmax - rmin), rh = rmin + rnd(rmax - rmin);""",
"""      var rw = rmin + rnd(rmax - rmin), rh = rmin + rnd(rmax - rmin);
      // one room in eight opens out into a hall, so a map has somewhere to
      // fight as well as somewhere to creep
      if (Math.random() < 0.13) { rw += 3 + rnd(5); rh += 2 + rnd(4); }""")

# ---- corridors: wider, and not all the same -----------------------------------------
sub("""    function corridor(ax, ay, bx, by) {
      var x, y, k;
      for (x = Math.min(ax, bx); x <= Math.max(ax, bx); x++) for (k = 0; k < corrW; k++) carve(x, ay + k);
      for (y = Math.min(ay, by); y <= Math.max(ay, by); y++) for (k = 0; k < corrW; k++) carve(bx + k, y);
    }
    for (i = 1; i < rooms.length; i++) corridor(cx(rooms[i - 1]), cy(rooms[i - 1]), cx(rooms[i]), cy(rooms[i]));
    for (i = 0; i < Math.round(rooms.length * 0.35); i++) {
      var a = rooms[rnd(rooms.length)], b = rooms[rnd(rooms.length)];
      corridor(cx(a), cy(a), cx(b), cy(b));
    }""",
"""    function corridor(ax, ay, bx, by, wide) {
      var x, y, k, cw2 = wide || corrW;
      for (x = Math.min(ax, bx); x <= Math.max(ax, bx); x++) for (k = 0; k < cw2; k++) carve(x, ay + k);
      for (y = Math.min(ay, by); y <= Math.max(ay, by); y++) for (k = 0; k < cw2; k++) carve(bx + k, y);
    }
    // the main chain, with the odd wider run through it
    for (i = 1; i < rooms.length; i++) {
      corridor(cx(rooms[i - 1]), cy(rooms[i - 1]), cx(rooms[i]), cy(rooms[i]),
               corrW + (Math.random() < 0.3 ? 1 : 0));
    }
    // loops are what stop a map being a row of dead ends: plenty of them
    for (i = 0; i < Math.round(rooms.length * 0.55); i++) {
      var a = rooms[rnd(rooms.length)], b = rooms[rnd(rooms.length)];
      corridor(cx(a), cy(a), cx(b), cy(b), corrW + (Math.random() < 0.25 ? 1 : 0));
    }""")

# ---- a different density every match ---------------------------------------------------
sub("""    else genRooms(span, span, mode === 'br' ? 5 : 7, mode === 'war' ? 18 : 15,
                  Math.round(span * span / 230), mode === 'br' ? 1 : 2, true);""",
"""    // the divisor sets how packed the rooms are, and it moves every match, so
    // one map comes out warren-tight and the next has more air in it
    else genRooms(span, span, mode === 'br' ? 6 : 7, mode === 'war' ? 19 : 16,
                  Math.round(span * span / (215 + rnd(70))), 2, true);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p83 applied')

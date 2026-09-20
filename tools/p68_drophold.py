# -*- coding: utf-8 -*-
"""What you just put down stays down: a couple of seconds before you can walk
back onto it. Without it a drop was picked straight back up."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""  function autoPickup(e) {
    if (isZombie(e)) return;                  // the infected carry nothing
    for (var i = loot.length - 1; i >= 0; i--) {
      var it = loot[i];
      var dx = it.x - e.x, dy = it.y - e.y;
      if (dx * dx + dy * dy > 22 * 22) continue;""",
"""  // you cannot scoop up what you dropped a moment ago
  function heldBack(e, it) { return it.holdBy === e.id && it.hold > performance.now(); }
  function markDropped(e, it) { it.holdBy = e.id; it.hold = performance.now() + 2500; return it; }
  function autoPickup(e) {
    if (isZombie(e)) return;                  // the infected carry nothing
    for (var i = loot.length - 1; i >= 0; i--) {
      var it = loot[i];
      var dx = it.x - e.x, dy = it.y - e.y;
      if (dx * dx + dy * dy > 22 * 22) continue;
      if (heldBack(e, it)) continue;""")
sub("""    var it = e.prompt;
    if (!it) return;
    var idx = loot.indexOf(it);""",
"""    var it = e.prompt;
    if (!it || heldBack(e, it)) return;
    var idx = loot.indexOf(it);""")
sub("""    loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: 'gun', key: sl.key,
      spin: rr(0, 6.2832), ammo: sl.ammo, n: 0, seen: true
    });""",
"""    markDropped(e, loot[loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: 'gun', key: sl.key,
      spin: rr(0, 6.2832), ammo: sl.ammo, n: 0, seen: true
    }) - 1]);""")
sub("""    loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: type, key: null,
      spin: rr(0, 6.2832), ammo: 0, n: n, seen: true
    });""",
"""    markDropped(e, loot[loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: type, key: null,
      spin: rr(0, 6.2832), ammo: 0, n: n, seen: true
    }) - 1]);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p68 applied')

# -*- coding: utf-8 -*-
"""Switching who you watch works the same when you are on someone else's host."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""      else if (k === 'm' && player) { player.mapOpen = !player.mapOpen; player.mapCur = null; }""",
"""      else if (!netGuestPaused && player && !player.alive && player.spec && (k === 'a' || k === 'd')) specCycle(player, k === 'a' ? -1 : 1);
      else if (k === 'm' && player) { player.mapOpen = !player.mapOpen; player.mapCur = null; }""")
sub("""  function guestTick(dt) {
    pollPad();""",
"""  function guestTick(dt) {
    pollPad();
    if (player && !player.alive && player.spec && pad && !netGuestPaused) {
      if (padHit(PAD.swapL)) specCycle(player, -1);
      if (padHit(PAD.swapR)) specCycle(player, 1);
    }""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p67 applied')

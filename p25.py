# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# A search that runs out of budget used to return nothing, which left the bot
# standing there - and on a big map that is most searches. Hand back the best
# partial route instead, so they always make progress toward the goal.
sub("""    var open = new Heap();
    gScore[start] = 0; cameFrom[start] = -1; seenStamp[start] = stamp;
    open.push(start, 0);
    var expanded = 0;
    while (open.n.length && expanded < 24000) {
      var cur = open.pop();
      if (doneStamp[cur] === stamp) continue;
      doneStamp[cur] = stamp;
      expanded++;
      if (cur === goal) {
        var out = [], node = cur;
        while (node !== -1) {
          out.push({ x: (node % STRIDE) * TILE + TILE / 2, y: Math.floor(node / STRIDE) * TILE + TILE / 2 });
          node = cameFrom[node];
        }
        out.reverse();
        return out;
      }
      var ccx = cur % STRIDE, ccy = Math.floor(cur / STRIDE);""",
"""    var open = new Heap();
    gScore[start] = 0; cameFrom[start] = -1; seenStamp[start] = stamp;
    open.push(start, 0);
    var expanded = 0;

    function rebuild(node) {
      var out = [];
      while (node !== -1) {
        out.push({ x: (node % STRIDE) * TILE + TILE / 2, y: Math.floor(node / STRIDE) * TILE + TILE / 2 });
        node = cameFrom[node];
      }
      out.reverse();
      return out;
    }

    var bestNode = start;
    var bx0 = Math.abs(sx - tx), by0 = Math.abs(sy - ty);
    var bestH = (bx0 > by0) ? bx0 + 0.4142 * by0 : by0 + 0.4142 * bx0;

    while (open.n.length && expanded < 12000) {
      var cur = open.pop();
      if (doneStamp[cur] === stamp) continue;
      doneStamp[cur] = stamp;
      expanded++;
      if (cur === goal) return rebuild(cur);
      var ccx = cur % STRIDE, ccy = Math.floor(cur / STRIDE);
      var chx = Math.abs(ccx - tx), chy = Math.abs(ccy - ty);
      var ch2 = (chx > chy) ? chx + 0.4142 * chy : chy + 0.4142 * chx;
      if (ch2 < bestH) { bestH = ch2; bestNode = cur; }""")

sub("""      }
    }
    return null;
  }

  // ---------------------------------------------------------------- state""",
"""      }
    }
    // out of budget or walled off: go as far toward it as we got
    return bestNode !== start ? rebuild(bestNode) : null;
  }

  // ---------------------------------------------------------------- state""")

# never sit on a failed search for three seconds
sub("""  function pathTo(e, gx, gy, cool) {
    e.path = findPath(Math.floor(e.x / TILE), Math.floor(e.y / TILE), Math.floor(gx / TILE), Math.floor(gy / TILE));
    e.pathI = 0; e.repathT = cool;
  }""",
"""  function pathTo(e, gx, gy, cool) {
    e.path = findPath(Math.floor(e.x / TILE), Math.floor(e.y / TILE), Math.floor(gx / TILE), Math.floor(gy / TILE));
    e.pathI = 0;
    // nothing usable came back - try again shortly rather than standing about
    e.repathT = (e.path && e.path.length) ? cool : 0.4;
  }""")

# and don't hammer the search every frame when wedged
sub("""      if (Math.abs(e.x - e.lastX) + Math.abs(e.y - e.lastY) < 10) {
        e.path = null; e.repathT = 0; e.alertT = 0; e.lootGoal = null; e.strafe *= -1;
      }""",
"""      if (Math.abs(e.x - e.lastX) + Math.abs(e.y - e.lastY) < 10) {
        e.path = null; e.repathT = 0.25; e.alertT = 0; e.lootGoal = null; e.strafe *= -1;
        // nudge free of whatever corner has them
        moveEnt(e, rr(-14, 14), rr(-14, 14));
      }""")

# healing should never be the whole of a bot's turn
sub("""    } else if (e.hp < 48 && e.meds > 0) {
      useMed(e);
    } else {""",
"""    } else {
      if (e.hp < 48 && e.meds > 0 && e.reloadT <= 0) useMed(e);""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p25 applied')

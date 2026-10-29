# -*- coding: utf-8 -*-
"""Two fights were stalling the whole bracket: cover could seal a corner off,
and nothing ever decided a pair who could not reach each other."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- a pit you can always cross ---------------------------------------------------
sub("""      pits.push({
        a: { x: ox + 4, y: oy + Math.floor(PIT / 2) },            // one corner
        b: { x: ox + PIT - 5, y: oy + Math.floor(PIT / 2) },      // and the other
        cx: ox + PIT / 2, cy: oy + PIT / 2
      });""",
"""      // a clear cross through the middle, so cover can never seal one of them
      // into a corner, and clear ground around both starts
      var midY = oy + Math.floor(PIT / 2), midX = ox + Math.floor(PIT / 2);
      for (var cxx = ox + 2; cxx < ox + PIT - 2; cxx++) { carve(cxx, midY); carve(cxx, midY - 1); }
      for (var cyy = oy + 2; cyy < oy + PIT - 2; cyy++) { carve(midX, cyy); carve(midX - 1, cyy); }
      var spots = [{ x: ox + 4, y: midY }, { x: ox + PIT - 5, y: midY }];
      for (var si = 0; si < spots.length; si++) {
        for (var sy = -1; sy <= 1; sy++) for (var sx = -1; sx <= 1; sx++) carve(spots[si].x + sx, spots[si].y + sy);
      }
      pits.push({ a: spots[0], b: spots[1], cx: ox + PIT / 2, cy: oy + PIT / 2 });""")

# ---- and a clock, so no pair can hold the whole bracket up -------------------------
sub("""  var tour = { round: 0, left: [], waiting: false, champion: null };""",
"""  var tour = { round: 0, left: [], waiting: false, champion: null, clock: 0 };
  var TOUR_ROUND_SECS = 75;""")
sub("""    tour.round++;
    tour.waiting = false;""",
"""    tour.round++;
    tour.waiting = false;
    tour.clock = TOUR_ROUND_SECS;""")
sub("""  function tourTick() {
    if (!MODE.tourney || state !== 'play' || !tour.left.length) return;""",
"""  function tourTick(dt) {
    if (!MODE.tourney || state !== 'play' || !tour.left.length) return;
    // a pair who cannot finish each other off does not get to hold everyone
    // else up: when the round clock runs out, the healthier one goes through
    tour.clock -= dt || 0;
    if (tour.clock <= 0) {
      tour.clock = 20;
      for (var sp2 = 0; sp2 < pits.length; sp2++) {
        var still = tour.left.filter(function (e) { return e.pit === sp2 && e.alive; });
        if (still.length < 2) continue;
        still.sort(function (x, y) { return y.hp - x.hp; });
        var loser = still[still.length - 1];
        feed('<b>' + still[0].name + '</b> wins on health', still[0].local || loser.local);
        loser.hp = 0;
        kill(loser, still[0].id);
      }
    }""")
sub("""    tourTick();""", """    tourTick(dt);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p88 applied')

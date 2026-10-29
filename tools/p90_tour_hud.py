# -*- coding: utf-8 -*-
"""Tourney HUD: the counter counts the tournament, nobody is marked as your
teammate, and the waiting card shows when your own fight is over."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- the top counter counts fighters left in the bracket --------------------------
sub("""    tour.left = list.slice();""",
"""    tour.left = list.slice();
    alive = list.length;""")
sub("""    if (tour.clock <= 0) {
      tour.clock = 20;""",
"""    alive = tour.left.filter(function (e) { return e.alive || e.tourBye; }).length;
    if (tour.clock <= 0) {
      tour.clock = 20;""")

# ---- in a tourney nobody is on your side ------------------------------------------
sub("""  function renderAllies() {
    if (noOverlay || !player.alive) return;""",
"""  function renderAllies() {
    if (noOverlay || !player.alive) return;
    if (MODE.tourney) return;                 // everyone here is an opponent or none of your business""")
sub("""    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a.alive || a === player || a.team !== player.team) continue;
      ctx.fillStyle = '#7ce7d8';""",
"""    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a.alive || a === player || a.team !== player.team || MODE.tourney) continue;
      ctx.fillStyle = '#7ce7d8';""")

# ---- the waiting card, for whoever is waiting -------------------------------------
sub("""    var me = player;
    if (!me || (me.alive && !me.tourBye)) return;""",
"""    var me = player;
    if (!me) return;
    var fightOver;
    if (netGuest) fightOver = !!tourIdle;
    else fightOver = me.tourOut || me.tourBye ||
      !ents.some(function (o) { return o !== me && o.pit === me.pit && o.alive; });
    if (!fightOver) return;""")
sub("""    ctx.fillText(me.tourOut ? 'YOU ARE OUT - WATCHING THE REST'
               : 'WAITING FOR THE OTHER FIGHTS TO FINISH', cw / 2, y0 + 60);""",
"""    ctx.fillText(!me.alive ? 'YOU ARE OUT - WATCHING THE REST'
               : 'YOUR FIGHT IS WON - WAITING FOR THE REST', cw / 2, y0 + 60);""")
# the host tells each guest whether their own fight is settled
sub("""        x.tr = [tour.round, tour.left.filter(function (e) { return e.alive || e.tourBye; }).length];""",
"""        var gIdle = !ents.some(function (o) { return o !== g.ent && o.pit === g.ent.pit && o.alive; });
        x.tr = [tour.round, tour.left.filter(function (e) { return e.alive || e.tourBye; }).length, gIdle ? 1 : 0];""")
sub("""    if (m.tr) { tour.round = m.tr[0]; tourLeft = m.tr[1]; }""",
    """    if (m.tr) { tour.round = m.tr[0]; tourLeft = m.tr[1]; tourIdle = !!m.tr[2]; }""")
sub("""  var tourLeft = 0;                  // how many are still in, as told by the host""",
"""  var tourLeft = 0;                  // how many are still in, as told by the host
  var tourIdle = false;              // and whether your own fight is settled""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p90 applied')

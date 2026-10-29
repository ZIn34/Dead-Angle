# -*- coding: utf-8 -*-
"""1V1 TOURNEY: everyone is paired off into their own walled pit, the winners
are paired again, and it runs until one is left."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); so = s
h = io.open(H, encoding='utf-8').read(); ho = h

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('JS PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

def subh(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

# ---- the mode ---------------------------------------------------------------------
sub("""    tut:  { field: 1,  zone: false, loot: false, respawn: false, label: 'TUTORIAL' }""",
"""    tour: { field: 16, zone: false, loot: false, respawn: false, label: 'LEFT', tourney: true },
    tut:  { field: 1,  zone: false, loot: false, respawn: false, label: 'TUTORIAL' }""")

# ---- a field of pits, one per pair ---------------------------------------------------
sub("""  function genArena() {""",
"""  // One walled pit per pair, laid out in a grid with no way between them.
  // Everybody fights at the same time without anyone else wandering in.
  var PIT = 26, pits = [];
  function genPits(pairCount) {
    var cols = Math.max(1, Math.ceil(Math.sqrt(pairCount)));
    var rows = Math.max(1, Math.ceil(pairCount / cols));
    MAP_W = cols * PIT + 2; MAP_H = rows * PIT + 2;
    grid.fill(1);
    mat.fill(0); curMat = 1;
    insideTiles.length = 0;
    pits = [];
    for (var p = 0; p < pairCount; p++) {
      var ox = 1 + (p % cols) * PIT, oy = 1 + Math.floor(p / cols) * PIT;
      // the floor of this pit, two tiles in from its walls
      for (var y = oy + 2; y < oy + PIT - 2; y++) {
        for (var x = ox + 2; x < ox + PIT - 2; x++) carve(x, y);
      }
      // a little cover so it is not a bare box
      var blocks = 3 + rnd(3);
      for (var b = 0; b < blocks; b++) {
        var bw = 2 + rnd(4), bh = 2 + rnd(4);
        var bx = ox + 4 + rnd(Math.max(1, PIT - bw - 8)), by = oy + 4 + rnd(Math.max(1, PIT - bh - 8));
        for (var yy = by; yy < by + bh; yy++) for (var xx = bx; xx < bx + bw; xx++) setT(xx, yy, 1);
      }
      pits.push({
        a: { x: ox + 4, y: oy + Math.floor(PIT / 2) },            // one corner
        b: { x: ox + PIT - 5, y: oy + Math.floor(PIT / 2) },      // and the other
        cx: ox + PIT / 2, cy: oy + PIT / 2
      });
    }
    finishMap();
  }

  function genArena() {""")

# ---- the bracket --------------------------------------------------------------------
sub("""  function foes(a, b) { return a.team !== b.team; }""",
"""  // In a tourney your only enemy is the one in your pit.
  function foes(a, b) {
    if (MODE.tourney) return a.pit === b.pit && a.team !== b.team;
    return a.team !== b.team;
  }
  var tour = { round: 0, left: [], waiting: false, champion: null };
  function tourNames(list) {
    return list.map(function (e) { return e.name; });
  }
  // Pair up whoever is left and drop each pair into their own pit.
  function tourSeed(list) {
    shuffle(list);
    tour.round++;
    tour.waiting = false;
    var pairCount = Math.ceil(list.length / 2);
    if (pits.length < pairCount) genPits(pairCount);
    var i;
    for (i = 0; i < ents.length; i++) { ents[i].pit = -1; ents[i].tourOut = ents[i].tourOut || false; }
    for (i = 0; i < list.length; i += 2) {
      var pit = pits[i >> 1], one = list[i], two = list[i + 1];
      one.pit = i >> 1; one.team = 0;
      placeEnt(one, pit.a);
      reviveForTour(one);
      if (two) {
        two.pit = i >> 1; two.team = 1;
        placeEnt(two, pit.b);
        reviveForTour(two);
      } else {
        // odd one out: through to the next round without a fight
        one.tourBye = true;
        feed('<b>' + one.name + '</b> gets a bye', one.local);
      }
    }
    tour.left = list.slice();
    var mine = locals[0] && locals[0].pit >= 0 ? ents.filter(function (e) {
      return e.pit === locals[0].pit && e !== locals[0] && !e.tourOut;
    })[0] : null;
    feed('<b>ROUND ' + tour.round + '</b> - ' + list.length + ' left' + (mine ? ' - you face <b>' + mine.name + '</b>' : ''), true);
  }
  function reviveForTour(e) {
    e.alive = true; e.down = false; e.hp = 100; e.respawnT = 0; e.bleeding = false;
    e.kc = null; e.spec = null; e.pendEnd = null;
    giveLoadout(e);
  }
  // A pit is settled when one of the two is out. When every pit is settled,
  // the winners go again.
  function tourTick() {
    if (!MODE.tourney || state !== 'play' || !tour.left.length) return;
    var standing = tour.left.filter(function (e) { return e.alive || e.tourBye; });
    var busy = false;
    for (var p = 0; p < pits.length; p++) {
      var inPit = tour.left.filter(function (e) { return e.pit === p && (e.alive || e.tourBye); });
      var started = tour.left.filter(function (e) { return e.pit === p; });
      if (started.length === 2 && inPit.length === 2) { busy = true; break; }
    }
    if (busy) return;                       // somebody is still fighting
    if (standing.length <= 1) {
      tour.champion = standing[0] || null;
      var mineWon = !!(tour.champion && tour.champion.local);
      finish(mineWon, tour.champion
        ? (mineWon ? 'You took the whole thing.' : tour.champion.name + ' took the whole thing.')
        : 'Nobody left standing.', 1);
      tour.left = [];
      return;
    }
    standing.forEach(function (e) { e.tourBye = false; });
    tourSeed(standing);
  }""")

# ---- the match starts as a bracket ------------------------------------------------------
sub("""    if (mapKind === 'world' && mode !== 'tut') genWorld(span);""",
"""    if (MODES[mode].tourney) genPits(Math.ceil(MODES[mode].field / 2));
    else if (mapKind === 'world' && mode !== 'tut') genWorld(span);""")
sub("""    } else {
      // a different skin each, so people are told apart by more than a colour
      var pool = [];
      for (var k = 0; k < 16; k++) pool.push(k);
      shuffle(pool);
      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; e.team = idx; });
    }""",
"""    } else {
      // a different skin each, so people are told apart by more than a colour
      var pool = [];
      for (var k = 0; k < 16; k++) pool.push(k);
      shuffle(pool);
      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; e.team = idx; });
    }
    if (MODE.tourney) {
      tour = { round: 0, left: [], waiting: false, champion: null };
      ents.forEach(function (e) { e.tourOut = false; e.tourBye = false; e.pit = -1; });
      tourSeed(ents.slice());
    }""")

# ---- losing a fight puts you out, not back in -------------------------------------------
sub("""    if (mode === 'duel') {""",
"""    if (MODE.tourney) {
      e.tourOut = true;
      var winner = ents.filter(function (o) { return o.pit === e.pit && o !== e && o.alive; })[0];
      if (winner) feed('<b>' + winner.name + '</b> beat <b>' + e.name + '</b>', winner.local || e.local);
      return;
    }
    if (mode === 'duel') {""")
sub("""    pingTick(dt);
    sightTick(dt);
    specTick();""",
"""    pingTick(dt);
    sightTick(dt);
    tourTick();
    specTick();""")

# ---- what you see while you wait ---------------------------------------------------------
sub("""  function renderDropHint() {""",
"""  // Between fights: who is left, and who you are waiting on.
  function renderTourney() {
    if (noOverlay || !MODE.tourney || state !== 'play') return;
    var me = player;
    if (!me || (me.alive && !me.tourBye)) return;
    var standing = tour.left.filter(function (e) { return e.alive || e.tourBye; });
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    var y0 = ch * 0.16;
    ctx.font = '400 15px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillStyle = '#f2bd1d';
    ctx.fillText('ROUND ' + tour.round, cw / 2, y0);
    ctx.font = '400 34px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillStyle = '#f1e7d0';
    ctx.fillText(standing.length + ' LEFT', cw / 2, y0 + 32);
    ctx.font = '500 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(241,231,208,.75)';
    ctx.fillText(me.tourOut ? 'YOU ARE OUT - WATCHING THE REST'
               : 'WAITING FOR THE OTHER FIGHTS TO FINISH', cw / 2, y0 + 60);
    var names = tourNames(standing).slice(0, 8).join('   ');
    if (names) {
      ctx.font = '600 10px "IBM Plex Mono", monospace';
      ctx.fillStyle = 'rgba(146,170,196,.9)';
      ctx.fillText(names, cw / 2, y0 + 80);
    }
    ctx.restore();
  }

  function renderDropHint() {""")
sub("""    renderTutorial();
    renderDropHint();""",
"""    renderTutorial();
    renderTourney();
    renderDropHint();""")

io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ---- pickable, in both menus -------------------------------------------------------------
subh("""            <button type="button" data-m="gun">GUN GAME</button>""",
"""            <button type="button" data-m="gun">GUN GAME</button>
            <button type="button" data-m="tour">1V1 TOURNEY</button>""")
subh("""              <button type="button" data-m="gun">GUN GAME</button>""",
"""              <button type="button" data-m="gun">GUN GAME</button>
              <button type="button" data-m="tour">1V1 TOURNEY</button>""")
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p87 applied')

# -*- coding: utf-8 -*-
"""2v2 duel scoring, a bigger battle royale island, and a hands-on tutorial."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ================================================================ big map ==
sub("""  var STRIDE = 168;                // max map dimension; maps vary inside it""",
    """  var STRIDE = 232;                // max map dimension; maps vary inside it""")
sub("""duel: 52, gun: 96, team: 118, war: 156, ctf: 126, sect: 122, zomb: 112, br: 164""",
    """duel: 52, gun: 96, team: 118, war: 156, ctf: 126, sect: 122, zomb: 112, br: 224""")
# longer routes on a bigger island need a longer search
sub("""    while (open.n.length && expanded < 12000) {""",
    """    while (open.n.length && expanded < 26000) {""")
sub("""br_cqb: 'Ten drop into""", """br_cqb: 'Twenty-six drop into""")
sub("""br_world: 'Ten drop into""", """br_world: 'Twenty-six drop into""")

# ================================================================ 2v2 duel ==
# Rounds are won by sides, not by whoever pulled the trigger, and a round
# only ends when a whole side is down.
sub("""    if (mode === 'duel') {
      if (killer && killer !== e) {
        score[killer.id]++;
        if (score[killer.id] >= MODE.target) {
          lastWinner = killer;
          finish(!!killer.local, killer.local
            ? ((locals.length > 1) ? killer.name + ' took it ' + score[killer.id] + '\\u2013' + score[e.id] + '.'
                       : 'You took it ' + score[0] + '\\u2013' + score[1] + '.')
            : kn + ' took it ' + score[1] + '\\u2013' + score[0] + '.');
          return;
        }
      }
      roundBreak = 1.8;
      return;
    }""",
"""    if (mode === 'duel') {
      for (var dq = 0; dq < ents.length; dq++) {
        if (ents[dq] !== e && ents[dq].alive && ents[dq].team === e.team) return;   // their partner fights on
      }
      var wt = 1 - e.team;                       // two sides: 0 and 1
      score[wt]++;
      if (score[wt] >= MODE.target) {
        for (var dw = 0; dw < ents.length; dw++) if (ents[dw].team === wt) { lastWinner = ents[dw]; break; }
        var mine2 = wt === player.team, sw = score[wt], sl = score[1 - wt];
        var who = squad > 1 ? (mine2 ? 'Your side' : 'Their side')
                            : (mine2 ? (locals.length > 1 ? player.name : 'You') : (lastWinner ? lastWinner.name : kn));
        finish(mine2, who + ' took it ' + sw + '\\u2013' + sl + '.');
        return;
      }
      roundBreak = 1.8;
      return;
    }""")
sub("""    else if (mode === 'duel') { big = won ? 'WIN' : 'LOSS'; small = score[0] + ' \\u2014 ' + score[1]; }""",
    """    else if (mode === 'duel') { big = won ? 'WIN' : 'LOSS'; small = score[player.team] + ' \\u2014 ' + score[1 - player.team]; }""")
sub("""    } else if (mode === 'duel') {
      elAlive.textContent = score[0] + ' \\u2013 ' + score[1];""",
    """    } else if (mode === 'duel') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];""")
# a new round puts each side at its own end, partners side by side
sub("""  function newRound() {
    var sp = pickSpawns(2);
    ents.forEach(function (e, i) { placeEnt(e, sp[i % sp.length]); });""",
"""  function newRound() {
    var sp = pickSpawns(2), seat = [0, 0];
    ents.forEach(function (e) {
      var t = e.team & 1, base = sp[t % sp.length], k = seat[t]++;
      placeEnt(e, k ? besideTile(base, k) : base);
    });""")
sub("""  function feed(html, mine) {""",
"""  // an open tile a step or two from `t`, so partners do not stack
  function besideTile(t, k) {
    var offs = [[2, 0], [0, 2], [-2, 0], [0, -2], [2, 2], [-2, -2]];
    for (var i = 0; i < offs.length; i++) {
      var o2 = offs[(k - 1 + i) % offs.length], x = t.x + o2[0], y = t.y + o2[1];
      if (x > 0 && y > 0 && x < MAP_W - 1 && y < MAP_H - 1 && !isWall(x, y)) return { x: x, y: y };
    }
    return t;
  }

  function feed(html, mine) {""")

# ================================================================ tutorial ==
sub("""    zomb: { field: 20, zone: false, loot: false, respawn: true,  label: 'ALIVE', teams: true, zombies: true, clock: 190 }
  };""",
"""    zomb: { field: 20, zone: false, loot: false, respawn: true,  label: 'ALIVE', teams: true, zombies: true, clock: 190 },
    tut:  { field: 1,  zone: false, loot: false, respawn: false, label: 'TUTORIAL' }
  };""")
sub("""    if (mapKind === 'world') genWorld(span);
    else if (mode === 'duel') genArena();""",
    """    if (mapKind === 'world' && mode !== 'tut') genWorld(span);
    else if (mode === 'duel' || mode === 'tut') genArena();""")
sub("""    var online = netRole === 'host' && netGuests.length > 0;
    var sc = online ? null : (splitWant ? splitControls() : null);""",
    """    var online = netRole === 'host' && netGuests.length > 0 && mode !== 'tut';
    var sc = (online || mode === 'tut') ? null : (splitWant ? splitControls() : null);""")
sub("""    if (netRole === 'host') for (var gi = 0; gi < netGuests.length; gi++) admitGuest(netGuests[gi], true);""",
    """    if (netRole === 'host' && mode !== 'tut') for (var gi = 0; gi < netGuests.length; gi++) admitGuest(netGuests[gi], true);
    if (mode === 'tut') tutSetup();""")
sub("""  function giveLoadout(e) {
    if (mode === 'gun') {""",
"""  function giveLoadout(e) {
    if (mode === 'tut') {
      e.slots = [e.dummy ? null : { key: 'pistol', ammo: WEAPONS.pistol.mag }, null];
      e.slot = 0; e.reserve = e.dummy ? 0 : 90; e.meds = 0; e.nades = 0; e.smokes = 0;
      return;
    }
    if (mode === 'gun') {""")
sub("""    if (MODE.zombies) {
      if (e.team === 0) {""",
"""    if (mode === 'tut') { e.respawnT = e.dummy ? 1.3 : 2; tutOn('kill', e); return; }
    if (MODE.zombies) {
      if (e.team === 0) {""")
sub("""      if (e.bot && e.alive && !e.down && !e.air) botThink(e, dt);""",
    """      if (e.bot && e.alive && !e.down && !e.air && !e.dummy) botThink(e, dt);""")
sub("""    if (MODE.respawn) {
      for (i = 0; i < ents.length; i++) {""",
"""    if (mode === 'tut') tutTick(dt);
    if (MODE.respawn) {
      for (i = 0; i < ents.length; i++) {""")
sub("""    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    renderDropHint();""",
"""    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    renderTutorial();
    renderDropHint();""")
sub("""    } else if (mode === 'duel') {
      elAlive.textContent = score[player.team]""",
"""    } else if (mode === 'tut') {
      elAlive.textContent = 'TUTORIAL';
      elZone.className = 'zone-line';
      elZone.textContent = 'STEP ' + Math.min(tut.i + 1, TUT.length) + ' OF ' + TUT.length + '  \\u00b7  ESC TO LEAVE';
    } else if (mode === 'duel') {
      elAlive.textContent = score[player.team]""")
sub("""  var MODE_LABEL = { br: 'Battle royale',""", """  var MODE_LABEL = { tut: 'Tutorial', br: 'Battle royale',""")

sub("""  function newRound() {""",
r"""  // ---------------------------------------------------------------- tutorial
  // A small arena, three standing targets, and one thing to learn at a time.
  // Each step waits for you to actually do it.
  var tut = { i: 0, t: 0, moved: 0, sprint: 0, kills: 0, lx: 0, ly: 0, slotWas: 0, flash: 0 };
  var TUT = [
    { title: 'MOVE', k: 'W A S D to walk', p: 'LEFT STICK to walk',
      done: function () { return tut.moved > 260; } },
    { title: 'AIM', k: 'Point with the MOUSE - you always face it', p: 'Point with the RIGHT STICK',
      done: function () { return tut.t > 2.5; } },
    { title: 'SHOOT', k: 'CLICK to shoot a target', p: 'RT to shoot a target',
      done: function () { return tut.kills >= 1; } },
    { title: 'RELOAD', k: 'R to reload', p: 'X to reload',
      start: function () { var sl = curSlot(player); if (sl) sl.ammo = Math.min(sl.ammo, 4); },
      done: function () { return player.reloadT > 0; } },
    { title: 'PICK UP', k: 'Walk to the rifle and press E', p: 'Walk to the rifle and press A',
      start: function () { tutDrop('gun', 'silenced'); },
      done: function () { return hasGun(player, 'silenced'); } },
    { title: 'SWAP', k: 'Q (or 1 / 2) swaps weapons', p: 'D-PAD LEFT / RIGHT swaps weapons',
      start: function () { tut.slotWas = player.slot; },
      done: function () { return player.slot !== tut.slotWas; } },
    { title: 'SPRINT', k: 'Hold SHIFT while walking - fast, but loud', p: 'Hold LB while walking - fast, but loud',
      done: function () { return tut.sprint > 1.2; } },
    { title: 'FRAG', k: 'G throws a frag - hit the group', p: 'LT throws a frag - hit the group',
      start: function () { player.nades = Math.max(player.nades, 1); tut.have = player.nades; },
      done: function () { return player.nades < tut.have; } },
    { title: 'SMOKE', k: 'H throws smoke - nobody sees through it', p: 'RB throws smoke - nobody sees through it',
      start: function () { player.smokes = Math.max(player.smokes, 1); tut.have = player.smokes; },
      done: function () { return player.smokes < tut.have; } },
    { title: 'HEAL', k: 'You are hurt. F uses a stim', p: 'You are hurt. Y uses a stim',
      start: function () { player.hp = Math.min(player.hp, 45); player.meds = Math.max(player.meds, 1); tut.have = player.meds; },
      done: function () { return player.meds < tut.have; } },
    { title: 'MELEE', k: 'V swings the gun butt - works with no ammo', p: 'B swings the gun butt - works with no ammo',
      done: function () { return player.meleeT > 0; } },
    { title: 'LISTEN', k: 'Every shot and footstep makes noise, and bots hunt by ear. In BLACKOUT you only see sound rings - a muzzle flash is the one exact giveaway.',
      p: null, wait: 7, done: function () { return tut.t > 7; } },
    { title: 'TEAM UP', k: 'In squad and team modes, stand beside a downed teammate to revive them. Blue markers are always your side.',
      p: null, wait: 7, done: function () { return tut.t > 7; } },
    { title: 'DROP IN', k: 'Battle royale starts in a plane: SPACE to jump, then steer your chute with W A S D. Stay inside the closing ring.',
      p: 'Battle royale starts in a plane: A to jump, then steer your chute with the LEFT STICK. Stay inside the closing ring.',
      wait: 8, done: function () { return tut.t > 8; } },
    { title: 'READY', k: 'That is everything. Press ENTER for the menu.', p: 'That is everything. Press A for the menu.',
      last: true, done: function () { return false; } }
  ];
  function hasGun(e, key) { return !!((e.slots[0] && e.slots[0].key === key) || (e.slots[1] && e.slots[1].key === key)); }
  function tutDrop(type, key) {
    // a couple of steps in front of you, on open floor
    var tx = Math.floor((player.x + Math.cos(player.ang) * 70) / TILE), ty = Math.floor((player.y + Math.sin(player.ang) * 70) / TILE);
    var t = { x: clamp(tx, 1, MAP_W - 2), y: clamp(ty, 1, MAP_H - 2) };
    if (isWall(t.x, t.y)) t = besideTile({ x: Math.floor(player.x / TILE), y: Math.floor(player.y / TILE) }, 1);
    addLoot(t.x, t.y, type, key, 0);
  }
  function tutSetup() {
    tut = { i: 0, t: 0, moved: 0, sprint: 0, kills: 0, lx: player.x, ly: player.y, slotWas: 0, flash: 0, have: 0 };
    // three targets in a loose group across the arena, facing you
    var px = Math.floor(player.x / TILE), py = Math.floor(player.y / TILE);
    var far = null, best = -1;
    for (var i = 0; i < floorTiles.length; i += 2) {
      var f = floorTiles[i], d = (f.x - px) * (f.x - px) + (f.y - py) * (f.y - py);
      if (d > 90 && d < 260 && d > best && lineClear(player.x, player.y, f.x * TILE + TILE / 2, f.y * TILE + TILE / 2)) { best = d; far = f; }
    }
    if (!far) far = floorTiles[rnd(floorTiles.length)];
    for (var k = 0; k < 3; k++) {
      var spot = k ? besideTile(far, k) : far;
      var d2 = makeEnt(spot, false, 'TARGET');
      d2.dummy = true; d2.team = 1; d2.skin = 3 + k; d2.home = spot;
      ents.push(d2);
      placeEnt(d2, spot);
      d2.ang = Math.atan2(player.y - d2.y, player.x - d2.x);
    }
    charCache = {};
    if (TUT[0].start) TUT[0].start();
  }
  function tutOn(what, e) {
    if (what === 'kill' && e && e.dummy) tut.kills++;
  }
  var tutEnterPrev = false;
  function tutTick(dt) {
    var i;
    // targets stand back up where they stood, and always face you
    for (i = 0; i < ents.length; i++) {
      var d = ents[i];
      if (!d.dummy) continue;
      if (!d.alive) {
        d.respawnT -= dt;
        if (d.respawnT <= 0) { placeEnt(d, d.home); d.slots = [null, null]; }
      } else d.ang = Math.atan2(player.y - d.y, player.x - d.x);
    }
    if (!player.alive) {
      player.respawnT -= dt;
      if (player.respawnT <= 0) placeEnt(player, { x: Math.floor(player.x / TILE), y: Math.floor(player.y / TILE) });
      return;
    }
    tut.moved += Math.sqrt((player.x - tut.lx) * (player.x - tut.lx) + (player.y - tut.ly) * (player.y - tut.ly));
    tut.lx = player.x; tut.ly = player.y;
    if ((player._spd || 0) > 200) tut.sprint += dt;
    tut.t += dt;
    if (tut.flash > 0) tut.flash -= dt;
    var st = TUT[tut.i];
    if (st.last) {
      var go = !!keys['enter'] || padDown(0);
      if (go && !tutEnterPrev) { tutDone(); return; }
      tutEnterPrev = go;
      return;
    }
    if (st.done()) {
      tut.i++; tut.t = 0; tut.flash = 0.9;
      tutEnterPrev = !!keys['enter'] || padDown(0);
      audioEmit(player.x, player.y, PICK_SND, player.id);
      if (TUT[tut.i].start) TUT[tut.i].start();
    }
  }
  function tutDone() {
    try { localStorage.setItem('earshot.tutDone', '1'); } catch (err) {}
    goHome();
    syncTutBtn();
  }
  function syncTutBtn() {
    var done = false;
    try { done = localStorage.getItem('earshot.tutDone') === '1'; } catch (err) {}
    var b = $('tutBtn');
    if (b) { b.className = done ? 'go ghost' : 'go'; b.textContent = done ? 'TUTORIAL' : 'TUTORIAL — START HERE'; }
  }
  function renderTutorial() {
    if (mode !== 'tut' || !player) return;
    var st = TUT[tut.i];
    var txt = (usingPad(player) && st.p) ? st.p : st.k;
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    // wrap the instruction to the width of the screen
    ctx.font = '500 13px "IBM Plex Mono", monospace';
    var maxW = Math.min(cw - 40, 520), words = txt.split(' '), lines = [], line = '';
    for (var w = 0; w < words.length; w++) {
      var tryL = line ? line + ' ' + words[w] : words[w];
      if (ctx.measureText(tryL).width > maxW - 36 && line) { lines.push(line); line = words[w]; } else line = tryL;
    }
    if (line) lines.push(line);
    var bw = maxW, bh = 52 + lines.length * 19, bx = cw / 2 - bw / 2, by = ch * 0.14;
    ctx.fillStyle = '#2e4559'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(bx, by, bw, bh); ctx.strokeRect(bx, by, bw, bh);
    if (tut.flash > 0) {
      ctx.fillStyle = 'rgba(242,189,29,' + (tut.flash * 0.5).toFixed(3) + ')';
      ctx.fillRect(bx, by, bw, bh);
    }
    ctx.fillStyle = '#f2bd1d';
    ctx.font = '400 17px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillText((tut.i + 1) + '/' + TUT.length + '  ' + st.title, cw / 2, by + 22);
    ctx.font = '500 13px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#f1e7d0';
    for (var li = 0; li < lines.length; li++) ctx.fillText(lines[li], cw / 2, by + 46 + li * 19);
    // timed steps show how long is left
    if (st.wait) {
      ctx.fillStyle = '#1d2d3b'; ctx.fillRect(bx + 3, by + bh - 7, bw - 6, 4);
      ctx.fillStyle = '#f2bd1d'; ctx.fillRect(bx + 3, by + bh - 7, (bw - 6) * clamp(tut.t / st.wait, 0, 1), 4);
    }
    ctx.restore();
  }

  function newRound() {""")

# menu button + wiring
sub("""  $('startBtn').addEventListener('click', function () {""",
"""  $('tutBtn').addEventListener('click', function () {
    if (netRole === 'guest') { openOnline(); return; }
    var was = { mode: mode, mapKind: mapKind, blackout: blackout, squad: squad };
    mode = 'tut'; mapKind = 'cqb'; blackout = false; squad = 1;
    startMatch();
    // the menu keeps what you had picked
    mode = 'tut'; tutRestore = was;
  });
  var tutRestore = null;
  $('startBtn').addEventListener('click', function () {""")
sub("""  function goHome() {
    netGuest = false; netGuestPaused = false;""",
"""  function goHome() {
    netGuest = false; netGuestPaused = false;
    if (tutRestore) { mode = tutRestore.mode; mapKind = tutRestore.mapKind; blackout = tutRestore.blackout; squad = tutRestore.squad; tutRestore = null; MODE = MODES[mode]; }""")
sub("""  syncMenu();
  requestAnimationFrame(frame);""", """  syncMenu();
  syncTutBtn();
  requestAnimationFrame(frame);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read()
a = """        <button class="go" id="quickBtn" type="button">QUICK PLAY ONLINE</button>"""
if a not in h:
    raise SystemExit('HTML PATTERN NOT FOUND')
h = h.replace(a, """        <button class="go" id="tutBtn" type="button">TUTORIAL</button>
""" + a, 1)
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p51 applied')

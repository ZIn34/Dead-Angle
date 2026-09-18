# -*- coding: utf-8 -*-
"""Online play: one host runs the match, a friend joins over WebRTC as P2.

The host's machine is the only simulation. The guest sends its controls (as
a virtual pad) and draws what the host sends back ~20 times a second. PeerJS's
free public broker only introduces the two browsers; the game traffic goes
directly between them.
"""
import io, re, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- naming follows "two people are playing", not "the screen is split" --
lines = s.split('\n')
for i, ln in enumerate(lines):
    if 'splitOn' in ln and ('feed(' in ln or "took it" in ln or 'ran the whole' in ln or ' put ' in ln
                            or 'zone closed' in ln or 'last one standing' in ln or 'locals[1].skin' in ln):
        lines[i] = ln.replace('splitOn', '(locals.length > 1)')
s = '\n'.join(lines)

# ---- who actually won, when the two people are rivals ----------------------
sub("""  var result = null, overCause = '';""",
    """  var result = null, overCause = '';
  var lastWinner = null;              // who closed out a free-for-all""")
sub("""    result = null; overCause = '';

    if (MODE.zone) {""",
    """    result = null; overCause = ''; lastWinner = null;

    if (MODE.zone) {""")
sub("""        if (score[killer.id] >= MODE.target) {""",
    """        if (score[killer.id] >= MODE.target) {
          lastWinner = killer;""")
sub("""        if (killer.level >= LADDER.length) {""",
    """        if (killer.level >= LADDER.length) {
          lastWinner = killer;""")
sub("""        for (var q2 = 0; q2 < locals.length; q2++) if (locals[q2].alive) champ = locals[q2];""",
    """        for (var q2 = 0; q2 < locals.length; q2++) if (locals[q2].alive) champ = locals[q2];
        lastWinner = champ;""")

sub("""  function finish(won, msg, place) {
    var big, small;""",
"""  function finish(won, msg, place) {
    // Two people on opposite sides: each only won if they were the one left.
    var p2 = locals.length > 1 ? locals[1] : null;
    var rivals = !!p2 && p2.team !== player.team;
    var guestWon = rivals ? (won && lastWinner === p2) : won;
    if (rivals) won = won && lastWinner === player;
    if (p2 && p2.ctl && p2.ctl.net) netSendOver(guestWon, msg, place, p2);
    var big, small;""")

# ---- state -----------------------------------------------------------------
sub("""  var locals = [], splitOn = false, splitWant = false;""",
"""  var locals = [], splitOn = false, splitWant = false;
  // online: netRole is 'host' or 'guest' while connected; netGuest is true
  // while this machine is drawing a match the host is running
  var netRole = null, netConn = null, netPeer = null, netGuest = false, netGuestPaused = false;
  var netIn = { ax: [0, 0], aim: null, down: 0, hits: 0 };
  var netGuestSkin = 0, netHostHeld = false;""")

# ---- the host gives the friend P2 ------------------------------------------
sub("""    var sc = splitWant ? splitControls() : null;
    if (splitWant && !sc) feed('split screen needs a <b>controller</b> for player 2', true);
    if (sc) {""",
"""    var online = netRole === 'host' && netConn && netConn.open;
    var sc = online ? null : (splitWant ? splitControls() : null);
    if (!online && splitWant && !sc) feed('split screen needs a <b>controller</b> for player 2', true);
    if (online) {
      var pn = makeEnt(sp[1 % sp.length], true, 'P2');
      pn.local = true; pn.ctl = { net: true }; pn.cam = { x: 0, y: 0 };
      player.name = 'P1';
      ents.push(pn); locals.push(pn);
      netIn = { ax: [0, 0], aim: null, down: 0, hits: 0 };
    }
    if (sc) {""")
sub("""    elHud.classList.toggle('split', splitOn);""",
    """    elHud.classList.toggle('split', splitOn);
    if (locals.length > 1 && locals[1].ctl.net && !MODE.teams && !MODE.zombies) locals[1].skin = netGuestSkin;""")
sub("""    state = 'play';
    syncHud();
  }

  function boardPlane() {""",
"""    state = 'play';
    syncHud();
    if (online) netSendStart(locals[1]);
  }

  function boardPlane() {""")

# ---- the friend's controls arrive as a virtual pad -------------------------
sub("""  function inputFor(e) {
    var c = e.ctl || { any: true, kb: true };""",
"""  function inputFor(e) {
    var c = e.ctl || { any: true, kb: true };
    if (c.net) {
      var n = netIn;
      return {
        any: false, net: true, pad: true, kb: false, touch: false, padOn: true,
        hit: function (i) { var b = 1 << i; if (n.hits & b) { n.hits &= ~b; return true; } return false; },
        down: function (i) { return !!(n.down & (1 << i)); },
        ax: function (i) {
          if (i < 2) return n.ax[i] || 0;
          if (n.aim === null || n.aim === undefined) return 0;
          return i === 2 ? Math.cos(n.aim) : Math.sin(n.aim);
        }
      };
    }""")
sub("""    if (rx || ry) {
      e.ang = aimAssist(e, Math.atan2(ry, rx));""",
"""    if (rx || ry) {
      e.ang = I.net ? Math.atan2(ry, rx) : aimAssist(e, Math.atan2(ry, rx));""")

# ---- host taps: anything the guest needs to see or hear --------------------
sub("""  function spark(x, y, n, color, spd) {""",
"""  function spark(x, y, n, color, spd) {
    if (netRole === 'host' && netHostLive()) netEv.push(['k', Math.round(x), Math.round(y), n, color, spd]);""")
sub("""  function audioEmit(x, y, def, owner) {""",
"""  function audioEmit(x, y, def, owner) {
    if (netRole === 'host' && netHostLive()) netEv.push(['a', Math.round(x), Math.round(y), netDefId(def), owner]);""")
sub("""  function feed(html, mine) {""",
"""  function feed(html, mine) {
    if (netRole === 'host' && netHostLive()) netEv.push(['f', html, !!mine]);""")

# ---- the loop --------------------------------------------------------------
sub("""    if (state === 'play') update(Math.max(dt, 0.0001));
    else uiPad(dt);
    render();""",
"""    if (state === 'play') {
      if (netGuest) guestTick(Math.max(dt, 0.0001));
      else update(Math.max(dt, 0.0001));
    }
    else uiPad(dt);
    if (netRole === 'host') netHostTick(dt);
    render();""")

# guest keys become buttons; host does not auto-pause when it loses focus
sub("""    if (state === 'play') {
      var kp = kbPlayer();""",
"""    if (netGuest && state === 'play') {
      var GB = { 'e': 0, ' ': 0, 'v': 1, 'x': 1, 'r': 2, 'f': 3, 'h': 5, 'g': 6, 'q': 14, '1': 14, '2': 14 };
      if (k === 'escape') { if (netGuestPaused) resume(); else pause(); }
      else if (k === 'm') { muted = !muted; feed(muted ? 'sound <b>off</b>' : 'sound <b>on</b>', true); }
      else if (GB[k] !== undefined && !netGuestPaused && !e.repeat) guestHits |= 1 << GB[k];
      if (['w', 'a', 's', 'd', ' '].indexOf(k) >= 0) e.preventDefault();
      return;
    }
    if (state === 'play') {
      var kp = kbPlayer();""")
sub("""  window.addEventListener('blur', function () { keys = {}; mouse.down = false; if (state === 'play') pause(); });""",
    """  window.addEventListener('blur', function () {
    keys = {}; mouse.down = false;
    if (state === 'play' && !netRole) pause();      // a friend online keeps playing
  });""")

sub("""  function pause() {
    if (state !== 'play') return;""",
"""  function pause() {
    if (netGuest) {                                   // the host's match keeps going
      netGuestPaused = true;
      $('pauseSub').textContent = 'ONLINE \\u00b7 the match keeps running';
      elPaused.hidden = false;
      return;
    }
    if (state !== 'play') return;""")
sub("""  function resume() {
    if (state !== 'paused') return;""",
"""  function resume() {
    if (netGuest) { netGuestPaused = false; elPaused.hidden = true; return; }
    if (state !== 'paused') return;""")
sub("""  function leaveMatch() { goHome(); }""",
"""  function leaveMatch() {
    if (netGuest) { netClose('You left the match.'); return; }
    if (netRole === 'host' && netConn && netConn.open) netSend({ t: 'end', why: 'The host left the match.' });
    goHome();
  }""")
sub("""  function goHome() {
    state = 'menu';""",
"""  function goHome() {
    netGuest = false; netGuestPaused = false;
    $('againBtn').hidden = false;
    state = 'menu';""")
sub("""  $('startBtn').addEventListener('click', startMatch);""",
"""  $('startBtn').addEventListener('click', function () {
    if (netRole === 'guest') { openOnline(); return; }         // the host starts
    startMatch();
  });""")

# the menu says who is connected
sub("""    if (splitWant) {
      var np = padIndices().length;""",
"""    if (netRole === 'host' && netConn && netConn.open) t += '  \\u2014  ONLINE: your friend is connected and drops in with you as P2.' + (squad < 2 && !MODE_TEAMMATES[mode] ? ' Solo: rivals. DUOS: partners.' : '');
    if (netRole === 'guest') t = 'ONLINE: connected. The host picks the mode and starts the match.';
    if (splitWant && !netRole) {
      var np = padIndices().length;""")

# ---- the network module ----------------------------------------------------
sub("""  // ---------------------------------------------------------------- loop""",
r"""  // ---------------------------------------------------------------- online
  var PEER_JS = 'https://cdn.jsdelivr.net/npm/peerjs@1.5.4/dist/peerjs.min.js';
  var netEv = [], netDefs = [], netSendT = 0, netSigs = {}, guestHits = 0, netInT = 0;
  var netQueue = [], guestYou = -1, netLastIn = '';
  var WKEYS = Object.keys(WEAPONS);

  function netStatus(txt) { var el = $('netStatus'); if (el) el.textContent = txt; }
  function netHostLive() {
    return !!(netConn && netConn.open && (state === 'play' || state === 'paused' || state === 'ending')
              && locals.length > 1 && locals[1].ctl && locals[1].ctl.net);
  }
  function netSend(obj) {
    if (!netConn || !netConn.open) return;
    try {
      netConn.send(JSON.stringify(obj, function (k, v) {
        return (typeof v === 'number' && v % 1) ? Math.round(v * 100) / 100 : v;
      }));
    } catch (err) {}
  }
  function netDefId(def) {
    if (def.__nid === undefined) { def.__nid = netDefs.length; netDefs.push(def); def.__new = true; }
    return def.__nid;
  }

  function loadPeer(cb) {
    if (window.Peer) { cb(); return; }
    var sc = document.createElement('script');
    sc.src = PEER_JS;
    sc.onload = cb;
    sc.onerror = function () { netStatus('Could not load the connection library. Check your internet.'); };
    document.head.appendChild(sc);
  }
  function roomCode() {
    var A = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', c = '';
    for (var i = 0; i < 5; i++) c += A.charAt(rnd(A.length));
    return c;
  }
  function netClose(why) {
    var wasGuest = netRole === 'guest';
    try { if (netConn) netConn.close(); } catch (err) {}
    try { if (netPeer) netPeer.destroy(); } catch (err) {}
    netConn = null; netPeer = null; netRole = null;
    $('netCodeBox').hidden = true;
    if (wasGuest && (netGuest || state !== 'menu')) { goHome(); openOnline(); }
    netStatus(why || 'Disconnected.');
    syncMenu();
  }

  function hostGame() {
    netClose('');
    netStatus('Starting...');
    loadPeer(function () {
      var code = roomCode();
      netPeer = new window.Peer('deadangle-' + code);
      netPeer.on('open', function () {
        netRole = 'host';
        $('netCode').textContent = code;
        $('netCodeBox').hidden = false;
        netStatus('Waiting for a friend. Give them this code; they press JOIN and type it in.');
        syncMenu();
      });
      netPeer.on('connection', function (conn) {
        if (netConn && netConn.open) { conn.on('open', function () { conn.close(); }); return; }
        netConn = conn;
        conn.on('open', function () {
          netStatus('Friend connected! Go BACK, pick a mode and start - they drop in as P2.');
          syncMenu();
        });
        conn.on('data', hostReceive);
        conn.on('close', hostLostGuest);
        conn.on('error', hostLostGuest);
      });
      netPeer.on('error', function (err) {
        if (err && err.type === 'unavailable-id') { hostGame(); return; }
        netStatus('Connection problem: ' + (err && err.type ? err.type : 'unknown') + '.');
      });
    });
  }
  function hostLostGuest() {
    netConn = null;
    // whoever was P2 is handed to a bot so the match can carry on
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i];
      if (L.ctl && L.ctl.net) {
        L.local = false; L.bot = true; L.ctl = null; L.skip = L.skip || {};
        L.path = null; L.target = null;
        locals.splice(i, 1);
        if (state === 'play' || state === 'paused') feed('<b>P2</b> disconnected - a bot takes over', true);
        break;
      }
    }
    if (netRole === 'host') netStatus('Your friend left. Still hosting with the same code.');
    syncMenu();
  }
  function hostReceive(raw) {
    var m; try { m = JSON.parse(raw); } catch (err) { return; }
    if (m.t === 'in') {
      netIn.ax = m.ax || [0, 0]; netIn.aim = m.aim; netIn.down = m.down | 0;
      netIn.hits |= m.hits | 0;
    } else if (m.t === 'hi') {
      netGuestSkin = clamp(m.skin | 0, 0, 15);
    }
  }

  function packRegion(src) {
    var out = '', row = [];
    for (var y = 0; y < MAP_H; y++) {
      row.length = 0;
      for (var x = 0; x < MAP_W; x++) row.push(src[y * STRIDE + x]);
      out += String.fromCharCode.apply(null, row);
    }
    return btoa(out);
  }
  function unpackRegion(b64, dst) {
    var str = atob(b64), k = 0;
    for (var y = 0; y < MAP_H; y++) for (var x = 0; x < MAP_W; x++) dst[y * STRIDE + x] = str.charCodeAt(k++);
  }
  function netSendStart(p2) {
    netSigs = {}; netEv = [];
    for (var i = 0; i < netDefs.length; i++) netDefs[i].__new = true;   // a fresh guest needs them all
    netSend({
      t: 'start', mode: mode, mapKind: mapKind, blackout: blackout, squad: squad, difficulty: difficulty,
      w: MAP_W, h: MAP_H, grid: packRegion(grid), mat: packRegion(mat), you: p2.id
    });
  }
  function netSendOver(won, msg, place, p2) {
    var big;
    if (mode === 'br') big = '#' + (won ? 1 : place);
    else big = won ? 'WIN' : 'LOSS';
    netSend({ t: 'over', won: won, big: big, small: mode === 'br' ? 'OF ' + fieldN : '', msg: msg,
              kills: p2.kills || 0, time: matchTime });
  }

  function packEnt(e) {
    var s0 = e.slots[0], s1 = e.slots[1];
    var bits = (e.alive ? 1 : 0) | (e.down ? 2 : 0) | (e.moving ? 4 : 0) |
               (e.air === 'plane' ? 8 : 0) | (e.air === 'chute' ? 16 : 0) | (e.bot ? 32 : 0);
    return [e.id, e.x, e.y, e.ang, e.team, e.skin, bits, e.animT || 0, e.animFire || 0, e.swingT || 0,
            e.throwT || 0, e.meleeT || 0, Math.round(e.hp), e.revT || 0, e.downT || 0, e.respawnT || 0,
            e.level || 0, e.airT || 0, e.name, e.slot,
            s0 ? WKEYS.indexOf(s0.key) : -1, s0 ? s0.ammo : 0, s1 ? WKEYS.indexOf(s1.key) : -1, s1 ? s1.ammo : 0,
            e.reserve, e.meds, e.nades, e.smokes, e.reloadT || 0, e.useT || 0, e.kills || 0];
  }
  function sigOf(list) {
    var h = list.length;
    for (var i = Math.max(0, list.length - 3); i < list.length; i++) h = (h * 31 + (list[i].x | 0) * 7 + (list[i].y | 0)) | 0;
    return h;
  }
  function lootSig() {
    var h = loot.length;
    for (var i = 0; i < loot.length; i++) h = (h * 31 + (loot[i].x | 0) + (loot[i].y | 0) * 7 + (loot[i].ammo | 0)) | 0;
    return h;
  }

  function netHostTick(dt) {
    if (!netHostLive()) { netEv.length = 0; return; }
    netSendT -= dt;
    if (netSendT > 0) return;
    netSendT = 1 / 20;
    var p2 = locals[1];
    var snap = {
      t: 's', hold: state === 'paused',
      e: ents.map(packEnt),
      b: bullets.map(function (b) { return [b.x, b.y, b.vx, b.vy, b.owner]; }),
      f: flashes, im: impacts, sm: smokes,
      n: nades.map(function (g) { return { x: g.x, y: g.y, spin: g.spin, kind: g.kind, fuse: g.fuse, owner: g.owner }; }),
      fl: flags.map(function (f) {
        return { team: f.team, hx: f.hx, hy: f.hy, x: f.x, y: f.y, home: f.home, ping: f.ping, carrier: f.carrier ? f.carrier.id : -1 };
      }),
      se: sectors, z: zone, p: plane,
      so: blackout ? sounds.map(function (q) {
        return { x: q.x, y: q.y, r: q.r, maxR: q.maxR, speed: q.speed, color: q.color, w: q.w, kind: q.kind, owner: q.owner };
      }) : null,
      h: [alive, score[0], score[1], round, roundClock, roundBreak, zombClock, matchTime, fieldN],
      dm: dmgMarks.filter(function (m) { return m.who === p2.id; }),
      ev: netEv
    };
    var ls = lootSig(); if (netSigs.lo !== ls) { netSigs.lo = ls; snap.lo = loot; }
    var ds = sigOf(decals); if (netSigs.dc !== ds) { netSigs.dc = ds; snap.dc = decals; }
    var es = sigOf(deaths); if (netSigs.de !== es) { netSigs.de = es; snap.de = deaths; }
    var cs = sigOf(corpses); if (netSigs.co !== cs) { netSigs.co = cs; snap.co = corpses.slice(-80); }
    var nd = null;
    for (var i = 0; i < netDefs.length; i++) if (netDefs[i].__new) {
      nd = nd || {};
      var d = netDefs[i];
      nd[i] = { maxR: d.maxR, speed: d.speed, color: d.color, w: d.w, aud: d.aud, sample: d.sample, sampleGain: d.sampleGain, rate: d.rate };
      d.__new = false;
    }
    if (nd) snap.defs = nd;
    netSend(snap);
    netEv = [];
  }

  // ---- the guest's side ----
  function joinGame(code) {
    code = String(code || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (code.length !== 5) { netStatus('Room codes are 5 letters and numbers.'); return; }
    netClose('');
    netStatus('Connecting...');
    loadPeer(function () {
      netPeer = new window.Peer();
      netPeer.on('open', function () {
        var conn = netPeer.connect('deadangle-' + code, { reliable: true, serialization: 'raw' });
        netConn = conn;
        var opened = false;
        setTimeout(function () { if (!opened && netConn === conn) netClose('No answer from that code. Check it with your friend.'); }, 12000);
        conn.on('open', function () {
          opened = true;
          netRole = 'guest';
          netSend({ t: 'hi', skin: WALLET.skin });
          netStatus('Connected! Waiting for the host to start a match.');
          syncMenu();
        });
        conn.on('data', guestReceive);
        conn.on('close', function () { if (netConn === conn) netClose('The host closed the game.'); });
        conn.on('error', function () { if (netConn === conn) netClose('Lost the connection.'); });
      });
      netPeer.on('error', function (err) {
        netClose(err && err.type === 'peer-unavailable' ? 'No game with that code. Check it with your friend.'
                                                        : 'Connection problem: ' + (err && err.type ? err.type : 'unknown') + '.');
      });
    });
  }

  function guestReceive(raw) {
    var m; try { m = JSON.parse(raw); } catch (err) { return; }
    if (m.t === 's') { netQueue.push(m); if (netQueue.length > 30) netQueue.splice(0, netQueue.length - 30); }
    else if (m.t === 'start') guestStart(m);
    else if (m.t === 'over') guestOver(m);
    else if (m.t === 'end') { if (netGuest) { goHome(); openOnline(); } netStatus(m.why || 'The match ended.'); }
  }

  function guestStart(m) {
    initAudio();
    matchToken++;
    mode = m.mode; MODE = MODES[mode]; mapKind = m.mapKind; blackout = !!m.blackout;
    squad = m.squad; difficulty = m.difficulty;
    VIEW_R = blackout ? VIEW_BLACKOUT : VIEW_BASE;
    MAP_W = m.w; MAP_H = m.h;
    grid.fill(0); mat.fill(0);
    unpackRegion(m.grid, grid); unpackRegion(m.mat, mat);
    finishMap();
    explored.fill(0);
    ents = []; bullets = []; sounds = []; parts = []; flashes = []; corpses = []; loot = [];
    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = [];
    dmgMarks = []; shake = 0; promptItem = null; zone = null; plane = null;
    locals = []; splitOn = false; player = null; guestYou = m.you; netQueue = [];
    kills = 0; shots = 0; hits = 0; matchTime = 0; score = [0, 0]; result = null;
    charCache = {};
    elFeed.innerHTML = '';
    ['menu', 'over', 'paused', 'shop', 'settings', 'online'].forEach(function (id) { $(id).hidden = true; });
    elHud.hidden = false; elHud.classList.remove('split');
    netGuest = true; netGuestPaused = false;
    state = 'play';
  }

  function guestOver(m) {
    if (!netGuest) return;
    var earned = (m.kills || 0) * 12 + Math.round((m.time || 0) / 6) + (m.won ? 80 : 0);
    WALLET.coins += earned;
    saveWallet();
    state = 'over';
    var tok = matchToken;
    setTimeout(function () {
      if (tok !== matchToken) return;
      $('placeN').textContent = m.big;
      $('placeN').className = m.won ? 'win' : '';
      $('placeL').textContent = m.small || '';
      $('overMsg').textContent = m.msg + '  +' + earned + ' credits.';
      $('stKills').textContent = m.kills || 0;
      $('stTime').textContent = fmtTime(m.time || 0);
      $('stAcc').textContent = '--';
      $('againBtn').hidden = true;                  // the host starts the next one
      elHud.hidden = true; elPaused.hidden = true;
      elOver.hidden = false;
    }, 850);
  }

  function netEnt(a) {
    var id = a[0], e = ents[id];
    if (!e) {
      e = makeEnt({ x: 0, y: 0 }, true, a[18]);
      e.id = id; e.x = a[1]; e.y = a[2];
      ents[id] = e;
    }
    if (Math.abs(a[1] - e.x) + Math.abs(a[2] - e.y) > 90) { e.x = a[1]; e.y = a[2]; }
    e.tx = a[1]; e.ty = a[2];
    e.ang = a[3]; e.team = a[4]; e.skin = a[5];
    var bits = a[6];
    e.alive = !!(bits & 1); e.down = !!(bits & 2); e.moving = !!(bits & 4);
    e.air = (bits & 8) ? 'plane' : ((bits & 16) ? 'chute' : null); e.bot = !!(bits & 32);
    e.animT = a[7]; e.animFire = a[8]; e.swingT = a[9]; e.throwT = a[10]; e.meleeT = a[11];
    e.hp = a[12]; e.revT = a[13]; e.downT = a[14]; e.respawnT = a[15]; e.level = a[16]; e.airT = a[17];
    e.name = a[18]; e.slot = a[19];
    e.slots[0] = a[20] >= 0 ? { key: WKEYS[a[20]], ammo: a[21] } : null;
    e.slots[1] = a[22] >= 0 ? { key: WKEYS[a[22]], ammo: a[23] } : null;
    e.reserve = a[24]; e.meds = a[25]; e.nades = a[26]; e.smokes = a[27];
    e.reloadT = a[28]; e.useT = a[29]; e.kills = a[30];
  }

  function applySnap(m) {
    var i;
    for (i = 0; i < m.e.length; i++) netEnt(m.e[i]);
    if (!player && ents[guestYou]) {
      player = ents[guestYou];
      player.local = true; player.ctl = { any: true, kb: true }; player.cam = cam;
      cam.x = player.x; cam.y = player.y;
      locals = [player];
    }
    bullets = m.b.map(function (b) { return { x: b[0], y: b[1], vx: b[2], vy: b[3], owner: b[4], life: 1 }; });
    flashes = m.f || []; impacts = m.im || []; smokes = m.sm || []; nades = m.n || [];
    flags = (m.fl || []).map(function (f) { f.carrier = f.carrier >= 0 ? ents[f.carrier] : null; return f; });
    sectors = m.se || []; zone = m.z; plane = m.p;
    if (m.so) sounds = m.so.map(function (q) { q.heard = {}; return q; });
    var h = m.h;
    alive = h[0]; score = [h[1], h[2]]; round = h[3]; roundClock = h[4]; roundBreak = h[5];
    zombClock = h[6]; matchTime = h[7]; fieldN = h[8];
    if (player) kills = player.kills || 0;
    dmgMarks = m.dm || [];
    if (m.lo) loot = m.lo;
    if (m.dc) decals = m.dc;
    if (m.de) deaths = m.de;
    if (m.co) corpses = m.co;
    if (m.defs) for (var k in m.defs) netDefs[k] = m.defs[k];
    netHostHeld = !!m.hold;
    var ev = m.ev || [];
    for (i = 0; i < ev.length; i++) {
      var q = ev[i];
      if (q[0] === 'k') spark(q[1], q[2], q[3], q[4], q[5]);
      else if (q[0] === 'a') { if (netDefs[q[3]]) audioEmit(q[1], q[2], netDefs[q[3]], q[4]); }
      else if (q[0] === 'f') feed(q[1], q[2]);
    }
  }

  function guestTick(dt) {
    pollPad();
    while (netQueue.length) applySnap(netQueue.shift());
    if (!player) return;
    var i;
    // glide everyone toward where the host last put them
    var kk = Math.min(1, dt * 16);
    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e || e.tx === undefined) continue;
      e.x += (e.tx - e.x) * kk; e.y += (e.ty - e.y) * kk;
    }
    for (var p = parts.length - 1; p >= 0; p--) {
      var pt = parts[p];
      pt.life -= dt;
      if (pt.life <= 0) { parts.splice(p, 1); continue; }
      pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.vx *= 0.9; pt.vy *= 0.9;
    }
    for (i = decals.length - 1; i >= 0; i--) decals[i].t += dt;
    for (i = impacts.length - 1; i >= 0; i--) impacts[i].t += dt;
    for (i = 0; i < deaths.length; i++) deaths[i].t += dt;
    for (i = flashes.length - 1; i >= 0; i--) { flashes[i].t -= dt; if (flashes[i].t <= 0) flashes.splice(i, 1); }
    for (i = 0; i < bullets.length; i++) { bullets[i].x += bullets[i].vx * dt; bullets[i].y += bullets[i].vy * dt; }
    for (i = dmgMarks.length - 1; i >= 0; i--) { dmgMarks[i].t -= dt; if (dmgMarks[i].t <= 0) dmgMarks.splice(i, 1); }

    updateMouseWorld();
    var lerp = 1 - Math.pow(0.0001, dt);
    var tx = player.x, ty = player.y;
    if (!touchMode && !padActive()) {
      tx += clamp(mouse.wx - player.x, -110, 110) * 0.2;
      ty += clamp(mouse.wy - player.y, -110, 110) * 0.2;
    }
    cam.x += (tx - cam.x) * lerp; cam.y += (ty - cam.y) * lerp;
    syncHud();

    // controls out, as a virtual pad
    var mx = 0, my = 0, aim = null, down = 0, hitsNow = guestHits;
    guestHits = 0;
    if (!netGuestPaused) {
      if (pad) {
        mx = padAxis(0); my = padAxis(1);
        var rx = padAxis(2), ry = padAxis(3);
        if (rx || ry) aim = Math.atan2(ry, rx);
        var PB = [0, 1, 2, 3, 5, 6, 14, 15, 12];
        for (i = 0; i < PB.length; i++) if (padHit(PB[i])) hitsNow |= 1 << (PB[i] === 15 ? 14 : (PB[i] === 12 ? 3 : PB[i]));
        if (padHit(9)) pause();
        if (padDown(4)) down |= 1 << 4;
        if (padDown(7)) down |= 1 << 7;
      }
      if (!mx && !my) {
        if (keys['a']) mx -= 1; if (keys['d']) mx += 1;
        if (keys['w']) my -= 1; if (keys['s']) my += 1;
        var ml = Math.sqrt(mx * mx + my * my);
        if (ml > 1) { mx /= ml; my /= ml; }
      }
      if (aim === null) {
        if (padActive()) { if (mx || my) aim = Math.atan2(my, mx); }
        else aim = Math.atan2(mouse.wy - player.y, mouse.wx - player.x);
      }
      if (keys['shift']) down |= 1 << 4;
      if (mouse.down) down |= 1 << 7;
    } else if (pad && padHit(9)) resume();
    if (aim === null) aim = player.ang;
    netInT -= dt;
    var pkt = { t: 'in', ax: [mx, my], aim: aim, down: down, hits: hitsNow };
    var key = mx.toFixed(2) + my.toFixed(2) + aim.toFixed(2) + down;
    if (hitsNow || key !== netLastIn || netInT <= 0) {
      netSend(pkt);
      netLastIn = key; netInT = 0.1;
    }
  }

  // ---- the ONLINE screen ----
  function openOnline() {
    elMenu.hidden = true;
    $('online').hidden = false;
    if (!netRole) netStatus('One of you hosts, the other joins with the code. Works best on a normal home connection.');
  }
  $('onlineBtn').addEventListener('click', openOnline);
  $('netHost').addEventListener('click', hostGame);
  $('netJoin').addEventListener('click', function () { joinGame($('netJoinCode').value); });
  $('netJoinCode').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') joinGame(this.value);
  });
  $('netBack').addEventListener('click', function () { $('online').hidden = true; elMenu.hidden = false; syncMenu(); });
  $('netLeave').addEventListener('click', function () { netClose('Disconnected.'); });

  // ---------------------------------------------------------------- loop""")

# the guest's own menu button goes to the online screen, not a solo match
sub("""    $('startBtn').textContent = mode === 'br' ? 'DROP IN'""",
    """    if (netRole === 'guest') { $('startBtn').textContent = 'WAITING FOR HOST'; return; }
    $('startBtn').textContent = mode === 'br' ? 'DROP IN'""")

# pause screen / results for the guest, and the host's paused notice
sub("""  function renderDropHint() {""",
"""  function renderHostHold() {
    if (!netGuest || !netHostHeld) return;
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '400 20px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillStyle = '#f2bd1d';
    ctx.fillText('HOST PAUSED', cw / 2, ch * 0.3);
    ctx.restore();
  }

  function renderDropHint() {""")
sub("""    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    renderDropHint();""",
"""    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    renderDropHint();
    renderHostHold();""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ================================================================ html ======
h = io.open(H, encoding='utf-8').read(); ho = h
def hsub(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

hsub("""        <button class="go ghost" id="shopBtn" type="button">""",
     """        <button class="go ghost" id="onlineBtn" type="button">PLAY ONLINE</button>
        <button class="go ghost" id="shopBtn" type="button">""")

hsub("""  <div class="screen" id="settings" hidden>""",
"""  <div class="screen" id="online" hidden>
    <div class="panel">
      <div class="brand">
        <h2 class="ptitle">ONLINE</h2>
        <div class="rule"></div>
        <div class="tag">you and a friend, anywhere</div>
      </div>
      <div class="pbtns">
        <button class="go" id="netHost" type="button">HOST A GAME</button>
        <div class="netcode" id="netCodeBox" hidden>ROOM CODE<b id="netCode">-----</b></div>
        <div class="joinrow">
          <input id="netJoinCode" maxlength="5" placeholder="CODE" autocomplete="off" spellcheck="false" aria-label="Room code">
          <button class="go ghost" id="netJoin" type="button">JOIN</button>
        </div>
      </div>
      <p class="modedesc" id="netStatus">One of you hosts, the other joins with the code.</p>
      <div class="pbtns">
        <button class="go ghost" id="netLeave" type="button">DISCONNECT</button>
        <button class="go ghost" id="netBack" type="button">BACK</button>
      </div>
    </div>
  </div>

  <div class="screen" id="settings" hidden>""")

hsub(""".ptitle{""", """.netcode{font-family:var(--font-m);font-size:11px;letter-spacing:.3em;color:var(--khaki);text-align:center}
.netcode b{display:block;margin-top:6px;font-family:var(--font-x);font-weight:400;font-size:42px;letter-spacing:.22em;text-indent:.22em;color:var(--gold);-webkit-text-stroke:2px var(--out);paint-order:stroke fill;text-shadow:3px 3px 0 var(--out)}
.joinrow{display:flex;gap:10px;align-items:center;justify-content:center}
.joinrow input{width:150px;padding:11px 12px;font-family:var(--font-x);font-size:18px;letter-spacing:.3em;text-indent:.3em;text-transform:uppercase;text-align:center;background:var(--paper);color:var(--out);border:3px solid var(--out);border-radius:4px}
.ptitle{""")

io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p47 applied')

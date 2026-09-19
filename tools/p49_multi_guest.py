# -*- coding: utf-8 -*-
"""Online for more than two: one host, many guests, joining mid-match.

A guest who arrives takes over a bot's body (in battle royale, only one still
riding the plane). If they leave, a bot takes the body back. Every guest gets
their own results.
"""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

def region(start, end, new):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + new + s[b:]

# ---- state ----------------------------------------------------------------
sub("""  var netRole = null, netConn = null, netPeer = null, netGuest = false, netGuestPaused = false;
  var netIn = { ax: [0, 0], aim: null, down: 0, hits: 0 };""",
"""  var netRole = null, netConn = null, netPeer = null, netGuest = false, netGuestPaused = false;
  // host side: everyone connected to us. { conn, name, skin, uid, party, in, ent, sigs }
  var netGuests = [], netPublic = false, netCode = '';
  var acctName = '';                 // the signed-in username, if any
  var NET_MAX = 8;                   // people in one match, host included
  // on this machine (not merely human - remote guests are local to the host's sim)
  function onHere(e) { return !!(e && e.local && !(e.ctl && e.ctl.net)); }""")

# ---- sound, stats and camera are for this machine's own players ------------
sub("""    var lis = (oe && oe.local) ? oe : nearestLocal(x, y);""",
    """    var lis = onHere(oe) ? oe : nearestLocal(x, y);""")
sub("""    var mine = !!(oe && oe.local);""", """    var mine = onHere(oe);""")
sub("""    var best = player, bd = 1e18;
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i], d""",
"""    var best = player, bd = 1e18;
    for (var i = 0; i < locals.length; i++) {
      if (!onHere(locals[i])) continue;
      var L = locals[i], d""")
sub("""    if (e.local) shots++;""", """    if (onHere(e)) shots++;""")
sub("""            if (ents[b.owner] && ents[b.owner].local) hits++;""", """            if (onHere(ents[b.owner])) hits++;""")
sub("""    if (killer && killer.local && killer !== e) {
      kills++;""", """    if (killer && killer.local && killer !== e) {
      if (onHere(killer)) kills++;""")

# ---- match start: bots first, then guests step into bots -------------------
sub("""    var online = netRole === 'host' && netConn && netConn.open;
    var sc = online ? null : (splitWant ? splitControls() : null);
    if (!online && splitWant && !sc) feed('split screen needs a <b>controller</b> for player 2', true);
    if (online) {
      var pn = makeEnt(sp[1 % sp.length], true, 'P2');
      pn.local = true; pn.ctl = { net: true }; pn.cam = { x: 0, y: 0 };
      player.name = 'P1';
      ents.push(pn); locals.push(pn);
      netIn = { ax: [0, 0], aim: null, down: 0, hits: 0 };
    }
    if (sc) {""",
"""    var online = netRole === 'host' && netGuests.length > 0;
    var sc = online ? null : (splitWant ? splitControls() : null);
    if (!online && splitWant && !sc) feed('split screen needs a <b>controller</b> for player 2', true);
    if (netRole === 'host') player.name = acctName || 'HOST';
    for (var gq = 0; gq < netGuests.length; gq++) netGuests[gq].ent = null;
    if (sc) {""")
sub("""    if (locals.length > 1 && locals[1].ctl.net && !MODE.teams && !MODE.zombies) locals[1].skin = netGuestSkin;""", "")
sub("""    spawnLoot(sp);
    plane = null;""",
"""    spawnLoot(sp);
    // friends in the lobby step into bots' bodies before the plane boards
    if (netRole === 'host') for (var gi = 0; gi < netGuests.length; gi++) admitGuest(netGuests[gi], true);
    plane = null;""")
sub("""    state = 'play';
    syncHud();
    if (online) netSendStart(locals[1]);
  }""",
"""    state = 'play';
    syncHud();
    if (netRole === 'host') for (var gs = 0; gs < netGuests.length; gs++) if (netGuests[gs].ent) netSendTo(netGuests[gs], startMsg(netGuests[gs]));
    lobbyTouch();
  }""")

# ---- results for each person ------------------------------------------------
sub("""    // Two people on opposite sides: each only won if they were the one left.
    var p2 = locals.length > 1 ? locals[1] : null;
    var rivals = !!p2 && p2.team !== player.team;
    var guestWon = rivals ? (won && lastWinner === p2) : won;
    if (rivals) won = won && lastWinner === player;
    if (p2 && p2.ctl && p2.ctl.net) netSendOver(guestWon, msg, place, p2);""",
"""    // With several people playing, each wins or loses for their own side.
    var hostSide = won;
    if (locals.length > 1) won = wonFor(player, hostSide);
    for (var gz = 0; gz < netGuests.length; gz++) {
      var gg = netGuests[gz];
      if (gg.ent) netSendOver(gg, wonFor(gg.ent, hostSide), msg, gg.ent.alive ? 1 : (gg.ent.place || place));
    }""")
sub("""  function finish(won, msg, place) {""",
"""  // `won` arrives from the host's side of things; turn it into this person's.
  function wonFor(e, hostWon) {
    if (MODE.teams || MODE.zombies) return e.team === player.team ? hostWon : !hostWon;
    if (!lastWinner) return false;
    return lastWinner === e || (squad > 1 && lastWinner.team === e.team);
  }
  function finish(won, msg, place) {""")
# battle royale: note where each person finished
sub("""    if (e.local && !anyLocalAlive()) {""",
    """    if (e.local) e.place = alive + 1;
    if (e.local && !anyLocalAlive()) {""")

# ---- a guest's controls -------------------------------------------------------
sub("""    if (c.net) {
      var n = netIn;""", """    if (c.net) {
      var n = c.net.in;""")

# ---- the host's side of the network -----------------------------------------
region("  function netHostLive() {", "  // ---- the guest's side ----", r"""  function netHostLive() {
    if (netRole !== 'host' || !(state === 'play' || state === 'paused' || state === 'ending')) return false;
    for (var i = 0; i < netGuests.length; i++) if (netGuests[i].ent) return true;
    return false;
  }
  function netStr(obj) {
    return JSON.stringify(obj, function (k, v) {
      return (typeof v === 'number' && v % 1) ? Math.round(v * 100) / 100 : v;
    });
  }
  // guest -> host (the guest has a single connection)
  function netSend(obj) {
    if (!netConn || !netConn.open) return;
    try { netConn.send(netStr(obj)); netStat.sent++; } catch (err) { netStat.err = String(err && err.message || err); }
  }
  function netSendTo(g, objOrStr) {
    if (!g.conn || !g.conn.open) return;
    try { g.conn.send(typeof objOrStr === 'string' ? objOrStr : netStr(objOrStr)); netStat.sent++; }
    catch (err) { netStat.err = String(err && err.message || err); }
  }
  function netSendAll(obj) { var str = netStr(obj); for (var i = 0; i < netGuests.length; i++) netSendTo(netGuests[i], str); }
  function netDefId(def) {
    if (def.__nid === undefined) { def.__nid = netDefs.length; netDefs.push(def); }
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
    if (netRole === 'host') netSendAll({ t: 'end', why: 'The host closed the party.', bye: true });
    for (var i = 0; i < netGuests.length; i++) { try { netGuests[i].conn.close(); } catch (err) {} }
    netGuests = [];
    lobbyDrop();
    try { if (netConn) netConn.close(); } catch (err) {}
    try { if (netPeer) netPeer.destroy(); } catch (err) {}
    netConn = null; netPeer = null; netRole = null; netPublic = false; netCode = '';
    $('netCodeBox').hidden = true;
    if (wasGuest && (netGuest || state !== 'menu')) { goHome(); openOnline(); }
    netStatus(why || 'Disconnected.');
    partyRender();
    syncMenu();
  }

  // Open a room. `then` runs once the room code is live.
  function hostGame(then) {
    if (netRole === 'host' && netPeer && netCode) { if (typeof then === 'function') then(); return; }
    netClose('');
    netStatus('Starting...');
    loadPeer(function () {
      var code = roomCode();
      netPeer = new window.Peer('deadangle-' + code);
      netPeer.on('open', function () {
        netRole = 'host'; netCode = code;
        $('netCode').textContent = code;
        $('netCodeBox').hidden = false;
        netStatus('Party open. Friends join with this code, or invite them from your friends list.');
        partyRender();
        syncMenu();
        if (typeof then === 'function') then();
      });
      netPeer.on('connection', function (conn) {
        var g = { conn: conn, name: 'PLAYER', skin: 0, uid: '', party: true, ent: null, sigs: {},
                  in: { ax: [0, 0], aim: null, down: 0, hits: 0 } };
        conn.on('data', function (raw) { hostReceive(g, raw); });
        conn.on('close', function () { hostLostGuest(g); });
        conn.on('error', function () { hostLostGuest(g); });
      });
      netPeer.on('error', function (err) {
        if (err && err.type === 'unavailable-id') { netRole = null; hostGame(then); return; }
        netStatus('Connection problem: ' + (err && err.type ? err.type : 'unknown') + '.');
      });
    });
  }
  function hostLostGuest(g) {
    var i = netGuests.indexOf(g);
    if (i < 0) return;
    netGuests.splice(i, 1);
    var L = g.ent;
    if (L) {
      // a bot takes the body back so the match can carry on
      L.local = false; L.bot = true; L.ctl = null; L.skip = L.skip || {};
      L.path = null; L.target = null;
      var li = locals.indexOf(L);
      if (li >= 0) locals.splice(li, 1);
      if (state === 'play' || state === 'paused') feed('<b>' + g.name + '</b> left - a bot takes over', false);
      g.ent = null;
    }
    partyBroadcast();
    partyRender();
    lobbyTouch();
    syncMenu();
  }
  function humansIn() { return 1 + netGuests.length; }
  function hostReceive(g, raw) {
    var m; try { m = JSON.parse(raw); } catch (err) { return; }
    if (m.t === 'in') {
      g.in.ax = m.ax || [0, 0]; g.in.aim = m.aim; g.in.down = m.down | 0;
      g.in.hits |= m.hits | 0;
    } else if (m.t === 'hi') {
      g.name = String(m.name || 'PLAYER').replace(/[^A-Za-z0-9_]/g, '').slice(0, 16) || 'PLAYER';
      g.skin = clamp(m.skin | 0, 0, 15); g.uid = String(m.uid || ''); g.party = !m.pub;
      if (humansIn() >= NET_MAX || (m.pub && !netPublic)) {
        netSendTo(g, { t: 'full' });
        setTimeout(function () { try { g.conn.close(); } catch (err) {} }, 300);
        return;
      }
      netGuests.push(g);
      feed('<b>' + g.name + '</b> joined', true);
      if (state === 'play' || state === 'paused') {
        if (admitGuest(g, false)) netSendTo(g, startMsg(g));
        else netSendTo(g, { t: 'wait', why: 'Match in progress - you will be in the next one.' });
      }
      partyBroadcast();
      partyRender();
      lobbyTouch();
      syncMenu();
    }
  }

  // Put a guest into the match by taking over a bot. Friends go to the host's
  // side where they can; in battle royale only a body still on the plane will do.
  function admitGuest(g, atStart) {
    if (g.ent) return true;
    var hum = {}, i;
    for (i = 0; i < locals.length; i++) hum[locals[i].team] = (hum[locals[i].team] || 0) + 1;
    var best = null, bestScore = -1e9;
    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.bot || isZombie(e)) continue;
      if (mode === 'br' && !atStart && e.air !== 'plane') continue;
      if (mode === 'br' && !e.alive) continue;
      var sc2 = -(hum[e.team] || 0) * 10 + (e.alive ? 2 : 0) + Math.random();
      if (g.party && e.team === player.team) sc2 += 50;
      if (sc2 > bestScore) { bestScore = sc2; best = e; }
    }
    if (!best) return false;
    best.bot = false; best.local = true; best.ctl = { net: g };
    best.cam = { x: best.x, y: best.y };
    best.name = g.name; best.target = null; best.path = null;
    if (!MODE.teams && !MODE.zombies) { best.skin = g.skin; charCache = {}; }
    locals.push(best);
    g.ent = best; g.sigs = {};
    g.in = { ax: [0, 0], aim: null, down: 0, hits: 0 };
    if (!atStart) feed('<b>' + g.name + '</b> dropped in', true);
    return true;
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
  var mapPack = null;
  function startMsg(g) {
    if (!mapPack || mapPack.token !== matchToken) mapPack = { token: matchToken, grid: packRegion(grid), mat: packRegion(mat) };
    g.sigs = {}; g.defsSent = 0;
    return { t: 'start', mode: mode, mapKind: mapKind, blackout: blackout, squad: squad, difficulty: difficulty,
             w: MAP_W, h: MAP_H, grid: mapPack.grid, mat: mapPack.mat, you: g.ent.id };
  }
  function netSendOver(g, won, msg, place) {
    var big = mode === 'br' ? '#' + place : (won ? 'WIN' : 'LOSS');
    netSendTo(g, { t: 'over', won: won, big: big, small: mode === 'br' ? 'OF ' + fieldN : '', msg: msg,
                   kills: g.ent.kills || 0, time: matchTime });
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
    lobbyTick(dt);
    if (!netHostLive()) { netEv.length = 0; return; }
    netSendT -= dt;
    if (netSendT > 0) return;
    netSendT = 1 / 20;
    // everything everyone sees, serialised once
    var shared = netStr({
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
      ev: netEv
    });
    var ls = lootSig(), ds = sigOf(decals), es = sigOf(deaths), cs = sigOf(corpses);
    for (var gi = 0; gi < netGuests.length; gi++) {
      var g = netGuests[gi];
      if (!g.ent) continue;
      // what this one person still needs: their own hit marks, and any lists
      // that changed since we last sent them
      var x = { dm: dmgMarks.filter(function (m) { return m.who === g.ent.id; }) };
      if (g.sigs.lo !== ls) { g.sigs.lo = ls; x.lo = loot; }
      if (g.sigs.dc !== ds) { g.sigs.dc = ds; x.dc = decals; }
      if (g.sigs.de !== es) { g.sigs.de = es; x.de = deaths; }
      if (g.sigs.co !== cs) { g.sigs.co = cs; x.co = corpses.slice(-80); }
      if ((g.defsSent || 0) < netDefs.length) {
        x.defs = {};
        for (var k = g.defsSent || 0; k < netDefs.length; k++) {
          var d = netDefs[k];
          x.defs[k] = { maxR: d.maxR, speed: d.speed, color: d.color, w: d.w, aud: d.aud, sample: d.sample, sampleGain: d.sampleGain, rate: d.rate };
        }
        g.defsSent = netDefs.length;
      }
      netSendTo(g, shared.slice(0, -1) + ',"x":' + netStr(x) + '}');
    }
    netEv = [];
  }

  // who is in the party, for everyone's screen
  function partyNames() {
    var n = [acctName || 'HOST'];
    for (var i = 0; i < netGuests.length; i++) if (netGuests[i].party) n.push(netGuests[i].name);
    return n;
  }
  function partyBroadcast() { if (netRole === 'host') netSendAll({ t: 'party', names: partyNames(), code: netCode }); }
  var partyList = [];
  function partyRender() {
    var el = $('partyList');
    if (!el) return;
    var names = netRole === 'host' ? partyNames() : (netRole === 'guest' ? partyList : []);
    el.innerHTML = '';
    names.forEach(function (nm, i) {
      var d = document.createElement('div');
      d.className = 'prow';
      d.textContent = (i === 0 ? '★ ' : '') + nm;
      el.appendChild(d);
    });
    el.hidden = !names.length;
  }

  // Public-match hooks; the accounts module fills these in when it loads.
  var lobbyTouch = function () {}, lobbyDrop = function () {}, lobbyTick = function () {};

""")

# ---- the guest joins with a name, and can be told the room is full ---------
region("  function joinGame(code) {", "  function guestReceive(raw) {", r"""  // pub: joining a stranger's public match. onFail: called instead of just
  // reporting, so Quick Play can try the next one.
  function joinGame(code, pub, onFail) {
    code = String(code || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (code.length !== 5) { netStatus('Room codes are 5 letters and numbers.'); return; }
    netClose('');
    netStatus('Connecting...');
    var failed = false;
    function fail(msg) {
      if (failed) return;
      failed = true;
      netClose(msg);
      if (onFail) onFail(msg);
    }
    loadPeer(function () {
      netPeer = new window.Peer();
      netPeer.on('open', function () {
        var conn = netPeer.connect('deadangle-' + code, { reliable: true, serialization: 'raw' });
        netConn = conn;
        var opened = false;
        setTimeout(function () { if (!opened && netConn === conn) fail('No answer from that code. Check it with your friend.'); }, 12000);
        conn.on('open', function () {
          opened = true;
          netRole = 'guest'; netCode = code;
          netSend({ t: 'hi', skin: WALLET.skin, name: acctName || 'PLAYER', uid: acctUid(), pub: !!pub });
          netStatus(pub ? 'Joining a match...' : 'Connected! Waiting for the host to start a match.');
          syncMenu();
        });
        conn.on('data', guestReceive);
        conn.on('close', function () { if (netConn === conn) { if (!opened) fail('Could not connect.'); else netClose('The host closed the game.'); } });
        conn.on('error', function () { if (netConn === conn) fail('Lost the connection.'); });
      });
      netPeer.on('error', function (err) {
        fail(err && err.type === 'peer-unavailable' ? 'No game with that code. Check it with your friend.'
                                                    : 'Connection problem: ' + (err && err.type ? err.type : 'unknown') + '.');
      });
    });
  }
  function acctUid() { return (window.firebase && firebase.auth && firebase.apps.length && firebase.auth().currentUser) ? firebase.auth().currentUser.uid : ''; }

""")
sub("""    if (m.t === 's') { netQueue.push(m); if (netQueue.length > 30) netQueue.splice(0, netQueue.length - 30); }""",
"""    if (m.t === 's') {
      if (m.x) { for (var xk in m.x) m[xk] = m.x[xk]; }
      netQueue.push(m); if (netQueue.length > 30) netQueue.splice(0, netQueue.length - 30);
    }
    else if (m.t === 'party') { partyList = m.names || []; partyRender(); }
    else if (m.t === 'wait') netStatus(m.why);
    else if (m.t === 'full') { netClose('That match is full.'); if (quickFail) quickFail(); }""")
sub("""    else if (m.t === 'end') { if (netGuest) { goHome(); openOnline(); } netStatus(m.why || 'The match ended.'); }""",
    """    else if (m.t === 'end') {
      if (netGuest) { goHome(); openOnline(); }
      if (m.bye) netClose(m.why); else netStatus(m.why || 'The match ended.');
    }""")
sub("""  var netQueue = [], guestYou = -1, netLastIn = '';""",
    """  var netQueue = [], guestYou = -1, netLastIn = '', quickFail = null;""")

# ---- leaving ----------------------------------------------------------------
sub("""    if (netRole === 'host' && netConn && netConn.open) netSend({ t: 'end', why: 'The host left the match.' });
    goHome();""",
"""    if (netRole === 'host') hostEndMatch('The host left the match.');
    goHome();""")
sub("""  function netHostLive() {""",
"""  // The host stops playing: friends go back to the party, strangers are let go.
  function hostEndMatch(why) {
    for (var i = netGuests.length - 1; i >= 0; i--) {
      var g = netGuests[i];
      if (g.party) netSendTo(g, { t: 'end', why: why });
      else { netSendTo(g, { t: 'end', why: why, bye: true }); try { g.conn.close(); } catch (err) {} netGuests.splice(i, 1); }
      g.ent = null;
    }
    netPublic = false;
    lobbyDrop();
    partyBroadcast(); partyRender();
  }
  function netHostLive() {""")

# the results screen's HOME ends a public match for the strangers too
sub("""  $('homeBtn').addEventListener('click', goHome);""",
    """  $('homeBtn').addEventListener('click', function () {
    if (netRole === 'host' && netPublic) hostEndMatch('The host left.');
    goHome();
  });""")

# menu text
sub("""    if (netRole === 'host' && netConn && netConn.open) t += '  \\u2014  ONLINE: your friend is connected and drops in with you as P2.' + (squad < 2 && !MODE_TEAMMATES[mode] ? ' Solo: rivals. DUOS: partners.' : '');""",
    """    if (netRole === 'host' && netGuests.length) t += '  \\u2014  PARTY: ' + netGuests.length + (netGuests.length > 1 ? ' friends' : ' friend') + ' will drop in with you.' + (squad < 2 && !MODE_TEAMMATES[mode] ? ' Solo: rivals. DUOS: partners.' : '');""")

# the old single-guest checks elsewhere
sub("""    net: function () {
      return { role: netRole, guest: netGuest, open: !!(netConn && netConn.open),""",
    """    net: function () {
      return { role: netRole, guest: netGuest, open: !!(netConn && netConn.open), guests: netGuests.map(function (g) { return g.name + (g.ent ? '@' + g.ent.id : ''); }),""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p49 applied')

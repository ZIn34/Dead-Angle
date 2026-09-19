# -*- coding: utf-8 -*-
"""CrazyGames mode: their SDK, their accounts and saves, their room invites.

Everything is guarded by CG_MODE (set only by the CrazyGames build) or by the
SDK actually being there, so the GitHub build behaves exactly as before.
"""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b, n=1):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, n)

# ---- storage: CrazyGames' data module when present (follows their account)
sub("""  function loadWallet() {""",
"""  var CG_MODE = window.DEAD_ANGLE_PLATFORM === 'crazygames';
  var CG = null;                          // the CrazyGames SDK, once it is ready
  function storeGet(k) {
    try {
      if (CG && CG.data) { var v = CG.data.getItem(k); if (v !== null && v !== undefined) return v; }
      return localStorage.getItem(k);
    } catch (err) { return null; }
  }
  function storeSet(k, v) {
    try { if (CG && CG.data) CG.data.setItem(k, v); } catch (err) {}
    try { localStorage.setItem(k, v); } catch (err) {}
  }
  function loadWallet() {""")
sub("""      var raw = localStorage.getItem('earshot.wallet');""", """      var raw = storeGet('earshot.wallet');""")
sub("""    try { localStorage.setItem('earshot.wallet', JSON.stringify(WALLET)); } catch (err) {}
    if (typeof cloudWallet === 'function') cloudWallet();""",
    """    storeSet('earshot.wallet', JSON.stringify(WALLET));
    if (typeof cloudWallet === 'function') cloudWallet();""")
sub("""      var raw = localStorage.getItem('earshot.settings');""", """      var raw = storeGet('earshot.settings');""")
sub("""    try { localStorage.setItem('earshot.settings', JSON.stringify(SET)); } catch (err) {}""",
    """    storeSet('earshot.settings', JSON.stringify(SET));""")
sub("""    try { localStorage.setItem('earshot.tutDone', '1'); } catch (err) {}""", """    storeSet('earshot.tutDone', '1');""")
sub("""    try { done = localStorage.getItem('earshot.tutDone') === '1'; } catch (err) {}""",
    """    done = storeGet('earshot.tutDone') === '1';""")

# ---- CrazyGames names can have dots in them
sub("""      g.name = String(m.name || 'PLAYER').replace(/[^A-Za-z0-9_]/g, '').slice(0, 16) || 'PLAYER';""",
    """      g.name = String(m.name || 'PLAYER').replace(/[^A-Za-z0-9_.]/g, '').slice(0, 20) || 'PLAYER';""")

# ---- no Firebase accounts on CrazyGames: only a silent anonymous sign-in,
# used for nothing but listing public matches
sub("""  function onAuth(user) {
    fbUser = user || null;""",
"""  function onAuth(user) {
    if (CG_MODE) { fbUser = user || null; return; }
    fbUser = user || null;""")
sub("""  function quickPlay() {
    if (!fbUser || !acctName) { openAccount('Log in to play online.'); return; }""",
"""  function quickPlay() {
    if (CG_MODE && !fbUser) {
      openOnline();
      quickStatus('Connecting...');
      loadFirebase(function () {
        if (fbAuth.currentUser) { fbUser = fbAuth.currentUser; quickPlay(); return; }
        fbAuth.signInAnonymously().then(function (c) { fbUser = c.user; quickPlay(); })
          .catch(function (err) { quickStatus(errText(err)); });
      });
      return;
    }
    if (!CG_MODE && (!fbUser || !acctName)) { openAccount('Log in to play online.'); return; }""")
sub("""    if (c === 'permission-denied') return 'The game database is not set up yet (Firestore rules).';""",
    """    if (c === 'permission-denied') return 'The game database is not set up yet (Firestore rules).';
    if (c === 'auth/admin-restricted-operation') return 'Quick Play needs Anonymous sign-in switched on in Firebase.';""")
sub("""  setInterval(function () { if (!$('friends').hidden && fbUser) renderFriends(); }, 15000);
  loadFirebase(function () {});""",
"""  setInterval(function () { if (!$('friends').hidden && fbUser) renderFriends(); }, 15000);
  if (!CG_MODE) loadFirebase(function () {});""")

# ---- mute and chat preferences from CrazyGames
sub("""  function musicLevel() {""", """  function musicLevel() {
    if (muted) return 0;""")
sub("""  function pchatVisible() {
    var box = $('partyChat');
    if (box) box.hidden = !(netRole === 'guest' || (netRole === 'host' && netGuests.length > 0));""",
"""  function pchatVisible() {
    var box = $('partyChat');
    if (box) box.hidden = cgNoChat() || !(netRole === 'guest' || (netRole === 'host' && netGuests.length > 0));""")
sub("""  function pchatAdd(from, text) {""", """  function pchatAdd(from, text) {
    if (cgNoChat()) return;""")
sub("""  function openIgChat() {""", """  function openIgChat() {
    if (cgNoChat()) return;""")

# ---- gameplay start/stop, celebrations, rooms
sub("""    state = 'play';
    syncHud();
    if (netRole === 'host') for (var gs = 0;""",
"""    state = 'play';
    syncHud();
    cgGame('gameplayStart'); cgRoom();
    if (netRole === 'host') for (var gs = 0;""")
sub("""  function finish(won, msg, place) {
    // With several people playing""",
"""  function finish(won, msg, place) {
    cgGame('gameplayStop');
    // With several people playing""")
sub("""    var earned = kills * 12 + Math.round(matchTime / 6) + (won ? 80 : 0);""",
    """    if (won) cgGame('happytime');
    var earned = kills * 12 + Math.round(matchTime / 6) + (won ? 80 : 0);""")
sub("""  function pause() {""", """  function pause() {
    cgGame('gameplayStop');""")
sub("""  function resume() {""", """  function resume() {
    cgGame('gameplayStart');""")
sub("""  function goHome() {
    netGuest = false; netGuestPaused = false;""",
"""  function goHome() {
    cgGame('gameplayStop');
    netGuest = false; netGuestPaused = false;""")
sub("""    netGuest = true; netGuestPaused = false;
    state = 'play';""", """    netGuest = true; netGuestPaused = false;
    state = 'play';
    cgGame('gameplayStart');""")
sub("""    if (m.won) cgGame""" if False else """  function guestOver(m) {
    if (!netGuest) return;""", """  function guestOver(m) {
    if (!netGuest) return;
    cgGame('gameplayStop');
    if (m.won) cgGame('happytime');""")
# rooms follow the party
sub("""        netStatus('Party open. Friends join with this code, or invite them from your friends list.');
        partyRender();""", """        netStatus(CG_MODE ? 'Party open. Share the invite link or this code.'
                          : 'Party open. Friends join with this code, or invite them from your friends list.');
        partyRender();
        cgRoom();""")
sub("""          netStatus(pub ? 'Joining a match...' : 'Connected! Waiting for the host to start a match.');
          syncMenu();""", """          netStatus(pub ? 'Joining a match...' : 'Connected! Waiting for the host to start a match.');
          syncMenu();
          cgRoom();""")
sub("""  function partyBroadcast() {""", """  function partyBroadcast() {
    cgRoom();""")
sub("""    netConn = null; netPeer = null; netRole = null; netPublic = false; netCode = '';""",
    """    if (netRole) { cgCall(function (c) { c.game.leftRoom(); c.game.hideInviteButton(); }); }
    netConn = null; netPeer = null; netRole = null; netPublic = false; netCode = '';""")

sub("""  // ---------------------------------------------------------------- accounts""",
r"""  // ---------------------------------------------------------------- crazygames
  var cgSet = { disableChat: false, muteAudio: false };
  function cgCall(fn) { if (!CG) return; try { fn(CG); } catch (err) {} }
  function cgGame(what) { cgCall(function (c) { if (c.game && c.game[what]) c.game[what](); }); }
  function cgNoChat() { return !!cgSet.disableChat; }
  function cgApply(st) {
    cgSet = st || cgSet;
    muted = !!cgSet.muteAudio;
    pchatVisible();
    if (cgNoChat() && $('igChat') && !$('igChat').hidden) $('igChat').hidden = true;
  }
  // tell CrazyGames which room we are in and whether friends can still come
  function cgRoom() {
    if (!CG) return;
    if (!netRole || !netCode) return;
    var joinable = netRole === 'host' && humansIn() < NET_MAX &&
                   ((state !== 'play' && state !== 'paused') || (typeof lobbyOpen === 'function' && lobbyOpen()));
    cgCall(function (c) {
      c.game.updateRoom({ roomId: netCode, isJoinable: joinable, inviteParams: { room: netCode } });
      if (joinable && state !== 'play') c.game.showInviteButton({ room: netCode });
      else c.game.hideInviteButton();
    });
  }
  function cgUser() {
    cgCall(function (c) {
      if (!c.user || !c.user.isUserAccountAvailable) return;
      c.user.getUser().then(function (u) {
        if (u && u.username) acctName = u.username;
        $('acctName').textContent = acctName;
        syncMenu();
      }).catch(function () {});
    });
  }
  function cgInit() {
    if (!CG_MODE) return;
    // no accounts, friends or friend chat of our own on CrazyGames
    acctName = 'GUEST' + (1000 + rnd(9000));
    $('acctBtn').hidden = true;
    $('friendsBtn').hidden = true;
    $('acctName').textContent = acctName;
    var sdk = window.CrazyGames && window.CrazyGames.SDK;
    if (!sdk) { cgLand(); return; }                        // blocked (ad blocker): play on regardless
    sdk.init().then(function () {
      CG = sdk;
      // bring anything saved before the SDK was ready into their storage
      ['earshot.wallet', 'earshot.settings', 'earshot.tutDone'].forEach(function (k) {
        try { if (CG.data.getItem(k) === null) { var v = localStorage.getItem(k); if (v !== null) CG.data.setItem(k, v); } } catch (err) {}
      });
      loadWallet(); loadSettings(); refreshCoins(); syncTutBtn();
      cgApply(CG.game.settings);
      CG.game.addSettingsChangeListener(cgApply);
      cgUser();
      CG.user.addAuthListener(function () { cgUser(); loadWallet(); refreshCoins(); });
      // someone clicked a friend's invite while already playing
      CG.game.addJoinRoomListener(function (p) {
        if (!p || !p.room) return;
        if (state === 'play' || state === 'paused') leaveMatch();
        openOnline(); joinGame(p.room, false);
      });
      var inv = CG.game.inviteParams;
      if (inv && inv.room) { openOnline(); joinGame(inv.room, false); return; }
      if (CG.game.isInstantMultiplayer) { openOnline(); hostGame(); return; }
      cgLand();
    }).catch(function () { cgLand(); });
  }
  // New players land straight in the action: the tutorial the first time,
  // the menu after that.
  function cgLand() {
    if (storeGet('earshot.tutDone') !== '1' && state === 'menu') $('tutBtn').click();
  }

  // ---------------------------------------------------------------- accounts""")

sub("""  syncMenu();
  syncTutBtn();
  requestAnimationFrame(frame);""", """  syncMenu();
  syncTutBtn();
  cgInit();
  requestAnimationFrame(frame);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p55 applied')

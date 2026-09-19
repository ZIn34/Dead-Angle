# -*- coding: utf-8 -*-
"""Accounts (Firebase), friends, invites, and Quick Play into public matches."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# coins and skins follow the account
sub("""  function saveWallet() {
    try { localStorage.setItem('earshot.wallet', JSON.stringify(WALLET)); } catch (err) {}
  }""",
"""  function saveWallet() {
    try { localStorage.setItem('earshot.wallet', JSON.stringify(WALLET)); } catch (err) {}
    if (typeof cloudWallet === 'function') cloudWallet();
  }""")

# starting a match clears the online screens too
sub("""    elMenu.hidden = true; elOver.hidden = true; elHud.hidden = false; elPaused.hidden = true;""",
    """    elMenu.hidden = true; elOver.hidden = true; elHud.hidden = false; elPaused.hidden = true;
    $('online').hidden = true; $('account').hidden = true;""")

# a public match rolls straight into the next one
sub("""      elHud.hidden = true;
      elOver.hidden = false;
    }, 850);""",
"""      elHud.hidden = true;
      elOver.hidden = false;
      if (netRole === 'host' && netPublic) {
        $('overMsg').textContent = why + '  Next match in 10s.';
        setTimeout(function () {
          if (tok === matchToken && state === 'over' && netRole === 'host' && netPublic) startMatch();
        }, 10000);
      }
    }, 850);""")

sub("""  // ---------------------------------------------------------------- loop""",
r"""  // ---------------------------------------------------------------- accounts
  // Firebase is only an address book here: who you are, who your friends are,
  // which public matches are open. The matches themselves still run peer to
  // peer on the host's machine.
  var FB_VER = '10.14.1';
  var FB_CFG = {
    apiKey: 'AIzaSyCTCjH9-4Trrz1BIZa3wZcue6x_89GMUSk',
    authDomain: 'dead-angle-f314f.firebaseapp.com',
    projectId: 'dead-angle-f314f',
    storageBucket: 'dead-angle-f314f.firebasestorage.app',
    messagingSenderId: '382280525012',
    appId: '1:382280525012:web:968327ff5739d7135cc741'
  };
  // usernames become a made-up address - nobody needs a real email to play
  var EMAIL_DOM = '@players.dead-angle.game';
  var fbReady = false, fbLoading = null, fbAuth = null, fbDb = null, fbUser = null;
  var fbFriends = [], fbInvUnsub = null, fbBeatT = null, fbWalletT = null, fbProfileTries = 0;

  function acctStatus(t) { var el = $('acctStatus'); if (el) el.textContent = t; }
  function quickStatus(t) { netStatus(t); var el = $('quickStatus'); if (el) { el.textContent = t; el.hidden = !t; } }

  function loadFirebase(cb) {
    if (fbReady) { cb(); return; }
    if (fbLoading) { fbLoading.push(cb); return; }
    fbLoading = [cb];
    var files = ['firebase-app-compat.js', 'firebase-auth-compat.js', 'firebase-firestore-compat.js'], k = 0;
    (function next() {
      if (k >= files.length) {
        try {
          if (!firebase.apps.length) firebase.initializeApp(FB_CFG);
          fbAuth = firebase.auth(); fbDb = firebase.firestore();
          fbAuth.onAuthStateChanged(onAuth);
          fbReady = true;
        } catch (err) { acctStatus('The account service did not start.'); fbLoading = null; return; }
        var q = fbLoading; fbLoading = null;
        q.forEach(function (f) { f(); });
        return;
      }
      var sc = document.createElement('script');
      sc.src = 'https://cdn.jsdelivr.net/npm/firebase@' + FB_VER + '/' + files[k++];
      sc.onload = next;
      sc.onerror = function () { acctStatus('Could not reach the account service.'); fbLoading = null; };
      document.head.appendChild(sc);
    })();
  }

  function errText(err) {
    var c = (err && err.code) || '';
    if (c === 'taken' || c === 'auth/email-already-in-use') return 'That username is taken.';
    if (c === 'auth/invalid-credential' || c === 'auth/wrong-password' || c === 'auth/user-not-found' || c === 'auth/invalid-login-credentials')
      return 'Wrong username or password.';
    if (c === 'auth/too-many-requests') return 'Too many tries - wait a minute.';
    if (c === 'auth/network-request-failed' || c === 'unavailable') return 'No connection to the account service.';
    if (c === 'auth/operation-not-allowed') return 'Username sign-in is not switched on in Firebase yet (Email/Password).';
    if (c === 'permission-denied') return 'The game database is not set up yet (Firestore rules).';
    if (c === 'auth/weak-password') return 'Pick a longer password (6+ characters).';
    return (err && err.message) || 'Something went wrong.';
  }
  function readCreds() {
    var nm = $('acctUser').value.trim(), pw = $('acctPass').value;
    if (!/^[A-Za-z0-9_]{3,16}$/.test(nm)) { acctStatus('Usernames are 3-16 letters, numbers or _.'); return null; }
    if (pw.length < 6) { acctStatus('Passwords need at least 6 characters.'); return null; }
    return { name: nm, lower: nm.toLowerCase(), pass: pw };
  }

  function signUp() {
    var c = readCreds(); if (!c) return;
    acctStatus('Creating your account...');
    loadFirebase(function () {
      fbDb.collection('usernames').doc(c.lower).get().then(function (d) {
        if (d.exists) throw { code: 'taken' };
        return fbAuth.createUserWithEmailAndPassword(c.lower + EMAIL_DOM, c.pass);
      }).then(function (cred) {
        var uid = cred.user.uid;
        return fbDb.collection('usernames').doc(c.lower).set({ uid: uid, name: c.name }).then(function () {
          return fbDb.collection('users').doc(uid).set({
            name: c.name, nameLower: c.lower, friends: [],
            coins: WALLET.coins, owned: WALLET.owned, skin: WALLET.skin,
            lastSeen: Date.now(), party: '', partyHost: false
          });
        }).catch(function (err) {
          // the name got taken in the same moment: undo the half-made account
          return cred.user.delete().then(function () { throw err; }, function () { throw err; });
        });
      }).then(function () {
        acctStatus('Welcome, ' + c.name + '!');
        fbProfileTries = 0; onAuth(fbAuth.currentUser);
        setTimeout(closeAccount, 700);
      }).catch(function (err) { acctStatus(errText(err)); });
    });
  }
  function logIn() {
    var c = readCreds(); if (!c) return;
    acctStatus('Logging in...');
    loadFirebase(function () {
      fbAuth.signInWithEmailAndPassword(c.lower + EMAIL_DOM, c.pass)
        .then(function () { acctStatus(''); closeAccount(); })
        .catch(function (err) { acctStatus(errText(err)); });
    });
  }
  function logOut() {
    if (netRole) netClose('Logged out.');
    if (fbAuth) fbAuth.signOut();
  }

  function onAuth(user) {
    fbUser = user || null;
    if (fbInvUnsub) { fbInvUnsub(); fbInvUnsub = null; }
    if (fbBeatT) { clearInterval(fbBeatT); fbBeatT = null; }
    if (!user) { acctName = ''; fbFriends = []; renderAcct(); renderFriends(); return; }
    fbDb.collection('users').doc(user.uid).get().then(function (d) {
      if (!d.exists) {
        // a brand-new account can arrive here a moment before its profile
        if (fbProfileTries++ < 4) setTimeout(function () { if (fbUser === user) onAuth(user); }, 1200);
        return;
      }
      var p = d.data();
      acctName = p.name || '';
      fbFriends = p.friends || [];
      // the account's coins and skins win; skins owned on this machine are kept
      if (typeof p.coins === 'number') {
        var owned = (p.owned || []).slice();
        WALLET.owned.forEach(function (k) { if (owned.indexOf(k) < 0) owned.push(k); });
        WALLET = { coins: p.coins, owned: owned.length ? owned : WALLET.owned, skin: (p.skin | 0) };
        if (WALLET.owned.indexOf(WALLET.skin) < 0) WALLET.skin = WALLET.owned[0];
        try { localStorage.setItem('earshot.wallet', JSON.stringify(WALLET)); } catch (err) {}
        refreshCoins();
      }
      renderAcct();
      heartbeat();
      fbBeatT = setInterval(heartbeat, 30000);
      listenInvites();
      renderFriends();
    }).catch(function (err) { acctStatus(errText(err)); renderAcct(); });
  }

  var cloudWallet = function () {
    if (!fbUser || !fbDb) return;
    clearTimeout(fbWalletT);
    fbWalletT = setTimeout(function () {
      if (!fbUser) return;
      fbDb.collection('users').doc(fbUser.uid).update({ coins: WALLET.coins, owned: WALLET.owned, skin: WALLET.skin }).catch(function () {});
    }, 1500);
  };
  function heartbeat() {
    if (!fbUser) return;
    fbDb.collection('users').doc(fbUser.uid).update({
      lastSeen: Date.now(), party: netRole ? netCode : '', partyHost: netRole === 'host'
    }).catch(function () {});
  }

  function renderAcct() {
    var on = !!(fbUser && acctName);
    $('acctName').textContent = on ? acctName : 'NOT LOGGED IN';
    $('acctBtn').textContent = on ? 'LOG OUT' : 'LOG IN';
    $('friendsBox').hidden = !on;
    $('friendsNeed').hidden = on;
  }
  function openAccount(msg) {
    ['menu', 'online'].forEach(function (id) { $(id).hidden = true; });
    $('account').hidden = false;
    acctStatus(msg || '');
    loadFirebase(function () {});
  }
  function closeAccount() { $('account').hidden = true; elMenu.hidden = false; syncMenu(); }

  // ---- friends ----
  function addFriend() {
    var nm = $('friendName').value.trim().toLowerCase();
    if (!fbUser) { openAccount('Log in to add friends.'); return; }
    if (!/^[a-z0-9_]{3,16}$/.test(nm)) { netStatus('Type their username.'); return; }
    fbDb.collection('usernames').doc(nm).get().then(function (d) {
      if (!d.exists) { netStatus('Nobody is called ' + nm + '.'); return; }
      var uid = d.data().uid;
      if (uid === fbUser.uid) { netStatus('That is you!'); return; }
      if (fbFriends.indexOf(uid) >= 0) { netStatus('Already on your list.'); return; }
      return fbDb.collection('users').doc(fbUser.uid).update({ friends: firebase.firestore.FieldValue.arrayUnion(uid) }).then(function () {
        fbFriends.push(uid);
        $('friendName').value = '';
        netStatus('Added ' + d.data().name + '.');
        renderFriends();
      });
    }).catch(function (err) { netStatus(errText(err)); });
  }
  function removeFriend(uid) {
    fbDb.collection('users').doc(fbUser.uid).update({ friends: firebase.firestore.FieldValue.arrayRemove(uid) }).then(function () {
      fbFriends = fbFriends.filter(function (u) { return u !== uid; });
      renderFriends();
    }).catch(function (err) { netStatus(errText(err)); });
  }
  var friendsT = null;
  function renderFriends() {
    var el = $('friendList');
    if (!el) return;
    if (!fbUser || !fbFriends.length) {
      el.innerHTML = fbUser ? '<div class="fempty">No friends yet - add one by username.</div>' : '';
      return;
    }
    Promise.all(fbFriends.map(function (uid) {
      return fbDb.collection('users').doc(uid).get().then(function (d) { var v = d.exists ? d.data() : null; if (v) v.uid = uid; return v; }, function () { return null; });
    })).then(function (list) {
      el.innerHTML = '';
      var now = Date.now();
      list.filter(Boolean).sort(function (a, b) { return (b.lastSeen || 0) - (a.lastSeen || 0); }).forEach(function (f) {
        var online = now - (f.lastSeen || 0) < 75000;
        var row = document.createElement('div');
        row.className = 'frow' + (online ? ' on' : '');
        var nm = document.createElement('span');
        nm.className = 'fname';
        nm.textContent = f.name;
        var st = document.createElement('em');
        st.textContent = online ? (f.party ? (f.partyHost ? 'HOSTING A PARTY' : 'IN A PARTY') : 'ONLINE') : 'OFFLINE';
        row.appendChild(nm); row.appendChild(st);
        if (online && f.partyHost && f.party && f.party !== netCode) {
          var jb = document.createElement('button');
          jb.className = 'tgl on'; jb.type = 'button'; jb.textContent = 'JOIN';
          jb.addEventListener('click', function () { joinGame(f.party, false); });
          row.appendChild(jb);
        }
        if (online) {
          var ib = document.createElement('button');
          ib.className = 'tgl'; ib.type = 'button'; ib.textContent = 'INVITE';
          ib.addEventListener('click', function () { invite(f); });
          row.appendChild(ib);
        }
        var rb = document.createElement('button');
        rb.className = 'tgl'; rb.type = 'button'; rb.textContent = '✕'; rb.title = 'Remove friend';
        rb.addEventListener('click', function () { removeFriend(f.uid); });
        row.appendChild(rb);
        el.appendChild(row);
      });
    });
  }

  // ---- invites ----
  function invite(f) {
    if (netRole === 'guest') { netStatus('Only the party leader can invite.'); return; }
    hostGame(function () {
      fbDb.collection('invites').doc(f.uid).collection('items').add({
        from: fbUser.uid, fromName: acctName, code: netCode, at: Date.now()
      }).then(function () { netStatus('Invite sent to ' + f.name + '.'); heartbeat(); })
        .catch(function (err) { netStatus(errText(err)); });
    });
  }
  var shownInvite = null;
  function listenInvites() {
    if (!fbUser) return;
    fbInvUnsub = fbDb.collection('invites').doc(fbUser.uid).collection('items').onSnapshot(function (qs) {
      var now = Date.now(), best = null;
      qs.forEach(function (d) {
        var v = d.data();
        if (now - (v.at || 0) > 180000) { d.ref.delete().catch(function () {}); return; }
        if (!best || v.at > best.v.at) best = { ref: d.ref, v: v };
      });
      if (!best) { $('inviteToast').hidden = true; shownInvite = null; return; }
      shownInvite = best;
      $('inviteText').textContent = best.v.fromName + ' invited you to their party';
      $('inviteToast').hidden = state === 'play';
    }, function () {});
  }
  function answerInvite(yes) {
    var inv = shownInvite;
    $('inviteToast').hidden = true;
    shownInvite = null;
    if (!inv) return;
    inv.ref.delete().catch(function () {});
    if (yes) { if (netGuest || state === 'play') leaveMatch(); openOnline(); joinGame(inv.v.code, false); }
  }

  // ---- quick play ----
  function quickPlay() {
    if (!fbUser || !acctName) { openAccount('Log in to play online.'); return; }
    if (netRole === 'guest') { openOnline(); netStatus('You are in a party - the leader starts the match.'); return; }
    initAudio();
    if (netRole === 'host' && netGuests.length) { goPublicHost(); return; }
    if (netRole) netClose('');
    openOnline();
    quickStatus('Finding a ' + MODE_LABEL[mode].toLowerCase() + ' match...');
    fbDb.collection('lobbies').where('mode', '==', mode).where('open', '==', true).limit(25).get().then(function (qs) {
      var now = Date.now(), list = [];
      qs.forEach(function (d) {
        var L = d.data();
        if (now - (L.updated || 0) < 30000 && L.humans < L.max && L.map === mapKind && L.host !== fbUser.uid) list.push(L);
      });
      list.sort(function (a, b) { return b.humans - a.humans; });
      tryLobby(list, 0);
    }).catch(function () { goPublicHost(); });
  }
  function tryLobby(list, i) {
    if (i >= list.length) { goPublicHost(); return; }
    quickStatus('Joining ' + (list[i].name || 'a match') + '...');
    quickFail = function () { quickFail = null; tryLobby(list, i + 1); };
    joinGame(list[i].code, true, function () { var f = quickFail; quickFail = null; if (f) f(); });
  }
  // nobody to join: open our own public match, which others will find
  function goPublicHost() {
    quickStatus('No open match - starting one. Others can drop in.');
    hostGame(function () {
      netPublic = true;
      lobbyWrite();
      quickStatus('');
      startMatch();
    });
  }
  var lobbyT = 0;
  function lobbyOpen() {
    if (state !== 'play' && state !== 'paused') return false;
    if (humansIn() >= Math.min(NET_MAX, fieldN)) return false;
    if (mode === 'br') return !!plane && plane.t < plane.dur * 0.75;   // only while there are seats on the plane
    return true;
  }
  function lobbyWrite() {
    if (!fbDb || !fbUser || !netCode || !netPublic) return;
    fbDb.collection('lobbies').doc(netCode).set({
      host: fbUser.uid, name: acctName, code: netCode, mode: mode, map: mapKind,
      humans: humansIn(), max: Math.min(NET_MAX, fieldN), open: lobbyOpen(), updated: Date.now()
    }).catch(function () {});
  }
  lobbyTouch = function () { if (netPublic) { lobbyT = 0.2; } };
  lobbyTick = function (dt) {
    if (!netPublic) return;
    lobbyT -= dt;
    if (lobbyT <= 0) { lobbyT = 8; lobbyWrite(); }
  };
  lobbyDrop = function () {
    if (fbDb && fbUser && netCode) fbDb.collection('lobbies').doc(netCode).delete().catch(function () {});
  };
  window.addEventListener('beforeunload', function () { if (netPublic) lobbyDrop(); });

  // ---- wiring ----
  $('acctBtn').addEventListener('click', function () { if (fbUser && acctName) logOut(); else openAccount(''); });
  $('acctLogin').addEventListener('click', logIn);
  $('acctSignup').addEventListener('click', signUp);
  $('acctBack').addEventListener('click', closeAccount);
  $('quickBtn').addEventListener('click', quickPlay);
  $('friendAdd').addEventListener('click', addFriend);
  $('friendsNeed').addEventListener('click', function () { openAccount(''); });
  $('inviteJoin').addEventListener('click', function () { answerInvite(true); });
  $('inviteNo').addEventListener('click', function () { answerInvite(false); });
  ['acctUser', 'acctPass', 'friendName'].forEach(function (id) {
    $(id).addEventListener('keydown', function (ev) {
      ev.stopPropagation();
      if (ev.key !== 'Enter') return;
      if (id === 'friendName') addFriend(); else logIn();
    });
  });
  // the friends list keeps itself fresh while you are looking at it
  setInterval(function () { if (!$('online').hidden && fbUser) renderFriends(); }, 15000);
  loadFirebase(function () {});

  // ---------------------------------------------------------------- loop""")

# the online screen shows friends when it opens
sub("""  function openOnline() {
    elMenu.hidden = true;
    $('online').hidden = false;""",
"""  function openOnline() {
    elMenu.hidden = true;
    $('online').hidden = false;
    partyRender();
    if (typeof renderFriends === 'function') renderFriends();""")
sub("""  $('onlineBtn').addEventListener('click', openOnline);
  $('netHost').addEventListener('click', hostGame);""",
"""  $('onlineBtn').addEventListener('click', openOnline);
  $('netHost').addEventListener('click', function () { hostGame(); });""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ================================================================ html ======
h = io.open(H, encoding='utf-8').read()
def hsub(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

# account chip over the title
hsub("""      <div class="brand">
        <h1>""", """      <div class="acct"><span id="acctName">NOT LOGGED IN</span><button class="tgl" id="acctBtn" type="button">LOG IN</button></div>
      <div class="brand">
        <h1>""")
hsub("""        <button class="go ghost" id="onlineBtn" type="button">PLAY ONLINE</button>""",
     """        <button class="go" id="quickBtn" type="button">QUICK PLAY ONLINE</button>
        <button class="go ghost" id="onlineBtn" type="button">FRIENDS &amp; PARTY</button>""")

# the online screen: party + friends
a = h.index('  <div class="screen" id="online" hidden>')
b = h.index('  <div class="screen" id="settings" hidden>')
h = h[:a] + """  <div class="screen" id="online" hidden>
    <div class="panel">
      <div class="brand">
        <h2 class="ptitle">PARTY</h2>
        <div class="rule"></div>
        <div class="tag">friends drop into your matches with you</div>
      </div>
      <p class="modedesc" id="netStatus">Host a party, or join one with a code.</p>
      <div class="pbtns">
        <button class="go" id="netHost" type="button">HOST A PARTY</button>
        <div class="netcode" id="netCodeBox" hidden>PARTY CODE<b id="netCode">-----</b></div>
        <div class="plist" id="partyList" hidden></div>
        <div class="joinrow">
          <input id="netJoinCode" maxlength="5" placeholder="CODE" autocomplete="off" spellcheck="false" aria-label="Party code">
          <button class="go ghost" id="netJoin" type="button">JOIN</button>
        </div>
      </div>

      <div class="brand">
        <h2 class="ptitle sm">FRIENDS</h2>
        <div class="rule"></div>
      </div>
      <button class="go ghost" id="friendsNeed" type="button">LOG IN FOR FRIENDS</button>
      <div class="friends" id="friendsBox" hidden>
        <div class="joinrow">
          <input class="wide" id="friendName" maxlength="16" placeholder="USERNAME" autocomplete="off" spellcheck="false" aria-label="Friend's username">
          <button class="go ghost" id="friendAdd" type="button">ADD</button>
        </div>
        <div class="flist" id="friendList"></div>
      </div>

      <div class="pbtns">
        <button class="go ghost" id="netLeave" type="button">LEAVE PARTY</button>
        <button class="go ghost" id="netBack" type="button">BACK</button>
      </div>
    </div>
  </div>

  <div class="screen" id="account" hidden>
    <div class="panel">
      <div class="brand">
        <h2 class="ptitle">ACCOUNT</h2>
        <div class="rule"></div>
        <div class="tag">keeps your name, skins, credits and friends</div>
      </div>
      <div class="acctform">
        <input class="wide" id="acctUser" maxlength="16" placeholder="USERNAME" autocomplete="username" spellcheck="false" aria-label="Username">
        <input class="wide" id="acctPass" type="password" maxlength="64" placeholder="PASSWORD" autocomplete="current-password" aria-label="Password">
      </div>
      <p class="modedesc" id="acctStatus"></p>
      <div class="pbtns">
        <button class="go" id="acctLogin" type="button">LOG IN</button>
        <button class="go ghost" id="acctSignup" type="button">CREATE ACCOUNT</button>
        <button class="go ghost" id="acctBack" type="button">BACK</button>
      </div>
      <p class="modedesc">No email needed. There is no password reset, so pick one you will remember.</p>
    </div>
  </div>

""" + h[b:]

# invite pop-up
hsub("""  <div class="screen" id="settings" hidden>""",
"""  <div class="toast" id="inviteToast" hidden>
    <span id="inviteText"></span>
    <button class="tgl on" id="inviteJoin" type="button">JOIN</button>
    <button class="tgl" id="inviteNo" type="button">NO</button>
  </div>

  <div class="screen" id="settings" hidden>""")

hsub(""".ptitle{""", """.acct{display:flex;align-items:center;gap:10px;font-family:var(--font-m);font-size:11px;letter-spacing:.18em;color:var(--khaki)}
.acct span{color:var(--paper);font-weight:600}
.plist,.flist{width:100%;max-width:420px;display:flex;flex-direction:column;gap:2px;background:var(--out);border:3px solid var(--out);box-shadow:4px 4px 0 rgba(0,0,0,.45)}
.flist:empty{display:none}
.prow,.frow,.fempty{background:var(--navy);padding:9px 12px;display:flex;align-items:center;gap:8px;font-family:var(--font-m);font-size:11px;letter-spacing:.12em;color:var(--paper);text-align:left}
.fempty{color:var(--khaki)}
.frow .fname{flex:1;font-weight:600}
.frow em{font-style:normal;font-size:9px;letter-spacing:.16em;color:var(--khaki)}
.frow.on em{color:var(--gold)}
.frow .tgl{padding:4px 10px}
.friends{width:100%;display:flex;flex-direction:column;align-items:center;gap:10px}
.acctform{display:flex;flex-direction:column;gap:10px;align-items:center}
.joinrow input.wide,.acctform input{width:260px;padding:11px 12px;font-family:var(--font-m);font-size:14px;font-weight:600;letter-spacing:.14em;text-align:center;background:var(--paper);color:var(--out);border:3px solid var(--out);border-radius:4px}
.ptitle.sm{font-size:clamp(22px,6vw,30px)}
.toast{position:absolute;top:14px;left:50%;transform:translateX(-50%);z-index:20;display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--navy);border:3px solid var(--out);border-radius:4px;box-shadow:4px 4px 0 rgba(0,0,0,.45);font-family:var(--font-m);font-size:12px;letter-spacing:.1em;color:var(--paper);pointer-events:auto;max-width:calc(100% - 32px)}
.ptitle{""")

io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p50 applied')

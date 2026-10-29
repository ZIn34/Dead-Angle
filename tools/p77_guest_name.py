# -*- coding: utf-8 -*-
"""A name is all you need: one short page before anything, online play as a
guest, your own name over your head, and credits that only stick if you sign
in. Both builds also share one look now, with blood left to the player."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- one look for both builds; blood is the player's choice ----------------------
sub("""  var FOV_HALF = CG_MODE ? 1.28 : 0.96, NEAR_SEE = CG_MODE ? 120 : 60;""",
"""  var FOV_HALF = 1.28, NEAR_SEE = 120;""")
sub("""  var GORE = !CG_MODE;""",
"""  // Blood is a setting, nothing else. CrazyGames is a PEGI 12 site, so their
  // build starts with it off; anyone can turn it on or off in SETTINGS.
  if (CG_MODE) SET.blood = false;""")
s = s.replace(' && GORE', '')
s = s.replace(' || !GORE', '')
sub("""    g.addColorStop(1, CG_MODE ? 'rgba(4,6,10,.74)' : 'rgba(4,6,10,.93)');""",
    """    g.addColorStop(1, 'rgba(4,6,10,.74)');""")
sub("""    if ($('bloodRow')) $('bloodRow').hidden = true;
""", "")

# ---- who you are -------------------------------------------------------------------
sub("""  var acctName = '';                 // the signed-in username, if any""",
"""  var acctName = '';                 // the signed-in username, if any
  var guestName = '';                // the name you typed on the way in
  var guestEarned = 0;               // credits earned since you last signed in
  function playerName() { return acctName || guestName || 'PLAYER'; }
  function isGuest() { return !(fbUser && acctName); }
  function needName() { return !acctName && !guestName; }
  function loadName() { try { guestName = storeGet('earshot.name') || ''; } catch (err) {} }
  function setGuestName(n) {
    n = String(n || '').replace(/[^A-Za-z0-9_]/g, '').slice(0, 16);
    if (n.length < 2) return false;
    guestName = n;
    storeSet('earshot.name', n);
    return true;
  }""")

# ---- the name page, before anything else ---------------------------------------------
sub("""  function openAccount(msg) {""",
"""  // One box, one button. Nothing stands between a new player and a match.
  function openNameGate(msg) {
    ['menu', 'online', 'friends', 'account', 'shop', 'settings'].forEach(function (id) { if ($(id)) $(id).hidden = true; });
    $('namegate').hidden = false;
    $('nameStatus').textContent = msg || '';
    $('guestUser').value = guestName || '';
    setTimeout(function () { try { $('guestUser').focus(); } catch (err) {} }, 30);
  }
  function closeNameGate() { $('namegate').hidden = true; elMenu.hidden = false; syncMenu(); renderAcct(); }
  function takeName() {
    if (!setGuestName($('guestUser').value)) { $('nameStatus').textContent = 'Two letters or more, letters and numbers.'; return false; }
    closeNameGate();
    return true;
  }
  $('namePlay').addEventListener('click', takeName);
  $('guestUser').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') takeName();
  });
  $('nameLogin').addEventListener('click', function () { $('namegate').hidden = true; openAccount(''); });

  function openAccount(msg) {""")
sub("""  function closeAccount() { $('account').hidden = true; elMenu.hidden = false; syncMenu(); }""",
"""  function closeAccount() {
    $('account').hidden = true;
    if (needName()) { openNameGate(''); return; }      // still nameless: back to the name
    elMenu.hidden = false; syncMenu();
  }""")

# ---- your name, wherever the game asks for one -----------------------------------------
s = s.replace("acctName || 'HOST'", "playerName()")
s = s.replace("name: acctName || 'PLAYER'", "name: playerName()")
sub("""    var on = !!(fbUser && acctName);
    $('acctName').textContent = on ? acctName : 'NOT LOGGED IN';
    $('acctBtn').textContent = on ? 'LOG OUT' : 'LOG IN';""",
"""    var on = !!(fbUser && acctName);
    $('acctName').textContent = on ? acctName : (guestName ? guestName + '  \\u00b7  GUEST' : 'NOT LOGGED IN');
    $('acctBtn').textContent = on ? 'LOG OUT' : 'LOG IN';
    var gh = $('guestHint');
    if (gh) gh.hidden = on || !WALLET.coins;""")

# ---- online needs a name, not an account -----------------------------------------------
sub("""    if (CG_MODE && !fbUser) {""", """    if (needName()) { openNameGate('Pick a name to play online.'); return; }
    if (!fbUser) {""")
sub("""    if (!CG_MODE && (!fbUser || !acctName)) { openAccount('Log in to play online.'); return; }
""", "")

# ---- your own name over your head; nobody else's ----------------------------------------
sub("""  function renderAllies() {""",
"""  // Your name floats over you so you know who you are playing as. Enemies
  // stay anonymous - a name would give away a player standing in the dark.
  function renderOwnName() {
    if (noOverlay || !player.alive || player.air === 'plane' || state !== 'play') return;
    var nm = player.local ? playerName() : player.name;
    if (!nm) return;
    var sx = (player.x - cam.x) * zoom + cw / 2;
    var sy = (player.y - cam.y) * zoom + ch / 2 - (player.r + 16) * zoom;
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '700 10px "IBM Plex Mono", monospace';
    pill(nm, sx, sy, '#8ff0e4');
    ctx.restore();
  }
  function renderAllies() {""")
sub("""    renderAllies();
    renderPings();""",
"""    renderAllies();
    renderOwnName();
    renderPings();""")

# ---- credits a guest has to sign in to keep ----------------------------------------------
sub("""    var earned = kills * 12 + Math.round(matchTime / 6) + (won ? 80 : 0);
    WALLET.coins += earned;""",
"""    var earned = kills * 12 + Math.round(matchTime / 6) + (won ? 80 : 0);
    WALLET.coins += earned;
    if (isGuest()) guestEarned += earned;""")
sub("""      $('overMsg').textContent = why;""",
"""      $('overMsg').textContent = why + (isGuest() && WALLET.coins ? '  Playing as a guest - sign in before you leave to keep your credits.' : '');""")
# the account takes the guest's credits with it instead of overwriting them
sub("""      if (typeof p.coins === 'number') {
        var owned = (p.owned || []).slice();
        WALLET.owned.forEach(function (k) { if (owned.indexOf(k) < 0) owned.push(k); });
        WALLET = { coins: p.coins, owned: owned.length ? owned : WALLET.owned, skin: (p.skin | 0) };""",
"""      if (typeof p.coins === 'number') {
        var owned = (p.owned || []).slice();
        WALLET.owned.forEach(function (k) { if (owned.indexOf(k) < 0) owned.push(k); });
        // whatever this guest earned before signing in comes with them
        WALLET = { coins: p.coins + guestEarned, owned: owned.length ? owned : WALLET.owned, skin: (p.skin | 0) };
        guestEarned = 0;""")
sub("""  resize();
  buildTextures();
  loadWallet();""",
"""  // a guest closing the tab would lose what they earned: say so first
  window.addEventListener('beforeunload', function (ev) {
    if (CG_MODE || !isGuest() || !WALLET.coins) return;
    ev.preventDefault();
    ev.returnValue = '';
    return '';
  });

  resize();
  buildTextures();
  loadName();
  loadWallet();""")
sub("""  syncTutBtn();
  cgInit();""",
"""  syncTutBtn();
  cgInit();
  if (!CG_MODE && needName()) openNameGate('');""")

# ---- a shorter first run ------------------------------------------------------------------
sub("""    { title: 'RELOAD', k: 'Reload', p: 'Reload', g: { caps: ['R'] }, gp: { caps: ['A'] },
      start: function () { var sl = curSlot(player); if (sl) sl.ammo = Math.min(sl.ammo, 4); },
      done: function () { return player.reloadT > 0; } },
""", "")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read(); ho = h
a = """  <div class="screen" id="account" hidden>"""
if a not in h:
    raise SystemExit('ACCOUNT SCREEN NOT FOUND')
h = h.replace(a, """  <div class="screen" id="namegate" hidden>
    <div class="panel">
      <div class="brand">
        <h1>DEAD <span class="gold">ANGLE</span></h1>
        <div class="rule"></div>
        <div class="tag">pick a name to play under</div>
      </div>
      <div class="acctform">
        <input class="wide" id="guestUser" maxlength="16" placeholder="USERNAME" spellcheck="false" aria-label="Username">
      </div>
      <p class="modedesc" id="nameStatus"></p>
      <div class="pbtns">
        <button class="go" id="namePlay" type="button">PLAY</button>
        <button class="go ghost" id="nameLogin" type="button">I HAVE AN ACCOUNT</button>
      </div>
      <p class="modedesc">No account needed. Credits you earn as a guest are only kept if you sign in before you leave.</p>
    </div>
  </div>

""" + a, 1)
b = """      <div class="acct"><span id="acctName">NOT LOGGED IN</span><button class="tgl" id="acctBtn" type="button">LOG IN</button></div>"""
if b not in h:
    raise SystemExit('ACCOUNT ROW NOT FOUND')
h = h.replace(b, b + """
      <p class="modedesc" id="guestHint" hidden>Sign in before you leave to keep your credits.</p>""", 1)
assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p77 applied')

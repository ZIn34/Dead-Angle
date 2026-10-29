# -*- coding: utf-8 -*-
"""A guest could not invite anyone: friends need an account, and the room code
had to be read out loud. Now a room has a link you can send, and FRIENDS says
what it wants instead of showing an empty screen."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
h = io.open(H, encoding='utf-8').read(); ho = h
s = io.open(G, encoding='utf-8').read(); so = s

def subh(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('JS PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ---- a link anyone can send -------------------------------------------------------
subh("""        <button class="go ghost" id="cgInviteBtn" type="button" hidden>COPY INVITE LINK</button>""",
"""        <button class="go ghost" id="cgInviteBtn" type="button" hidden>COPY INVITE LINK</button>
        <button class="go ghost" id="linkBtn" type="button" hidden>COPY INVITE LINK</button>""")
sub("""  function openAccount(msg) {""",
"""  // Anyone can invite without an account: the room's own address.
  function roomLink() {
    return location.origin + location.pathname + '?room=' + netCode;
  }
  function copyRoomLink() {
    if (!netCode) return;
    var link = roomLink();
    var done = function () { netStatus('Link copied - send it to whoever you want in.'); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(link).then(done, function () { netStatus(link); });
    else netStatus(link);
  }
  if ($('linkBtn')) $('linkBtn').addEventListener('click', copyRoomLink);
  // and opening that link drops you straight into their room
  function roomFromUrl() {
    var m = /[?&]room=([A-Za-z0-9]{3,8})/.exec(location.search || '');
    return m ? m[1].toUpperCase() : '';
  }

  function openAccount(msg) {""")
sub("""    showIf('netLeave', !!netRole && !quick);     // BACK is the way out of waiting""",
"""    showIf('netLeave', !!netRole && !quick);     // BACK is the way out of waiting
    showIf('linkBtn', !CG_MODE && netView === 'host' && hosting && !!netCode);""")

# ---- FRIENDS says what it needs ------------------------------------------------------
sub("""  $('friendsBtn').addEventListener('click', openFriends);""",
"""  $('friendsBtn').addEventListener('click', function () {
    // a guest has no friends list to show, so send them where it is made
    if (isGuest()) { openAccount('Friends need an account. It takes a moment, and your name and credits come with you.'); return; }
    openFriends();
  });""")

# ---- join straight from a link ---------------------------------------------------------
sub("""  if (!CG_MODE && needName()) openNameGate('');""",
"""  if (!CG_MODE && needName()) openNameGate('');
  // someone sent you a room link: go there as soon as you have a name
  (function () {
    var want = roomFromUrl();
    if (!want || CG_MODE) return;
    var tryJoin = function () {
      if (needName()) { setTimeout(tryJoin, 400); return; }
      openOnline('join');
      $('netJoinCode').value = want;
      netStatus('Joining the room from your link...');
      joinGame(want);
    };
    setTimeout(tryJoin, 300);
  })();""")

io.open(H, 'w', encoding='utf-8', newline='').write(h)
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p86 applied')

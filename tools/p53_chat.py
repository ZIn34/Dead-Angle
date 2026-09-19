# -*- coding: utf-8 -*-
"""Friend chat (mutual friends only), a word filter for chat and usernames."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# usernames go through the same filter
sub("""    if (!/^[A-Za-z0-9_]{3,16}$/.test(nm)) { acctStatus('Usernames are 3-16 letters, numbers or _.'); return null; }""",
    """    if (!/^[A-Za-z0-9_]{3,16}$/.test(nm)) { acctStatus('Usernames are 3-16 letters, numbers or _.'); return null; }
    if (rude(nm)) { acctStatus('Pick a different username.'); return null; }""")

# friend docs are kept, so chat knows who is mutual
sub("""    })).then(function (list) {
      el.innerHTML = '';
      var now = Date.now();""",
"""    })).then(function (list) {
      fbFriendDocs = list.filter(Boolean);
      el.innerHTML = '';
      var now = Date.now();""")
sub("""        row.appendChild(nm); row.appendChild(st);""",
"""        row.appendChild(nm); row.appendChild(st);
        // chat, only once you have added each other
        if ((f.friends || []).indexOf(fbUser.uid) >= 0) {
          var cb = document.createElement('button');
          cb.className = 'tgl' + (chatUnread[f.uid] ? ' on' : ''); cb.type = 'button';
          cb.textContent = chatUnread[f.uid] ? 'CHAT \\u2022 NEW' : 'CHAT';
          cb.addEventListener('click', function () { openChat(f); });
          row.appendChild(cb);
        } else {
          var hint = document.createElement('em');
          hint.className = 'fhint'; hint.textContent = 'ADD EACH OTHER TO CHAT';
          row.appendChild(hint);
        }""")

sub("""  // ---- invites ----""", r"""  // ---- chat ----
  // A plain word filter. It will not catch everything, but it keeps the
  // obvious stuff out of names and messages.
  var RUDE = ['fuck', 'shit', 'bitch', 'cunt', 'dick', 'pussy', 'cock', 'whore', 'slut', 'bastard',
              'asshole', 'nigg', 'fag', 'retard', 'rape', 'nazi', 'kys', 'penis', 'vagina', 'porn', 'sex'];
  function squash(t) {
    return String(t).toLowerCase().replace(/[@4]/g, 'a').replace(/3/g, 'e').replace(/[1!|]/g, 'i')
      .replace(/0/g, 'o').replace(/[5$]/g, 's').replace(/7/g, 't').replace(/[^a-z]/g, '');
  }
  function rude(t) {
    var q = squash(t);
    for (var i = 0; i < RUDE.length; i++) if (q.indexOf(RUDE[i]) >= 0) return true;
    return false;
  }
  function clean(t) {
    return String(t).split(/(\s+)/).map(function (w) { return rude(w) ? w.replace(/[^\s]/g, '*') : w; }).join('');
  }

  var fbFriendDocs = [], chatWith = null, chatUnsub = null, chatUnread = {};
  function pairId(a, b) { return a < b ? a + '_' + b : b + '_' + a; }
  function chatSeen(uid, at) {
    try {
      var m = JSON.parse(localStorage.getItem('earshot.chatSeen') || '{}');
      if (at === undefined) return m[uid] || 0;
      m[uid] = at; localStorage.setItem('earshot.chatSeen', JSON.stringify(m));
    } catch (err) {}
    return 0;
  }
  function openChat(f) {
    if (!fbUser) return;
    chatWith = f;
    ['friends', 'menu'].forEach(function (id) { $(id).hidden = true; });
    $('chat').hidden = false;
    $('chatName').textContent = f.name;
    $('chatLog').innerHTML = '<div class="cmsg sys">Loading...</div>';
    $('chatStatus').textContent = '';
    if (chatUnsub) chatUnsub();
    chatUnsub = fbDb.collection('chats').doc(pairId(fbUser.uid, f.uid)).collection('msgs')
      .orderBy('at', 'desc').limit(60).onSnapshot(function (qs) {
        var msgs = [];
        qs.forEach(function (d) { msgs.push(d.data()); });
        msgs.reverse();
        var log = $('chatLog');
        log.innerHTML = '';
        if (!msgs.length) log.innerHTML = '<div class="cmsg sys">No messages yet. Say hi!</div>';
        msgs.forEach(function (m) {
          var d = document.createElement('div');
          d.className = 'cmsg' + (m.from === fbUser.uid ? ' me' : '');
          var who = document.createElement('b');
          who.textContent = m.from === fbUser.uid ? acctName : f.name;
          var tx = document.createElement('span');
          tx.textContent = clean(m.text || '');
          d.appendChild(who); d.appendChild(tx);
          log.appendChild(d);
        });
        log.scrollTop = log.scrollHeight;
        if (msgs.length) chatSeen(f.uid, msgs[msgs.length - 1].at || Date.now());
        chatUnread[f.uid] = false;
        syncChatBadge();
      }, function (err) { $('chatStatus').textContent = errText(err); });
  }
  function closeChat() {
    if (chatUnsub) { chatUnsub(); chatUnsub = null; }
    chatWith = null;
    $('chat').hidden = true;
    $('friends').hidden = false;
    renderFriends();
  }
  function sendChat() {
    var inp = $('chatInput'), text = inp.value.trim();
    if (!text || !chatWith || !fbUser) return;
    if (text.length > 200) text = text.slice(0, 200);
    inp.value = '';
    fbDb.collection('chats').doc(pairId(fbUser.uid, chatWith.uid)).collection('msgs').add({
      from: fbUser.uid, text: clean(text), at: Date.now()
    }).catch(function (err) {
      $('chatStatus').textContent = err && err.code === 'permission-denied'
        ? 'You can only chat once you have both added each other.' : errText(err);
    });
  }
  // a gentle "new message" mark on the FRIENDS button
  function syncChatBadge() {
    var any = false;
    for (var k in chatUnread) if (chatUnread[k]) any = true;
    var b = $('friendsBtn');
    if (b) b.textContent = any ? 'FRIENDS • NEW MESSAGE' : 'FRIENDS';
  }
  function checkUnread() {
    if (!fbUser || !fbDb || state === 'play') return;
    var mutual = fbFriendDocs.filter(function (f) { return (f.friends || []).indexOf(fbUser.uid) >= 0; });
    mutual.forEach(function (f) {
      if (chatWith && chatWith.uid === f.uid) return;
      fbDb.collection('chats').doc(pairId(fbUser.uid, f.uid)).collection('msgs').orderBy('at', 'desc').limit(1).get()
        .then(function (qs) {
          var last = null;
          qs.forEach(function (d) { last = d.data(); });
          chatUnread[f.uid] = !!(last && last.from !== fbUser.uid && (last.at || 0) > chatSeen(f.uid));
          syncChatBadge();
        }, function () {});
    });
  }
  setInterval(checkUnread, 30000);
  // after logging in, learn who your friends are so the badge can work
  function primeFriends() {
    if (!fbUser || !fbFriends.length) return;
    Promise.all(fbFriends.map(function (uid) {
      return fbDb.collection('users').doc(uid).get().then(function (d) { var v = d.exists ? d.data() : null; if (v) v.uid = uid; return v; }, function () { return null; });
    })).then(function (list) { fbFriendDocs = list.filter(Boolean); checkUnread(); });
  }

  // ---- invites ----""")
sub("""      listenInvites();
      renderFriends();""", """      listenInvites();
      renderFriends();
      primeFriends();""")
sub("""  $('friendAdd').addEventListener('click', addFriend);""",
"""  $('friendAdd').addEventListener('click', addFriend);
  $('chatSend').addEventListener('click', sendChat);
  $('chatBack').addEventListener('click', closeChat);
  $('chatInput').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') sendChat();
  });""")
# a match or the account screen closes the chat
sub("""    $('online').hidden = true; $('account').hidden = true; $('friends').hidden = true;""",
    """    $('online').hidden = true; $('account').hidden = true; $('friends').hidden = true;
    if ($('chat') && !$('chat').hidden) closeChat(), $('friends').hidden = true;""")
sub("""    ['menu', 'over', 'paused', 'shop', 'settings', 'online', 'friends', 'account'].forEach(function (id) { $(id).hidden = true; });""",
    """    ['menu', 'over', 'paused', 'shop', 'settings', 'online', 'friends', 'account', 'chat'].forEach(function (id) { $(id).hidden = true; });""")
# controller
sub("""    var ids = ['osk', 'account', 'friends', 'online', 'paused', 'over', 'settings', 'shop', 'menu'];""",
    """    var ids = ['osk', 'account', 'chat', 'friends', 'online', 'paused', 'over', 'settings', 'shop', 'menu'];""")
sub("""    else if (!$('friends').hidden) $('friendsBack').click();""",
    """    else if (!$('chat').hidden) $('chatBack').click();
    else if (!$('friends').hidden) $('friendsBack').click();""")
# the on-screen keyboard needs a space for chat
sub("""    [['SHIFT', 'abc'], ['BACK', '\\u232b DELETE'], ['DONE', 'DONE']].forEach(function (p) {""",
    """    [['SHIFT', 'abc'], [' ', 'SPACE'], ['BACK', '\\u232b DELETE'], ['DONE', 'DONE']].forEach(function (p) {""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read()
a = """  <div class="screen" id="account" hidden>"""
if a not in h:
    raise SystemExit('HTML PATTERN NOT FOUND')
h = h.replace(a, """  <div class="screen" id="chat" hidden>
    <div class="panel">
      <div class="brand">
        <h2 class="ptitle sm">CHAT &middot; <span id="chatName"></span></h2>
        <div class="rule"></div>
      </div>
      <div class="chatlog" id="chatLog"></div>
      <div class="joinrow">
        <input class="wide chatin" id="chatInput" maxlength="200" placeholder="MESSAGE" autocomplete="off" aria-label="Message">
        <button class="go" id="chatSend" type="button">SEND</button>
      </div>
      <p class="modedesc" id="chatStatus"></p>
      <button class="go ghost" id="chatBack" type="button">BACK</button>
    </div>
  </div>

""" + a, 1)
a = """.ptitle{"""
h = h.replace(a, """.chatlog{width:100%;max-width:460px;height:min(46vh,340px);overflow-y:auto;display:flex;flex-direction:column;gap:6px;padding:10px;background:var(--navy-d);border:3px solid var(--out);box-shadow:4px 4px 0 rgba(0,0,0,.45);text-align:left}
.cmsg{align-self:flex-start;max-width:80%;padding:7px 10px;background:var(--navy);border:2px solid var(--out);border-radius:4px;font-family:var(--font-m);font-size:12px;color:var(--paper);word-break:break-word}
.cmsg b{display:block;font-size:9px;letter-spacing:.16em;color:var(--khaki);margin-bottom:2px}
.cmsg.me{align-self:flex-end;background:#4a4326}
.cmsg.me b{color:var(--gold)}
.cmsg.sys{align-self:center;background:transparent;border:0;color:var(--khaki)}
.joinrow input.chatin{width:min(300px,60vw);text-align:left;letter-spacing:.04em;text-transform:none}
.frow .fhint{font-size:8px;color:var(--khaki)}
""" + a, 1)
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p53 applied')

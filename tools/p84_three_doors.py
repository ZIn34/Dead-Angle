# -*- coding: utf-8 -*-
"""Three doors, each showing only its own thing: QUICK PLAY is a waiting room
with a player count and nothing else, HOST A ROOM hands out a code, JOIN A ROOM
asks for one."""
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

# ---- three buttons on the menu -------------------------------------------------
subh("""        <button class="go ghost" id="quickBtn" type="button">QUICK PLAY</button>
        <button class="go ghost" id="onlineBtn" type="button">HOST A ROOM</button>""",
"""        <button class="go ghost" id="quickBtn" type="button">QUICK PLAY</button>
        <button class="go ghost" id="onlineBtn" type="button">HOST A ROOM</button>
        <button class="go ghost" id="joinBtn" type="button">JOIN A ROOM</button>""")
subh("""      <p class="onlinehint">QUICK PLAY looks for other people for 20 seconds, then starts and fills the empty seats with bots &#183; HOST A ROOM gives you a code to share</p>""",
"""      <p class="onlinehint">QUICK PLAY waits for whoever turns up, then starts &#183; HOST A ROOM gives you a code to read out &#183; JOIN A ROOM takes someone else's code</p>""")

# ---- a waiting room with nothing in it but the count ------------------------------
subh("""        <h2 class="ptitle">ROOM</h2>""", """        <h2 class="ptitle" id="onlineTitle">ROOM</h2>""")
subh("""        <div class="tag">one of you hosts, everyone else types the code</div>""",
     """        <div class="tag" id="onlineTag">one of you hosts, everyone else types the code</div>""")
subh("""        <p class="joinlabel">OR JOIN SOMEONE ELSE'S ROOM</p>""",
     """        <p class="joinlabel" id="joinLabel">THE HOST'S CODE</p>""")
subh("""        <div class="joinrow">
          <input id="netJoinCode""",
     """        <div class="joinrow" id="joinRow">
          <input id="netJoinCode""")
subh("""      <p class="modedesc" id="netStatus">Host a room and read out the code, or type someone else's code below.</p>""",
"""      <div class="quickwait" id="quickWait" hidden>
        <b id="quickN">1</b>
        <span id="quickLbl">PLAYER WAITING</span>
        <i id="quickT">starting in 20s</i>
      </div>
      <p class="modedesc" id="netStatus">Host a room and read out the code, or type someone else's code below.</p>""")
subh(""".joinlabel{margin:10px 0 2px;""",
""".quickwait{display:flex;flex-direction:column;align-items:center;gap:2px;margin:6px 0 2px}
.quickwait b{font-family:var(--font-d);font-weight:700;font-size:54px;line-height:1;color:var(--gold);font-variant-numeric:tabular-nums}
.quickwait span{font-family:var(--font-m);font-size:10px;letter-spacing:.26em;color:var(--khaki)}
.quickwait i{font-style:normal;font-family:var(--font-m);font-size:11px;letter-spacing:.14em;color:var(--text);margin-top:8px}
.joinlabel{margin:10px 0 2px;""")

io.open(H, 'w', encoding='utf-8', newline='').write(h)

# ---- which parts of the screen each door shows ------------------------------------
sub("""  function openOnline() {
    elMenu.hidden = true;
    $('online').hidden = false;
    partyRender();
    if (typeof renderFriends === 'function') renderFriends();
    if (!netRole) netStatus('One of you hosts and reads out the code; everyone else types it in. Works best on a normal home connection.');
  }
  $('onlineBtn').addEventListener('click', openOnline);""",
"""  // Three ways in, and each one shows only its own half of this screen:
  // waiting for strangers, handing out a code, or typing one in.
  var netView = 'host';
  function showIf(id, on) { var el = $(id); if (el) el.hidden = !on; }
  function syncNetView() {
    var hosting = netRole === 'host', joined = netRole === 'guest';
    var quick = netView === 'quick';
    $('onlineTitle').textContent = quick ? 'QUICK PLAY' : (netView === 'join' ? 'JOIN A ROOM' : 'ROOM');
    $('onlineTag').textContent = quick ? 'waiting for whoever turns up'
      : (netView === 'join' ? 'type the code the host reads out' : 'one of you hosts, everyone else types the code');
    showIf('quickWait', quick);
    showIf('netHost', netView === 'host' && !hosting && !joined);
    showIf('netCodeBox', netView === 'host' && hosting && !!netCode);
    showIf('joinLabel', netView === 'join' && !joined);
    showIf('joinRow', netView === 'join' && !joined);
    showIf('netLeave', !!netRole);
    showIf('netStatus', !quick);
  }
  function openOnline(view) {
    if (view) netView = view;
    elMenu.hidden = true;
    $('online').hidden = false;
    partyRender();
    if (typeof renderFriends === 'function') renderFriends();
    if (!netRole && netView === 'host') netStatus('Press HOST A ROOM, then read the code out to everyone else.');
    if (!netRole && netView === 'join') netStatus('Type the five letters the host reads out.');
    syncNetView();
  }
  $('onlineBtn').addEventListener('click', function () { openOnline('host'); });
  $('joinBtn').addEventListener('click', function () {
    openOnline('join');
    setTimeout(function () { try { $('netJoinCode').focus(); } catch (err) {} }, 30);
  });""")

# the waiting room's own numbers, from the same countdown that starts the match
sub("""    if (queueSay <= 0) {
      queueSay = 0.5;
      var msg = 'Waiting for players ' + n + '/' + cap + ' \\u00b7 starting in ' + Math.max(0, Math.ceil(queueT)) + 's - bots fill any empty seats';
      quickStatus(msg);
      netSendAll({ t: 'queue', msg: msg });
    }""",
"""    if (queueSay <= 0) {
      queueSay = 0.5;
      var left = Math.max(0, Math.ceil(queueT));
      var msg = 'Waiting for players ' + n + '/' + cap + ' \\u00b7 starting in ' + left + 's - bots fill any empty seats';
      quickStatus(msg);
      if ($('quickN')) {
        $('quickN').textContent = n;
        $('quickLbl').textContent = n === 1 ? 'PLAYER WAITING' : 'PLAYERS WAITING';
        $('quickT').textContent = 'starting in ' + left + 's';
      }
      netSendAll({ t: 'queue', msg: msg });
    }""")
# quick play opens its own view
sub("""  $('quickBtn').addEventListener('click', function () { quickBegin(); quickPlay(); });""",
"""  $('quickBtn').addEventListener('click', function () { netView = 'quick'; quickBegin(); quickPlay(); });""")
# and every time the room changes, the view catches up
sub("""  function partyRender() {""",
"""  function partyRender() {
    syncNetView();""")

io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p84 applied')

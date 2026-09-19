# -*- coding: utf-8 -*-
"""Party bot settings, dropping your weapon, party chat, clearer teammate
markers, and the minimap moved to the bottom left."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ================================================================ bots ======
sub("""  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false, squad = 1;""",
    """  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false, squad = 1;
  var botFill = 1;                   // share of the usual bot count: 1, 0.5 or 0.25""")
sub("""    fieldN = MODE.field;
    if (squad > 1 && !MODE.teams && mode === 'duel') fieldN = 4;   // 1v1 becomes 2v2""",
"""    fieldN = MODE.field;
    if (squad > 1 && !MODE.teams && mode === 'duel') fieldN = 4;   // 1v1 becomes 2v2
    // fewer bots if asked, never so few there is nobody to fight
    if (botFill < 1 && mode !== 'duel' && mode !== 'tut') {
      var humN = 1 + (netRole === 'host' ? netGuests.length : 0) + (splitWant ? 1 : 0);
      fieldN = Math.max(humN + 2, Math.round(fieldN * botFill));
      if (MODE.teams && fieldN % 2) fieldN++;
    }
    alive = fieldN;""")
sub("""  $('diffRow').addEventListener('click', function (ev) {""",
"""  $('botsRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    botFill = parseFloat(b.getAttribute('data-b'));
    pressRow(this, 'data-b', b.getAttribute('data-b'));
  });
  $('diffRow').addEventListener('click', function (ev) {""")
sub("""  partyPickRow('partySquadRow', 'squadRow', 'data-s', function (v) { squad = parseInt(v, 10); });""",
"""  partyPickRow('partySquadRow', 'squadRow', 'data-s', function (v) { squad = parseInt(v, 10); });
  partyPickRow('partyDiffRow', 'diffRow', 'data-d', function (v) { difficulty = parseInt(v, 10); });
  partyPickRow('partyBotsRow', 'botsRow', 'data-b', function (v) { botFill = parseFloat(v); });""")
sub("""      pressRow($('partySquadRow'), 'data-s', String(squad));""",
    """      pressRow($('partySquadRow'), 'data-s', String(squad));
      pressRow($('partyDiffRow'), 'data-d', String(difficulty));
      pressRow($('partyBotsRow'), 'data-b', String(botFill));""")
sub("""(MODES[mode].teams ? '' : (squad > 1 ? ' \\u00b7 DUOS' : ' \\u00b7 SOLO')) });""",
    """(MODES[mode].teams ? '' : (squad > 1 ? ' \\u00b7 DUOS' : ' \\u00b7 SOLO')) +
        ' \\u00b7 ' + ['CALM', 'STANDARD', 'RUTHLESS'][difficulty] + ' BOTS' + (botFill < 1 ? (botFill < 0.5 ? ' (FEW)' : ' (HALF)') : '') });""")

# ================================================================ drop ======
sub("""  function swapSlot(n, e) {""",
"""  // Put down what is in your hands, loaded as it is, for a friend (or anyone).
  function dropWeapon(e) {
    if (!e || !e.alive || e.down || e.air || mode === 'gun') return;
    var sl = curSlot(e);
    if (!sl || !WEAPONS[sl.key]) return;
    loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: 'gun', key: sl.key,
      spin: rr(0, 6.2832), ammo: sl.ammo, n: 0, seen: true
    });
    e.slots[e.slot] = null;
    e.reloadT = 0;
    var other = e.slot === 0 ? 1 : 0;
    if (e.slots[other]) e.slot = other;
    audioEmit(e.x, e.y, PICK_SND, e.id);
  }
  function swapSlot(n, e) {""")
sub("""      if (I.hit(12)) useMed(e);""", """      if (I.hit(12)) useMed(e);
      if (I.hit(13)) dropWeapon(e);""")
sub("""      else if (k === 'v') melee(kp);""", """      else if (k === 'v') melee(kp);
      else if (k === 'z') dropWeapon(kp);""")
# the online guest's keys and buttons too
sub("""      var GB = { 'e': 0, ' ': 0, 'v': 1, 'x': 1, 'r': 2, 'f': 3, 'h': 5, 'g': 6, 'q': 14, '1': 14, '2': 14 };""",
    """      var GB = { 'e': 0, ' ': 0, 'v': 1, 'x': 1, 'r': 2, 'f': 3, 'h': 5, 'g': 6, 'q': 14, '1': 14, '2': 14, 'z': 13 };""")
sub("""        var PB = [0, 1, 2, 3, 5, 6, 14, 15, 12];""", """        var PB = [0, 1, 2, 3, 5, 6, 14, 15, 12, 13];""")

# ================================================================ party chat
sub("""  // Public-match hooks; the accounts module fills these in when it loads.""",
r"""  // ---- party chat: rides the same connection as the game ----
  var pchat = [];
  function escHtml(t) { return String(t).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function pchatAdd(from, text) {
    pchat.push({ from: from, text: text });
    if (pchat.length > 60) pchat.shift();
    var log = $('pchatLog');
    if (log) {
      var d = document.createElement('div');
      d.className = 'cmsg' + (from === (acctName || (netRole === 'host' ? 'HOST' : 'PLAYER')) ? ' me' : '');
      var b = document.createElement('b'); b.textContent = from;
      var sp = document.createElement('span'); sp.textContent = text;
      d.appendChild(b); d.appendChild(sp);
      log.appendChild(d);
      while (log.children.length > 60) log.removeChild(log.firstChild);
      log.scrollTop = log.scrollHeight;
    }
    // in a match it shows in the feed, top right
    if (state === 'play' || state === 'paused') {
      var f = document.createElement('div');
      f.className = 'you';
      f.innerHTML = '<b>' + escHtml(from) + '</b>: ' + escHtml(text);
      elFeed.appendChild(f);
      while (elFeed.children.length > 6) elFeed.removeChild(elFeed.firstChild);
      setTimeout(function () { if (f.parentNode) f.parentNode.removeChild(f); }, 9000);
    }
  }
  function partySay(from, text) {
    text = cleanText(String(text || '').trim()).slice(0, 120);
    if (!text) return;
    pchatAdd(from, text);
    netSendAll({ t: 'pchat', from: from, text: text });
  }
  function sendPartyChat(text) {
    text = String(text || '').trim();
    if (!text || !netRole) return;
    if (netRole === 'host') partySay(acctName || 'HOST', text);
    else netSend({ t: 'pchat', text: text.slice(0, 120) });
  }
  function cleanText(t) { return typeof clean === 'function' ? clean(t) : t; }
  function pchatVisible() {
    var box = $('partyChat');
    if (box) box.hidden = !(netRole === 'guest' || (netRole === 'host' && netGuests.length > 0));
  }

  // Public-match hooks; the accounts module fills these in when it loads.""")
sub("""    } else if (m.t === 'hi') {""", """    } else if (m.t === 'pchat') {
      partySay(g.name, m.text);
    } else if (m.t === 'hi') {""")
sub("""    else if (m.t === 'party') {""", """    else if (m.t === 'pchat') pchatAdd(m.from, m.text);
    else if (m.t === 'party') {""")
sub("""    // the host picks the match right here once anyone has joined
    var pp = $('partyPick');""", """    pchatVisible();
    // the host picks the match right here once anyone has joined
    var pp = $('partyPick');""")
sub("""  $('partyStart').addEventListener('click', function () { startMatch(); });""",
"""  $('partyStart').addEventListener('click', function () { startMatch(); });
  $('pchatSend').addEventListener('click', function () { sendPartyChat($('pchatInput').value); $('pchatInput').value = ''; });
  $('pchatInput').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') { sendPartyChat(this.value); this.value = ''; }
  });
  // in a match: T (or Enter) to say something to the party
  $('igChatInput').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') { sendPartyChat(this.value); this.value = ''; closeIgChat(); }
    else if (ev.key === 'Escape') closeIgChat();
  });
  function openIgChat() { keys = {}; mouse.down = false; $('igChat').hidden = false; $('igChatInput').focus(); }
  function closeIgChat() { $('igChat').hidden = true; $('igChatInput').blur(); }""")
sub("""    if (netGuest && state === 'play') {
      var GB =""", """    if (netRole && (state === 'play') && (k === 't' || k === 'enter') && $('igChat').hidden) { e.preventDefault(); openIgChat(); return; }
    if (netGuest && state === 'play') {
      var GB =""")
# a new party starts with a clean log; leaving clears it
sub("""    netConn = null; netPeer = null; netRole = null; netPublic = false; netCode = '';""",
    """    netConn = null; netPeer = null; netRole = null; netPublic = false; netCode = '';
    pchat = []; if ($('pchatLog')) $('pchatLog').innerHTML = '';""")

# ================================================================ markers ===
# People on your side stand out: gold for real players, cyan for bots, both
# with a dark outline so they read on any ground. Players are always shown,
# even far off, with their name.
a = s.index("  function renderAllies() {")
b = s.index("  // Objectives are map knowledge")
s = s[:a] + r"""  function renderAllies() {
    if (!player.alive) return;
    var mates = [];
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (a === player || !a.alive || a.air === 'plane' || a.team !== player.team) continue;
      mates.push(a);
    }
    if (!mates.length) return;
    // real players first, then the nearest bots
    mates.sort(function (x, y) {
      return ((x.bot ? 1 : 0) - (y.bot ? 1 : 0)) || (dist(x, player) - dist(y, player));
    });
    var shownBots = 0;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    for (var m = 0; m < mates.length; m++) {
      var t = mates[m];
      if (t.bot && ++shownBots > 8) continue;
      var human = !t.bot;
      var tint = t.down ? '#ff4d8d' : (human ? '#f2bd1d' : '#7ce7d8');
      var sx = (t.x - cam.x) * zoom + cw / 2;
      var sy = (t.y - cam.y) * zoom + ch / 2;
      var pad = 30;
      var off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
      var ang = Math.atan2(t.y - player.y, t.x - player.x);
      var d = Math.round(dist(t, player));
      sx = clamp(sx, pad, cw - pad);
      sy = clamp(sy, pad, ch - pad);
      ctx.fillStyle = tint;
      ctx.strokeStyle = '#0d0f12';
      if (off) {
        ctx.save();
        ctx.translate(sx, sy);
        ctx.rotate(ang);
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(-7, -8); ctx.lineTo(8, 0); ctx.lineTo(-7, 8); ctx.closePath();
        ctx.stroke(); ctx.fill();
        ctx.restore();
        ctx.font = '700 9px "IBM Plex Mono", monospace';
        ctx.lineWidth = 3;
        var lbl = (human ? t.name + ' ' : '') + d + 'u';
        ctx.strokeText(lbl, sx, sy + 18); ctx.fillText(lbl, sx, sy + 18);
      } else {
        // a solid marker and a name over their head
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(sx - 8, sy - 30); ctx.lineTo(sx + 8, sy - 30); ctx.lineTo(sx, sy - 19); ctx.closePath();
        ctx.stroke(); ctx.fill();
        ctx.font = (human ? '700 10px' : '600 9px') + ' "IBM Plex Mono", monospace';
        var nm = t.down ? t.name + ' DOWN' : t.name;
        ctx.strokeText(nm, sx, sy - 40); ctx.fillText(nm, sx, sy - 40);
      }
    }
    ctx.textAlign = 'left';
    ctx.restore();
  }

""" + s[b:]

# ================================================================ minimap ===
sub("""    var S = Math.round(Math.min(148, Math.min(cw, ch) * 0.30));
    var bx = 16, by = 16;""",
"""    var S = Math.round(Math.min(148, Math.min(cw, ch) * 0.30));
    // bottom left, above your health and kit
    var bx = 16, by = Math.max(60, ch - S - (splitOn ? 78 : 158));""")
# the tutorial box no longer needs to dodge a top-left map
sub("""    var miniB = SET.minimap ? 16 + Math.round(Math.min(148, Math.min(cw, ch) * 0.30)) + 12 : 0;""",
    """    var miniB = 0;""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ================================================================ html ======
h = io.open(H, encoding='utf-8').read()
def hsub(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

hsub("""          <button class="go" id="partyStart" type="button">START MATCH</button>""",
"""          <div class="pick">
            <p>BOTS</p>
            <div class="row" id="partyDiffRow">
              <button type="button" data-d="0">CALM</button>
              <button type="button" data-d="1">STANDARD</button>
              <button type="button" data-d="2">RUTHLESS</button>
            </div>
            <div class="row" id="partyBotsRow">
              <button type="button" data-b="1">FULL LOBBY</button>
              <button type="button" data-b="0.5">HALF</button>
              <button type="button" data-b="0.25">FEW</button>
            </div>
          </div>
          <button class="go" id="partyStart" type="button">START MATCH</button>""")
hsub("""        <div class="plist" id="partyList" hidden></div>""",
"""        <div class="plist" id="partyList" hidden></div>
        <div class="pchat" id="partyChat" hidden>
          <div class="chatlog small" id="pchatLog"></div>
          <div class="joinrow">
            <input class="wide chatin" id="pchatInput" maxlength="120" placeholder="PARTY CHAT" autocomplete="off" aria-label="Party chat">
            <button class="go ghost" id="pchatSend" type="button">SEND</button>
          </div>
        </div>""")
# main menu: how many bots
hsub("""        <p class="modedesc" id="modeDesc"></p>""",
"""        <div class="pick">
          <p>BOTS</p>
          <div class="row" id="botsRow">
            <button type="button" data-b="1" aria-pressed="true">FULL LOBBY</button>
            <button type="button" data-b="0.5" aria-pressed="false">HALF</button>
            <button type="button" data-b="0.25" aria-pressed="false">FEW</button>
          </div>
        </div>
        <p class="modedesc" id="modeDesc"></p>""")
# in-match chat line
hsub("""  <div class="toast" id="inviteToast" hidden>""",
"""  <div class="igchat" id="igChat" hidden>
    <input id="igChatInput" maxlength="120" placeholder="SAY TO YOUR PARTY - ENTER TO SEND, ESC TO CANCEL" autocomplete="off" aria-label="Party chat">
  </div>

  <div class="toast" id="inviteToast" hidden>""")
hsub(""".ptitle{""", """.pchat{width:100%;display:flex;flex-direction:column;align-items:center;gap:8px}
.chatlog.small{height:min(24vh,170px)}
.igchat{position:absolute;left:50%;bottom:120px;transform:translateX(-50%);z-index:25;width:min(520px,calc(100% - 32px))}
.igchat input{width:100%;padding:10px 12px;font-family:var(--font-m);font-size:13px;background:rgba(241,231,208,.95);color:var(--out);border:3px solid var(--out);border-radius:4px}
.ptitle{""")
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p54 applied')

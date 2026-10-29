# -*- coding: utf-8 -*-
"""Two ways online, named for what they do: QUICK PLAY looks for people,
HOST A ROOM hands you a code."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
h = io.open(H, encoding='utf-8').read(); ho = h

def sub(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

# ---- the menu: two buttons that say what they are ---------------------------------
sub("""        <button class="go ghost" id="quickBtn" type="button">QUICK PLAY ONLINE</button>
        <button class="go ghost" id="onlineBtn" type="button">PARTY</button>""",
"""        <button class="go ghost" id="quickBtn" type="button">QUICK PLAY</button>
        <button class="go ghost" id="onlineBtn" type="button">HOST A ROOM</button>""")
sub("""      <div class="mbtns">""",
"""      <p class="onlinehint">QUICK PLAY looks for other people for 20 seconds, then starts and fills the empty seats with bots &#183; HOST A ROOM gives you a code to share</p>
      <div class="mbtns">""")

# ---- the room screen: hosting on top, joining underneath ---------------------------
sub("""        <h2 class="ptitle">PARTY</h2>
        <div class="rule"></div>
        <div class="tag">friends drop into your matches with you</div>
      </div>
      <p class="modedesc" id="netStatus">Host a party, or join one with a code.</p>
      <div class="pbtns">
        <button class="go" id="netHost" type="button">HOST A PARTY</button>""",
"""        <h2 class="ptitle">ROOM</h2>
        <div class="rule"></div>
        <div class="tag">one of you hosts, everyone else types the code</div>
      </div>
      <p class="modedesc" id="netStatus">Host a room and read out the code, or type someone else's code below.</p>
      <div class="pbtns">
        <button class="go" id="netHost" type="button">HOST A ROOM</button>""")
sub("""        <div class="netcode" id="netCodeBox" hidden>PARTY CODE<b id="netCode">-----</b></div>""",
    """        <div class="netcode" id="netCodeBox" hidden>ROOM CODE<b id="netCode">-----</b></div>""")
sub("""        <div class="joinrow">
          <input id="netJoinCode" maxlength="5" placeholder="CODE" autocomplete="off" spellcheck="false" aria-label="Party code">
          <button class="go ghost" id="netJoin" type="button">JOIN</button>
        </div>""",
"""        <p class="joinlabel">OR JOIN SOMEONE ELSE'S ROOM</p>
        <div class="joinrow">
          <input id="netJoinCode" maxlength="5" placeholder="CODE" autocomplete="off" spellcheck="false" aria-label="Room code">
          <button class="go ghost" id="netJoin" type="button">JOIN</button>
        </div>""")
sub("""        <button class="go ghost" id="netLeave" type="button">LEAVE PARTY</button>""",
    """        <button class="go ghost" id="netLeave" type="button">LEAVE ROOM</button>""")

# ---- a little room to breathe for the two new lines ---------------------------------
sub(""".modedesc{margin:0;""",
""".onlinehint{margin:-6px 0 0;max-width:46ch;font-family:var(--font-m);font-size:10px;line-height:1.6;color:var(--khaki);opacity:.85}
.joinlabel{margin:10px 0 2px;font-family:var(--font-m);font-size:10px;letter-spacing:.18em;color:var(--gold)}
.modedesc{margin:0;""")

assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)

# ---- the words the game says about itself ----------------------------------------------
s = io.open(G, encoding='utf-8').read(); so = s
pairs = [
    ("'One of you hosts, the other joins with the code. Works best on a normal home connection.'",
     "'One of you hosts and reads out the code; everyone else types it in. Works best on a normal home connection.'"),
    ("'Party open. Share the invite link or this code.'", "'Room open. Share the invite link or this code.'"),
    ("'Party open. Friends join with this code, or invite them from your friends list.'",
     "'Room open. Everyone joins with this code, or from your friends list.'"),
    ("'You are in a party - the leader starts the match.'", "'You are in a room - the host starts the match.'"),
    ("'In the party. The host picked '", "'In the room. The host picked '"),
    ("'Connected! Waiting for the host to start a match.'", "'Connected. Waiting for the host to start the match.'"),
]
for a, b in pairs:
    if a in s:
        s = s.replace(a, b, 1)
if s != so:
    io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p82 applied')

# -*- coding: utf-8 -*-
"""New controller layout, one table for everyone (you, split-screen P2 and
online guests), and a HUD that shows the pad buttons and both weapons."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# one table of which button does what (standard gamepad button numbers)
sub("""  function inputFor(e) {""",
"""  // A reload (and jump) - B drop (give up when downed) - X pick up - Y stim
  // LB/RB swap - LT sprint - RT fire - d-pad left frag, right smoke, up melee
  // (the right stick click melees too) - Start pause
  var PAD = { reload: 0, jump: 0, drop: 1, giveup: 1, pickup: 2, stim: 3, swapL: 4, swapR: 5,
              sprint: 6, fire: 7, pause: 9, melee2: 11, melee: 12, frag: 14, smoke: 15 };
  function inputFor(e) {""")
sub("""      if (I.hit(0)) playerPickup(e);
      if (I.hit(1)) melee(e);
      if (I.hit(2)) startReload(e);
      if (I.hit(3)) useMed(e);
      if (I.hit(14) || I.hit(15)) swapSlot(undefined, e);
      if (I.hit(5)) throwNade(e, 'smoke');
      if (I.hit(6)) throwNade(e, 'frag');
      if (I.hit(12)) useMed(e);
      if (I.hit(13)) dropWeapon(e);
      if (I.hit(9)) { pause(); return; }""",
"""      if (I.hit(PAD.pickup)) playerPickup(e);
      if (I.hit(PAD.drop)) dropWeapon(e);
      if (I.hit(PAD.reload)) startReload(e);
      if (I.hit(PAD.stim)) useMed(e);
      if (I.hit(PAD.swapL) || I.hit(PAD.swapR)) swapSlot(undefined, e);
      if (I.hit(PAD.frag)) throwNade(e, 'frag');
      if (I.hit(PAD.smoke)) throwNade(e, 'smoke');
      if (I.hit(PAD.melee) || I.hit(PAD.melee2)) melee(e);
      if (I.hit(PAD.pause)) { pause(); return; }""")
sub("""    var sprinting = ((I.kb && !!keys['shift']) || (!!I.pad && I.down(4))) && (ix || iy);""",
    """    var sprinting = ((I.kb && !!keys['shift']) || (!!I.pad && I.down(PAD.sprint))) && (ix || iy);""")
sub("""      var go = (I.pad && I.hit(0)) || (I.kb && e.jumpReq);""",
    """      var go = (I.pad && (I.hit(PAD.jump) || I.hit(PAD.pickup))) || (I.kb && e.jumpReq);""")

# online guests: keys and pad buttons go over as the same button numbers
sub("""      var GB = { 'e': 0, ' ': 0, 'v': 1, 'x': 1, 'r': 2, 'f': 3, 'h': 5, 'g': 6, 'q': 14, '1': 14, '2': 14, 'z': 13 };""",
    """      var GB = { 'e': PAD.pickup, ' ': PAD.jump, 'v': PAD.melee, 'x': PAD.giveup, 'r': PAD.reload, 'f': PAD.stim,
                 'h': PAD.smoke, 'g': PAD.frag, 'q': PAD.swapL, '1': PAD.swapL, '2': PAD.swapL, 'z': PAD.drop };""")
sub("""        var PB = [0, 1, 2, 3, 5, 6, 14, 15, 12, 13];
        for (i = 0; i < PB.length; i++) if (padHit(PB[i])) hitsNow |= 1 << (PB[i] === 15 ? 14 : (PB[i] === 12 ? 3 : PB[i]));
        if (padHit(9)) pause();
        if (padDown(4)) down |= 1 << 4;""",
"""        var PB = [PAD.reload, PAD.drop, PAD.pickup, PAD.stim, PAD.swapL, PAD.swapR, PAD.melee, PAD.melee2, PAD.frag, PAD.smoke];
        for (i = 0; i < PB.length; i++) if (padHit(PB[i])) hitsNow |= 1 << PB[i];
        if (padHit(PAD.pause)) pause();
        if (padDown(PAD.sprint)) down |= 1 << PAD.sprint;""")
sub("""      if (keys['shift']) down |= 1 << 4;""", """      if (keys['shift']) down |= 1 << PAD.sprint;""")

# HUD: the pad's buttons for kit, and both guns with how to swap
sub("""    if (mk) mk.textContent = promptKey('F', 'Y');
    if (nk) nk.textContent = promptKey('G', 'LT');
    if (sk2) sk2.textContent = promptKey('H', 'RB');""",
"""    if (mk) mk.textContent = promptKey('F', 'Y');
    if (nk) nk.textContent = promptKey('G', 'D-PAD \\u25c0');
    if (sk2) sk2.textContent = promptKey('H', 'D-PAD \\u25b6');""")
sub("""      elSlot[k].textContent = (k + 1) + ' ' + (s ? WEAPONS[s.key].name : '\\u2014');""",
    """      var nm = s ? WEAPONS[s.key].name : '\\u2014';
      elSlot[k].textContent = usingPad(player) ? (k === 0 ? 'LB  ' + nm : nm + '  RB') : (k + 1) + '  ' + nm;""")
# on-screen prompts
sub("""    ctx.fillText(promptKey('E', 'A'), bx + 14, by + boxH / 2 + 1);""", """    ctx.fillText(promptKey('E', 'X'), bx + 14, by + boxH / 2 + 1);""")

# tutorial says the new buttons
for a, b in [
    ("p: 'X to reload',", "p: 'A to reload',"),
    ("p: 'Walk to the rifle (gold marker) and press A'", "p: 'Walk to the rifle (gold marker) and press X'"),
    ("p: 'D-PAD LEFT / RIGHT swaps weapons',", "p: 'LB or RB swaps weapons',"),
    ("p: 'Hold LB while walking - fast, but loud',", "p: 'Hold LT while walking - fast, but loud',"),
    ("p: 'LT throws a frag - hit the group',", "p: 'D-PAD LEFT throws a frag - hit the group',"),
    ("p: 'RB throws smoke - nobody sees through it',", "p: 'D-PAD RIGHT throws smoke - nobody sees through it',"),
    ("p: 'B swings the gun butt - works with no ammo',", "p: 'D-PAD UP (or click the right stick) swings the gun butt',"),
]:
    sub(a, b)

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# bigger weapon chips so both guns read at a glance
h = io.open(H, encoding='utf-8').read()
a = """.slots span{font-size:9px;letter-spacing:.12em;padding:3px 8px;"""
if a not in h:
    raise SystemExit('HTML PATTERN NOT FOUND')
h = h.replace(a, """.slots span{font-size:10.5px;font-weight:600;letter-spacing:.12em;padding:5px 11px;""", 1)
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p59 applied')

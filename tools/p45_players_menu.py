# -*- coding: utf-8 -*-
"""The PLAYERS pick on the menu: one player, or two on a split screen."""
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

sub("""  $('lightRow').addEventListener('click', function (ev) {""",
"""  $('playersRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    splitWant = b.getAttribute('data-n') === '2';
    pressRow(this, 'data-n', splitWant ? '2' : '1');
    syncMenu();
  });
  $('lightRow').addEventListener('click', function (ev) {""")

sub("""    if (blackout) t += '  \\u2014  BLACKOUT:""",
"""    if (splitWant) {
      var np = padIndices().length;
      t += np >= 2 ? '  \\u2014  SPLIT SCREEN: one controller each.'
         : np === 1 ? '  \\u2014  SPLIT SCREEN: P1 on keyboard and mouse, P2 on the controller.'
         : '  \\u2014  SPLIT SCREEN: plug in a controller for player 2 and press a button on it.';
      if (squad < 2 && !MODE_TEAMMATES[mode]) t += ' In solo you two are rivals; pick DUOS to team up.';
    }
    if (blackout) t += '  \\u2014  BLACKOUT:""")

sub("""  function syncMenu() {""",
"""  var MODE_TEAMMATES = { team: 1, war: 1, ctf: 1, sect: 1, zomb: 1 };
  function syncMenu() {""")

# the menu text depends on how many pads are plugged in
sub("""  window.addEventListener('gamepadconnected', function () { padSeen = true; syncSettings(); });""",
    """  window.addEventListener('gamepadconnected', function () { padSeen = true; syncSettings(); syncMenu(); });""")

assert s != o
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('p45 applied')

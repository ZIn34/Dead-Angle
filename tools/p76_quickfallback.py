# -*- coding: utf-8 -*-
"""QUICK PLAY has to end in a match. The deadline is anchored to the click, so
nothing inside the online code can push it back by retrying."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""  // Whatever goes wrong out there - their SDK blocked, the broker down, an
  // empty site - the button has to end in a match, not a spinner.
  var quickGuard = 0;
  function quickWatch() {
    clearTimeout(quickGuard);
    quickGuard = setTimeout(function () {
      if (state === 'play' || state === 'paused') return;   // already playing
      if (queueOn || netRole === 'guest') return;           // in a lobby, leave it alone
      quickStatus('No match to join - starting one with bots.');
      if (netRole) netClose('');
      setTimeout(function () { if (state !== 'play') startMatch(); }, 700);
    }, 10000);
  }
  function quickPlay() {
    quickWatch();""",
"""  // Whatever goes wrong out there - the broker down, their sandbox blocking
  // it, an empty site - the button has to end in a match rather than a
  // spinner. The clock starts when the player clicks and nothing inside the
  // online code can push it back, because all of that is what might be stuck.
  var QUICK_WAIT = 12000, quickAt = 0, quickTimer = 0;
  function quickStand() { clearInterval(quickTimer); quickTimer = 0; }
  function quickBegin() {
    quickAt = performance.now();
    clearInterval(quickTimer);
    quickTimer = setInterval(function () {
      if (state === 'play' || state === 'paused') { quickStand(); return; }
      // a lobby is really holding a seat for us: it starts the match itself
      if (queueOn && netRole === 'host') { quickStand(); return; }
      if (netGuest && netConn && netConn.open) { quickStand(); return; }
      if (performance.now() - quickAt < QUICK_WAIT) return;
      quickStand();
      quickStatus('No match to join - starting one with bots.');
      if (netRole) netClose('');
      setTimeout(function () { if (state !== 'play') startMatch(); }, 700);
    }, 400);
  }
  function quickPlay() {""")
sub("""  $('quickBtn').addEventListener('click', quickPlay);""",
    """  $('quickBtn').addEventListener('click', function () { quickBegin(); quickPlay(); });""")
# leaving the online screen by hand calls it off
sub("""  $('netBack').addEventListener('click', function () {""",
    """  $('netBack').addEventListener('click', function () {
    quickStand();""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p76 applied')

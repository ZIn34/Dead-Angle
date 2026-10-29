# -*- coding: utf-8 -*-
"""Twenty people on one host is twenty copies of the world going out every
tick. The rate and the interest radius now tighten as the room fills."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""  var NET_SEE = 1500;                       // how far a guest is told about""",
"""  var NET_SEE = 1500;                       // how far a guest is told about
  // The host pays for every guest separately, so a full room sends a little
  // less often and tells each person about a little less of the map. Six
  // friends notice nothing; twenty people get a match that still keeps up on
  // an ordinary home connection.
  function seeRadius() {
    var n = netGuests.length;
    return n > 12 ? 1050 : (n > 6 ? 1250 : NET_SEE);
  }
  function sendHz() {
    var n = netGuests.length;
    return n > 12 ? 12 : (n > 6 ? 15 : 20);
  }""")
sub("""    var ge = guestEye(g);
    if (!ge) return true;
    var dx = x - ge.x, dy = y - ge.y;
    return dx * dx + dy * dy < NET_SEE * NET_SEE;""",
"""    var ge = guestEye(g);
    if (!ge) return true;
    var dx = x - ge.x, dy = y - ge.y, r = seeRadius();
    return dx * dx + dy * dy < r * r;""")
sub("""    netSendT = 1 / 20;""", """    netSendT = 1 / sendHz();""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p78 applied')

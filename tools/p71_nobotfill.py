# -*- coding: utf-8 -*-
"""Out goes the FULL LOBBY / HALF / FEW picker: every match fills up."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""  var botFill = 1;                   // share of the usual bot count: 1, 0.5 or 0.25
""", "")
sub("""    // fewer bots if asked, never so few there is nobody to fight
    if (botFill < 1 && mode !== 'duel' && mode !== 'tut') {
      var humN = 1 + (netRole === 'host' ? netGuests.length : 0) + (splitWant ? 1 : 0);
      fieldN = Math.max(humN + 2, Math.round(fieldN * botFill));
      if (MODE.teams && fieldN % 2) fieldN++;
    }
""", "")
sub("""  partyPickRow('partyBotsRow', 'botsRow', 'data-b', function (v) { botFill = parseFloat(v); });
""", "")
sub("""  $('botsRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    botFill = parseFloat(b.getAttribute('data-b'));
    pressRow(this, 'data-b', b.getAttribute('data-b'));
  });
""", "")
sub("""        ' \\u00b7 ' + ['CALM', 'STANDARD', 'RUTHLESS'][difficulty] + ' BOTS' + (botFill < 1 ? (botFill < 0.5 ? ' (FEW)' : ' (HALF)') : '') });""",
    """        ' \\u00b7 ' + ['CALM', 'STANDARD', 'RUTHLESS'][difficulty] + ' BOTS' });""")
sub("""      pressRow($('partyBotsRow'), 'data-b', String(botFill));
""", "")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read(); ho = h
for block in ["""        <div class="pick">
          <p>BOTS</p>
          <div class="row" id="botsRow">
            <button type="button" data-b="1" aria-pressed="true">FULL LOBBY</button>
            <button type="button" data-b="0.5" aria-pressed="false">HALF</button>
            <button type="button" data-b="0.25" aria-pressed="false">FEW</button>
          </div>
        </div>
""", """            <div class="row" id="partyBotsRow">
              <button type="button" data-b="1">FULL LOBBY</button>
              <button type="button" data-b="0.5">HALF</button>
              <button type="button" data-b="0.25">FEW</button>
            </div>
"""]:
    if block not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + block[:120])
    h = h.replace(block, '', 1)
assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p71 applied')

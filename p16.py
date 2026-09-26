# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

sub("""  $('startBtn').addEventListener('click', startMatch);
  $('againBtn').addEventListener('click', function () { elOver.hidden = true; elMenu.hidden = false; state = 'menu'; });""",
"""  function refreshCoins() {
    var a = $('menuCoins'), b = $('coinsN');
    if (a) a.textContent = WALLET.coins;
    if (b) b.textContent = WALLET.coins;
  }

  // The shop previews each skin by composing it exactly as the game would.
  function buildShop() {
    var grid = $('shopGrid');
    if (!grid) return;
    grid.innerHTML = '';
    for (var i = 0; i < 16; i++) (function (idx) {
      var card = document.createElement('div');
      card.className = 'skincard' + (WALLET.skin === idx ? ' on' : '') + (skinOwned(idx) ? '' : ' locked');
      var pv = document.createElement('canvas');
      pv.width = 104; pv.height = 156;
      if (PACK_READY) {
        var src = buildChar(idx, 'smg');
        pv.getContext('2d').drawImage(src, 0, 0, src.width, src.height, 0, 0, 104, 156);
      }
      card.appendChild(pv);
      var lab = document.createElement('span');
      lab.textContent = skinOwned(idx)
        ? (WALLET.skin === idx ? 'WEARING' : 'SELECT')
        : skinPrice(idx) + ' CR';
      card.appendChild(lab);
      card.addEventListener('click', function () {
        if (skinOwned(idx)) {
          WALLET.skin = idx;
        } else if (WALLET.coins >= skinPrice(idx)) {
          WALLET.coins -= skinPrice(idx);
          WALLET.owned.push(idx);
          WALLET.skin = idx;
        } else {
          lab.textContent = 'NEED ' + (skinPrice(idx) - WALLET.coins);
          return;
        }
        saveWallet();
        refreshCoins();
        buildShop();
      });
      grid.appendChild(card);
    })(i);
  }

  function goHome() {
    state = 'menu';
    keys = {}; mouse.down = false;
    elOver.hidden = true; elHud.hidden = true; elPaused.hidden = true;
    $('shop').hidden = true;
    elMenu.hidden = false;
    refreshCoins();
  }

  $('shopBtn').addEventListener('click', function () {
    buildShop(); refreshCoins();
    elMenu.hidden = true;
    $('shop').hidden = false;
  });
  $('shopBack').addEventListener('click', function () {
    $('shop').hidden = true;
    elMenu.hidden = false;
  });

  $('startBtn').addEventListener('click', startMatch);
  $('againBtn').addEventListener('click', function () { elOver.hidden = true; startMatch(); });
  $('homeBtn').addEventListener('click', goHome);""")

sub("""  resize();
  buildTextures();
  syncMenu();""",
"""  resize();
  buildTextures();
  loadWallet();
  refreshCoins();
  syncMenu();""")

# leaving a match should use the same path as the results screen's HOME
sub("""  function leaveMatch() {
    state = 'menu';
    keys = {}; mouse.down = false;
    elPaused.hidden = true; elHud.hidden = true; elOver.hidden = true;
    elMenu.hidden = false;
  }""",
"""  function leaveMatch() { goHome(); }""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p16 applied')

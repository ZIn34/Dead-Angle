# -*- coding: utf-8 -*-
"""Menus in the asset pack's look: gold, navy, dirt, heavy black outlines."""
import io, re

H = r'C:\Users\micha\Documents\dead-angle\index.html'
G = r'C:\Users\micha\Documents\dead-angle\game.js'

s = io.open(H, encoding='utf-8').read(); o = s

s = s.replace('family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Mono',
              'family=Chakra+Petch:wght@500;600;700&family=Russo+One&family=IBM+Plex+Mono', 1)
s = s.replace('''  --font-d:"Chakra Petch"''', '''  /* the pack's own colours - menus only; the HUD keeps cyan/rose for team meaning */
  --gold:#f2bd1d;
  --gold-hi:#ffd54a;
  --navy:#2e4559;
  --navy-d:#1d2d3b;
  --navy-l:#3d5a73;
  --paper:#f1e7d0;
  --khaki:#b3a78c;
  --out:#0d0f12;
  --font-x:"Russo One","Chakra Petch",sans-serif;
  --font-d:"Chakra Petch"''', 1)

a = s.index('/* ---------- Screens ---------- */')
b = s.index('\n', s.index('.paused{', a))
CSS = r'''/* ---------- Screens ---------- */
.screen{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:24px 16px;overflow-y:auto;pointer-events:auto;background:radial-gradient(120% 90% at 50% 42%,rgba(20,16,10,.25) 0%,rgba(14,12,9,.72) 60%,rgba(10,9,7,.92) 100%)}
.panel{width:100%;max-width:600px;display:flex;flex-direction:column;align-items:center;gap:22px;text-align:center}

.brand{display:flex;flex-direction:column;align-items:center;gap:12px}
h1{margin:0;font-family:var(--font-x);font-size:clamp(34px,10vw,66px);font-weight:400;letter-spacing:.08em;text-indent:.08em;line-height:.94;color:var(--paper);-webkit-text-stroke:2px var(--out);paint-order:stroke fill;text-shadow:4px 5px 0 var(--out)}
h1 .gold{color:var(--gold)}
.rule{width:110px;height:5px;background:var(--gold);border:2px solid var(--out);box-sizing:content-box}
.tag{font-family:var(--font-m);font-size:11px;letter-spacing:.3em;color:var(--khaki);text-transform:uppercase}
.premise{margin:0;max-width:48ch;font-size:14.5px;line-height:1.6;color:#d8ccb2;text-wrap:balance;text-shadow:0 1px 0 rgba(0,0,0,.6)}
.premise b{color:var(--gold);font-weight:600}

.legend{width:100%;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px;background:var(--out);border:3px solid var(--out);box-shadow:4px 4px 0 rgba(0,0,0,.45)}
.legend div{background:var(--navy);padding:9px 12px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-family:var(--font-m);font-size:10px;letter-spacing:.09em}
.legend s{text-decoration:none;display:flex;align-items:center;gap:8px;color:var(--paper)}
.legend i{width:10px;height:10px;border-radius:50%;border:1.5px solid currentColor;flex:none}
.legend u{text-decoration:none;color:var(--khaki);font-variant-numeric:tabular-nums}
.legend .hd{grid-column:1/-1;justify-content:flex-start;color:var(--gold);letter-spacing:.26em;font-size:9px;padding:7px 12px;background:var(--navy-d)}

.picks{display:flex;flex-direction:column;align-items:center;gap:14px;width:100%}
.pick{display:flex;flex-direction:column;align-items:center;gap:8px}
.pick>p{margin:0;font-family:var(--font-x);font-size:11px;letter-spacing:.24em;color:var(--gold);text-shadow:1px 1px 0 var(--out)}
.row{display:flex;flex-wrap:wrap;justify-content:center;gap:2px;background:var(--out);border:3px solid var(--out);box-shadow:3px 3px 0 rgba(0,0,0,.45)}
.row button{appearance:none;border:0;background:var(--navy);color:#c9c0ab;font-family:var(--font-m);font-size:10.5px;font-weight:500;letter-spacing:.14em;padding:9px 16px;cursor:pointer;transition:background .12s,color .12s}
.row button:hover{background:var(--navy-l);color:var(--paper)}
.row button[aria-pressed="true"]{background:var(--gold);color:var(--out);font-weight:600}
.row button:focus-visible{outline:3px solid var(--paper);outline-offset:-3px}
.modedesc{margin:0;max-width:46ch;font-family:var(--font-m);font-size:11px;line-height:1.6;color:#c2b79f;min-height:2.2em}

.ctrls{display:flex;flex-wrap:wrap;justify-content:center;gap:7px 14px;font-family:var(--font-m);font-size:10.5px;letter-spacing:.09em;color:var(--khaki)}
.ctrls span{display:flex;align-items:center;gap:5px}
.ctrls kbd{font-family:var(--font-m);font-size:10px;font-weight:600;color:var(--out);border:2px solid var(--out);border-bottom-width:3px;padding:1px 6px;background:var(--paper);border-radius:3px}

.go{appearance:none;cursor:pointer;font-family:var(--font-x);font-weight:400;font-size:18px;letter-spacing:.2em;text-indent:.2em;padding:14px 46px;color:var(--out);background:var(--gold);border:3px solid var(--out);border-radius:4px;box-shadow:0 5px 0 var(--out),0 9px 0 rgba(0,0,0,.3);transition:transform .08s,box-shadow .08s,background .12s}
.go:hover{background:var(--gold-hi);transform:translateY(-1px);box-shadow:0 6px 0 var(--out),0 10px 0 rgba(0,0,0,.3)}
.go:active{transform:translateY(4px);box-shadow:0 1px 0 var(--out),0 3px 0 rgba(0,0,0,.3)}
.go:focus-visible{outline:3px solid var(--paper);outline-offset:4px}
.go.ghost{background:var(--navy);color:var(--paper);font-size:13px;padding:11px 30px;box-shadow:0 4px 0 var(--out),0 7px 0 rgba(0,0,0,.3)}
.go.ghost:hover{background:var(--navy-l);color:var(--gold)}
.go.ghost:active{box-shadow:0 1px 0 var(--out)}
.ptitle{margin:0;font-family:var(--font-x);font-weight:400;font-size:clamp(32px,8.5vw,50px);letter-spacing:.14em;text-indent:.14em;line-height:1;color:var(--paper);-webkit-text-stroke:2px var(--out);paint-order:stroke fill;text-shadow:4px 4px 0 var(--out)}
.pbtns{display:flex;flex-direction:column;align-items:center;gap:16px}
.setlist{width:100%;max-width:440px;display:flex;flex-direction:column;gap:2px;background:var(--out);border:3px solid var(--out);box-shadow:4px 4px 0 rgba(0,0,0,.45)}
.setrow{background:var(--navy);padding:11px 14px;display:flex;align-items:center;gap:12px;font-family:var(--font-m);font-size:10.5px;letter-spacing:.14em;color:#d3c9b2}
.setrow span{flex:1;text-align:left}
.setrow b{font-family:var(--font-x);font-weight:400;font-size:14px;color:var(--gold);min-width:34px;text-align:right;font-variant-numeric:tabular-nums}
.setrow input[type=range]{flex:0 0 150px;accent-color:var(--gold);background:transparent}
.tgl{appearance:none;border:2px solid var(--out);background:var(--navy-d);color:var(--khaki);font-family:var(--font-m);font-size:10px;font-weight:600;letter-spacing:.16em;padding:5px 16px;cursor:pointer;border-radius:3px}
.tgl.on{background:var(--gold);color:var(--out)}
.screen button:focus,.screen input:focus{outline:3px solid var(--paper);outline-offset:3px}
.skincard:focus{outline:3px solid var(--paper);outline-offset:-3px}
.shopgrid{width:100%;flex:none;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));grid-auto-rows:minmax(104px,auto);gap:2px;background:var(--out);border:3px solid var(--out);box-shadow:4px 4px 0 rgba(0,0,0,.45)}
.skincard{background:var(--navy);padding:10px 4px 8px;display:flex;flex-direction:column;align-items:center;gap:6px;cursor:pointer;transition:background .12s}
.skincard:hover{background:var(--navy-l)}
.skincard canvas{display:block;width:52px;height:78px;flex:none}
.skincard span{font-family:var(--font-m);font-size:8.5px;font-weight:500;letter-spacing:.14em;color:#d3c9b2}
.skincard.on{background:#4a4326;box-shadow:inset 0 0 0 3px var(--gold)}
.skincard.on span{color:var(--gold)}
.skincard.locked{background:var(--navy-d)}
.skincard.locked canvas{opacity:.82}
.skincard.locked span{color:var(--gold)}
@media (max-width:480px){.shopgrid{grid-template-columns:repeat(3,minmax(0,1fr))}}

.place{display:flex;flex-direction:column;align-items:center;gap:6px}
.place b{font-family:var(--font-x);font-weight:400;font-size:clamp(54px,16vw,98px);line-height:.9;color:var(--paper);font-variant-numeric:tabular-nums;-webkit-text-stroke:3px var(--out);paint-order:stroke fill;text-shadow:5px 6px 0 var(--out)}
.place b.win{color:var(--gold)}
.place s{text-decoration:none;font-family:var(--font-m);font-size:11px;letter-spacing:.3em;color:var(--khaki)}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2px;background:var(--out);border:3px solid var(--out);width:100%;max-width:400px;box-shadow:4px 4px 0 rgba(0,0,0,.45)}
.stats div{background:var(--navy);padding:13px 8px;display:flex;flex-direction:column;gap:5px}
.stats strong{font-family:var(--font-x);font-size:22px;font-weight:400;color:var(--paper);font-variant-numeric:tabular-nums}
.stats span{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;color:var(--khaki)}

.paused{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(12,10,7,.8);font-family:var(--font-m);font-size:12px;letter-spacing:.34em;color:var(--khaki);text-align:center;padding:16px}'''
s = s[:a] + CSS + s[b:]
s = s.replace('<h1>DEAD ANGLE</h1>', '<h1>DEAD <span class="gold">ANGLE</span></h1>', 1)
assert s != o
io.open(H, 'w', encoding='utf-8', newline='').write(s)

# ---- menu backdrop: the dirt from the world map, drifting, with gold rings --
g = io.open(G, encoding='utf-8').read(); go = g
old = '''  function renderAmbient() {
    amb.t -= 1 / 60;'''
new = '''  function renderAmbient() {
    // the world's own ground, slowly drifting, pushed well back
    amb.drift = (amb.drift || 0) + 1 / 60;
    if (floorPat) {
      ctx.save();
      ctx.translate(-(amb.drift * 9) % (TILE * 8), -(amb.drift * 5) % (TILE * 8));
      ctx.fillStyle = floorPat;
      ctx.fillRect(0, 0, cw + TILE * 8, ch + TILE * 8);
      ctx.restore();
      ctx.fillStyle = 'rgba(16,13,9,.62)';
    } else {
      ctx.fillStyle = '#17140f';
    }
    ctx.fillRect(0, 0, cw, ch);
    amb.t -= 1 / 60;'''
assert old in g
g = g.replace(old, new, 1)
old2 = "      ctx.strokeStyle = 'rgba(' + g.def.color + ',' + (fade * fade * 0.5).toFixed(3) + ')';"
assert old2 in g
g = g.replace(old2, "      ctx.strokeStyle = 'rgba(242,189,29,' + (fade * fade * 0.4).toFixed(3) + ')';", 1)
io.open(G, 'w', encoding='utf-8', newline='').write(g)
print('p42 applied')

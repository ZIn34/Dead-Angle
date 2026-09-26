# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# A throw you can aim and pitch, so a bot can land one on a target rather than
# always hurling it as far as it will go.
sub("""  function throwNade(e, kind) {
    var have = kind === 'smoke' ? e.smokes : e.nades;
    if (have <= 0 || e.useT > 0 || !e.alive || e.down) return;
    if (kind === 'smoke') e.smokes--; else e.nades--;
    nades.push({
      x: e.x + Math.cos(e.ang) * (e.r + 4), y: e.y + Math.sin(e.ang) * (e.r + 4),
      vx: Math.cos(e.ang) * 430, vy: Math.sin(e.ang) * 430,
      fuse: kind === 'smoke' ? 1.05 : 1.35, spin: Math.random() * 6.2832,
      owner: e.id, kind: kind || 'frag'
    });
    emit(e.x, e.y, PIN_SND, e.id, 'pin');
  }""",
"""  function throwNade(e, kind, ang, power) {
    var have = kind === 'smoke' ? e.smokes : e.nades;
    if (have <= 0 || e.useT > 0 || !e.alive || e.down) return;
    if (kind === 'smoke') e.smokes--; else e.nades--;
    var a = (ang === undefined) ? e.ang : ang;
    var v = power || 560;
    nades.push({
      x: e.x + Math.cos(a) * (e.r + 4), y: e.y + Math.sin(a) * (e.r + 4),
      vx: Math.cos(a) * v, vy: Math.sin(a) * v,
      fuse: kind === 'smoke' ? 1.05 : 1.35, spin: Math.random() * 6.2832,
      owner: e.id, kind: kind || 'frag'
    });
    emit(e.x, e.y, PIN_SND, e.id, 'pin');
  }

  // How hard to throw so it lands about `d` away, given the skid.
  function throwPower(d) { return clamp(d * 1.95, 240, 620); }""")

sub("""      var damp = Math.pow(0.12, dt);          // skids to a stop""",
    """      var damp = Math.pow(0.2, dt);           // skids to a stop""")

sub("""      senseT: Math.random() * 0.2, stuckT: 0, lastX: 0, lastY: 0, swapT: 0,""",
    """      senseT: Math.random() * 0.2, stuckT: 0, lastX: 0, lastY: 0, swapT: 0,
      nadeT: rr(3, 9), smokeT: rr(5, 14),""")

# ------------------------------------------------------- bots use the kit ---
sub("""    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;""",
"""    e.nadeT -= dt;
    e.smokeT -= dt;
    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;""")

sub("""    // --- stuck detection
    e.stuckT += dt;""",
"""    // --- grenades. Thrown at something they can actually see, pitched to
    //     land on it, and never onto their own side.
    if (e.nades > 0 && e.nadeT <= 0 && !e.down) {
      var gt = e.target || (e.alertT > 3.5 ? { x: e.alertX, y: e.alertY } : null);
      if (gt) {
        var gd = Math.sqrt((gt.x - e.x) * (gt.x - e.x) + (gt.y - e.y) * (gt.y - e.y));
        if (gd > 105 && gd < 340 && lineClear(e.x, e.y, gt.x, gt.y)) {
          var clear = true;
          for (var fq = 0; fq < ents.length; fq++) {
            var fm = ents[fq];
            if (fm === e || !fm.alive || foes(e, fm)) continue;
            if (dist(fm, gt) < 150) { clear = false; break; }
          }
          if (clear) {
            var ga3 = Math.atan2(gt.y - e.y, gt.x - e.x) + rr(-0.09, 0.09);
            throwNade(e, 'frag', ga3, throwPower(gd));
            e.nadeT = rr(D.smart ? 6 : 13, D.smart ? 15 : 26);
            e.fireT = Math.max(e.fireT, 0.45);
          }
        }
      }
    }

    // --- smoke, to break a line they are losing
    if (D.smart && e.smokes > 0 && e.smokeT <= 0 && e.target && !e.down) {
      var wantSmoke = (e.hp < 45) || dry || (reloadRetreat && e.hp < 70) || carrying;
      var sd2 = dist(e, e.target);
      if (wantSmoke && sd2 > 90 && sd2 < 420 && lineClear(e.x, e.y, e.target.x, e.target.y)) {
        var sa3 = Math.atan2(e.target.y - e.y, e.target.x - e.x);
        throwNade(e, 'smoke', sa3, throwPower(sd2 * 0.55));
        e.smokeT = rr(16, 30);
      }
    }

    // --- stuck detection
    e.stuckT += dt;""")

# The rifle was built as a near-silent sidearm; as a 30-round automatic that
# made it both quiet and strong. Louder in the world and louder in your ears.
sub("""snd: { maxR: 220,  speed: 620,  color: '157,176,196', w: 1.3, aud: { rate: 1.70, cut: 1250, hp: 520, decay: 0.07, body: 0,   vol: 0.20 } } }""",
    """snd: { maxR: 540,  speed: 760,  color: '157,176,196', w: 1.8, aud: { rate: 1.55, cut: 1900, hp: 380, decay: 0.10, body: 96,  vol: 0.58 } } }""")

sub("""      master.gain.value = 0.5;""", """      master.gain.value = 0.66;""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p28 applied')

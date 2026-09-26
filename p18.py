# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# Recorded clips, embedded as base64 so nothing is fetched at runtime. Any
# sound def carrying a `sample` name plays the recording; the rest still use
# the synthesiser, and both go through the same distance, delay and pan.
sub("""  var actx = null, master = null, noiseBuf = null, muted = false;""",
"""  var actx = null, master = null, noiseBuf = null, muted = false;
  var SFX_BUF = {};

  function decodeSamples() {
    var src = window.EARSHOT_SFX;
    if (!src || !actx) return;
    Object.keys(src).forEach(function (name) {
      if (SFX_BUF[name]) return;
      try {
        var bin = atob(src[name]);
        var buf = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        var done = function (b) { SFX_BUF[name] = b; };
        var res = actx.decodeAudioData(buf.buffer, done, function () {});
        if (res && res.then) res.then(done, function () {});
      } catch (err) { /* a clip that will not decode simply stays synthesised */ }
    });
  }

  function sampleVoice(buf, when, gain, muffle, pan, rate) {
    var out = master;
    if (actx.createStereoPanner) {
      var pn = actx.createStereoPanner();
      pn.pan.value = clamp(pan, -1, 1);
      pn.connect(master);
      out = pn;
    }
    var src = actx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = rate || 1;
    var lp = actx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = Math.max(320, 17000 * muffle * muffle);
    var g = actx.createGain();
    g.gain.value = gain;
    src.connect(lp); lp.connect(g); g.connect(out);
    src.start(when);
  }""")

sub("""      for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    } catch (err) { actx = null; }""",
"""      for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      decodeSamples();
    } catch (err) { actx = null; }""")

sub("""  function audioEmit(x, y, def, owner) {
    if (!actx || muted || !def.aud || !player) return;""",
"""  function audioEmit(x, y, def, owner) {
    if (!actx || muted || !player) return;
    if (!def.aud && !def.sample) return;""")

sub("""    try {
      voice(def.aud, when, gain, muffle, clamp(dx / 420, -1, 1) * 0.8);
      if (def.aud.twice) voice(def.aud, when + def.aud.twice, gain * 0.8, muffle, clamp(dx / 420, -1, 1) * 0.8);
    } catch (err) { /* an audio hiccup must never break the frame */ }""",
"""    var pan = clamp(dx / 420, -1, 1) * 0.8;
    try {
      var buf = def.sample ? SFX_BUF[def.sample] : null;
      if (buf) {
        sampleVoice(buf, when, gain * (def.sampleGain || 1), muffle, pan, def.rate || 1);
      } else if (def.aud) {
        voice(def.aud, when, gain, muffle, pan);
        if (def.aud.twice) voice(def.aud, when + def.aud.twice, gain * 0.8, muffle, pan);
      }
    } catch (err) { /* an audio hiccup must never break the frame */ }""")

# the frag now uses the real recording
sub("""  var NADE_SND  = { maxR: 1900, speed: 1100, color: '255,150,60', w: 3.4,
                    aud: { rate: 0.40, cut: 1500, hp: 45, decay: 0.75, body: 52, vol: 1.0 } };""",
"""  var NADE_SND  = { maxR: 1900, speed: 1100, color: '255,150,60', w: 3.4,
                    sample: 'frag', sampleGain: 1.0,
                    aud: { rate: 0.40, cut: 1500, hp: 45, decay: 0.75, body: 52, vol: 1.0 } };""")

# a blast throws debris and dust, not a muzzle flash
sub("""    flashes.push({ x: g.x, y: g.y, ang: 0, t: 0.22, max: 0.22, tint: '#ffcf7a', scale: 3.2 });
""", "")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p18 applied')

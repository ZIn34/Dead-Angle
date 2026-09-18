# -*- coding: utf-8 -*-
"""Segment a recording of sound effects and cut each one out as its own clip."""
import os, sys, wave, array, subprocess
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
src = sys.argv[1]
tag = sys.argv[2]
os.makedirs('sfx', exist_ok=True)
wav = 'sfx/_%s.wav' % tag

subprocess.check_call([FF, '-y', '-i', src, '-vn', '-ac', '1', '-ar', '44100',
                       '-acodec', 'pcm_s16le', wav],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

w = wave.open(wav, 'rb')
sr = w.getframerate()
pcm = array.array('h')
pcm.frombytes(w.readframes(w.getnframes()))
w.close()

BLK = int(sr * 0.005)
env, peak = [], 1
for i in range(0, len(pcm) - BLK, BLK):
    m = 0
    for j in range(i, i + BLK, 4):
        v = pcm[j]
        if v < 0: v = -v
        if v > m: m = v
    env.append(m)
    if m > peak: peak = m

thresh = max(peak * 0.06, 200)
GAP = int(0.11 / 0.005)
segs, start, quiet = [], None, 0
for i, v in enumerate(env):
    if v >= thresh:
        if start is None: start = i
        quiet = 0
    elif start is not None:
        quiet += 1
        if quiet >= GAP:
            segs.append((start, i - quiet)); start = None; quiet = 0
if start is not None:
    segs.append((start, len(env) - 1))
segs = [(a, b) for a, b in segs if (b - a) * 0.005 > 0.04]

print('%s: %.2fs, peak %d, %d effects' % (tag, len(pcm) / float(sr), peak, len(segs)))
gain = 26000.0 / peak

for k, (a, b) in enumerate(segs):
    s0 = max(0, int((a * 0.005 - 0.012) * sr))
    s1 = min(len(pcm), int((b * 0.005 + 0.09) * sr))
    clip = array.array('h', pcm[s0:s1])
    fade = int(sr * 0.008)
    for i in range(len(clip)):
        v = clip[i] * gain
        if i < fade: v *= i / float(fade)
        if i > len(clip) - fade: v *= (len(clip) - i) / float(fade)
        clip[i] = max(-32767, min(32767, int(v)))
    name = 'sfx/%s_%02d.wav' % (tag, k)
    o = wave.open(name, 'wb')
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes(clip.tobytes())
    o.close()
    pk = max(env[a:b + 1]) if b > a else 0
    print('  %2d  %6.2fs  %5.0f ms  peak %5d  -> %s' % (k, a * 0.005, (b - a) * 0.005 * 1000, pk, name))

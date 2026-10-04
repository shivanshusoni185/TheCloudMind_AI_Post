"""Step 4: original procedural score + editorial SFX, ducked under narration,
mixed and loudness-normalised (-14 LUFS integrated, <= -1 dBTP)."""
import json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT
import scenes as S

SR = 48000
TL = S.TL; TOTAL = TL["total"]; N = int(round(TOTAL * SR))
BPM = 88; BEAT = 60 / BPM; BAR = 4 * BEAT
rng = np.random.default_rng(1)
st = {s["id"]: s["start"] for s in TL["scenes"]}
def G(sid, t): return st[sid] + t          # scene-local -> global time

def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc, order=2): return sosfilt(butter(order, fc / (SR / 2), "low", output="sos"), x)
def hp(x, fc, order=2): return sosfilt(butter(order, fc / (SR / 2), "high", output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), x)
tt = np.arange(N) / SR

def env_curve(points):
    """Piecewise-linear automation from (time, value) pairs."""
    p = sorted(points); return np.interp(tt, [a for a, _ in p], [b for _, b in p]).astype(np.float32)

# ------------------------------------------------------------ harmony (D major colour)
CHORDS = {  # midi notes
    "D": [50, 57, 62, 64, 66, 69], "Bm": [47, 54, 59, 61, 62, 66], "G": [43, 50, 55, 59, 62, 66, 69],
    "A": [45, 52, 57, 59, 64, 66], "Em": [40, 47, 52, 55, 59, 62], "F#m": [42, 49, 54, 57, 61, 64],
}
PROG = ["D", "Bm", "G", "A", "D", "F#m", "G", "A", "Em", "G", "D", "A"]

def chord_at(t):
    return PROG[int(t // (2 * BAR)) % len(PROG)]

# ------------------------------------------------------------ section automation (brief's music arc)
e = lambda sid: st[sid]
pad_amt = env_curve([(0, 0), (4, 0.7), (e(3), 0.75), (e(5), 0.95), (e(9), 0.9), (e(11), 0.85), (TOTAL - 3, 0.6), (TOTAL, 0)])
arp_amt = env_curve([(0, 0), (6, 0.0), (10, 0.35), (e(3), 0.5), (e(5), 0.6), (e(7), 0.75), (e(8), 0.95), (e(9), 0.7), (e(11), 0.45), (TOTAL - 4, 0.2), (TOTAL, 0)])
pulse_amt = env_curve([(0, 0), (e(3) - 1, 0), (e(3) + 2, 0.45), (e(5), 0.25), (e(6), 0.45), (e(7), 0.75), (e(8), 0.6), (e(9) - 0.5, 0.0), (TOTAL, 0)])
str_amt = env_curve([(0, 0), (e(5) - 1, 0), (e(5) + 3, 0.55), (e(6), 0.45), (e(7), 0.75), (e(8), 0.95), (e(9), 0.35), (e(11), 0.5), (TOTAL - 2, 0.3), (TOTAL, 0)])
bright = env_curve([(0, 1400), (e(5), 2400), (e(7), 2800), (e(8), 4200), (e(9), 3200), (e(11), 2200), (TOTAL, 1200)])
air_amt = env_curve([(0, 0.2), (e(9) - 1, 0.2), (e(9) + 2, 0.8), (e(11), 0.5), (TOTAL, 0.2)])

def pad():
    out = np.zeros((2, N), np.float32)
    seglen = 2 * BAR; nseg = int(TOTAL / seglen) + 2
    for k in range(nseg):
        t0 = k * seglen
        if t0 >= TOTAL: break
        name = chord_at(t0 + 0.01) if t0 < TOTAL - 2 * seglen else "D"
        i0 = int(t0 * SR); n = int((seglen + 1.6) * SR); i1 = min(N, i0 + n); n = i1 - i0
        lt = np.arange(n) / SR
        env = np.clip(lt / 1.4, 0, 1) * np.clip((seglen + 1.6 - lt) / 1.6, 0, 1)
        for ch in range(2):
            sig = np.zeros(n)
            for m in CHORDS[name]:
                for det in (-0.07, 0.06):
                    f = midi(m + 12 * (m < 48)) * 2 ** ((det + (0.03 if ch else -0.03)) / 12)
                    ph = rng.random() * 6.28
                    sig += np.sin(2 * np.pi * f * lt + ph) * 0.6 + 0.25 * np.sin(4 * np.pi * f * lt + ph) + 0.1 * np.sin(6 * np.pi * f * lt)
            out[ch, i0:i1] += (sig * env).astype(np.float32) * 0.035
    return out

def bell(f, dur, amp):
    n = int(dur * SR); lt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * lt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * lt) * np.exp(-lt * 6) + 0.2 * np.sin(2 * np.pi * f * 5.4 * lt) * np.exp(-lt * 12))
    return (s * np.exp(-lt * 3.2) * np.minimum(1, lt / 0.004) * amp).astype(np.float32)

def arps():
    out = np.zeros((2, N), np.float32)
    step = BEAT / 2; k = 0; t = 2.0
    while t < TOTAL - 2:
        a = arp_amt[int(t * SR)]
        if a > 0.02:
            notes = CHORDS[chord_at(t)]
            pat = [3, 4, 5, 4, 2, 4, 5, 3]
            m = notes[pat[k % 8] % len(notes)] + 12
            if t > e(8) - 0.5 and t < e(9):
                m += 12 if k % 4 == 1 else 0               # Saturn: brighter, higher
            if (k % 8 in (1, 5)) and a < 0.5:               # sparse when quieter
                t += step; k += 1; continue
            b = bell(midi(m), 1.8, 0.05 * a * (0.8 + 0.4 * rng.random()))
            i = int(t * SR); j = min(N, i + len(b))
            pan = 0.5 + 0.35 * math.sin(k * 0.7)
            out[0, i:j] += b[:j - i] * (1 - pan); out[1, i:j] += b[:j - i] * pan
        t += step; k += 1
    return out

def pulses():
    out = np.zeros(N, np.float32); t = 0.0; k = 0
    n = int(0.6 * SR); lt = np.arange(n) / SR
    f = 46 + 30 * np.exp(-lt * 30)
    kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-lt * 7) * np.minimum(1, lt / 0.003)
    while t < TOTAL - 1:
        a = pulse_amt[int(t * SR)]
        if a > 0.02 and k % 2 == 0:
            i = int(t * SR); j = min(N, i + n)
            out[i:j] += (kick[:j - i] * 0.22 * a * (1.0 if k % 4 == 0 else 0.6)).astype(np.float32)
        t += BEAT; k += 1
    return np.stack([out, out])

def strings():
    out = np.zeros((2, N), np.float32)
    seglen = 2 * BAR
    for k in range(int(TOTAL / seglen) + 1):
        t0 = k * seglen; name = chord_at(t0 + 0.01)
        i0 = int(t0 * SR); i1 = min(N, i0 + int((seglen + 1.2) * SR)); n = i1 - i0
        if n <= 0: break
        lt = np.arange(n) / SR
        env = np.clip(lt / 2.0, 0, 1) * np.clip((seglen + 1.2 - lt) / 1.5, 0, 1)
        for ch in range(2):
            sig = np.zeros(n)
            for m in CHORDS[name][2:5]:
                f = midi(m + 12) * (1 + 0.003 * np.sin(2 * np.pi * 5.2 * lt + ch))
                ph = 2 * np.pi * np.cumsum(f) / SR
                sig += sum(np.sin(h * ph) / h for h in range(1, 7))   # band-limited saw
            out[ch, i0:i1] += (sig * env * 0.016).astype(np.float32)
    return out

def air():
    n = rng.standard_normal((2, N)).astype(np.float32)
    n = np.stack([bp(n[0], 3000, 9000), bp(n[1], 3000, 9000)])
    wob = 0.6 + 0.4 * np.sin(2 * np.pi * tt / 7.3)
    return n * 0.012 * air_amt * wob

def reverb(x, secs=3.2, wet=0.35):
    n = int(secs * SR); lt = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-lt * 6.9 / secs)
        ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
        out.append(x[ch] * (1 - wet) + fftconvolve(x[ch], ir)[:N] * wet * 1.2)
    return np.stack(out).astype(np.float32)

# ------------------------------------------------------------ SFX (editorial accents)
def place(buf, sig, t, gain=1.0, pan=0.5):
    i = int(t * SR); j = min(N, i + sig.shape[-1])
    if i >= N or j <= i: return
    s = sig[..., :j - i] * gain
    if s.ndim == 1:
        buf[0, i:j] += s * (1 - pan) * 1.4; buf[1, i:j] += s * pan * 1.4
    else:
        buf[:, i:j] += s

def noise(d): return rng.standard_normal(int(d * SR)).astype(np.float32)

def whoosh(d=1.1, lo=300, hi=3500):
    x = noise(d); n = len(x); lt = np.arange(n) / n
    out = np.zeros(n, np.float32); blk = 512
    for i in range(0, n, blk):   # swept band-pass
        c = lo * (hi / lo) ** lt[i]
        out[i:i + blk] = bp(x[max(0, i - 2048):i + blk], c * 0.7, min(c * 1.4, 20000))[-len(x[i:i + blk]):]
    env = np.sin(np.pi * lt) ** 2
    return out * env * 0.5

def rise(d=2.0):
    x = lp(noise(d), 1800); n = len(x); lt = np.arange(n) / n
    tone = np.sin(2 * np.pi * np.cumsum(110 + 110 * lt) / SR) * 0.4
    return ((x * 0.4 + tone) * lt ** 2 * (1 - np.clip((lt - 0.92) / 0.08, 0, 1))).astype(np.float32)

def impact(f0=55, d=1.6):
    n = int(d * SR); lt = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(f0 + 40 * np.exp(-lt * 18)) / SR) * np.exp(-lt * 3.0)
    s += lp(noise(d), 500) * np.exp(-lt * 9) * 0.5
    return (s * np.minimum(1, lt / 0.004)).astype(np.float32)

def chime(f=1318.5, d=2.5):
    return bell(f, d, 1.0) + bell(f * 1.5, d, 0.5)

def click():
    n = int(0.05 * SR); lt = np.arange(n) / SR
    return (hp(noise(0.05), 2000) * np.exp(-lt * 160) + np.sin(2 * np.pi * 2400 * lt) * np.exp(-lt * 90) * 0.6).astype(np.float32)

def low_tone(d=3.0, f=73.4):
    n = int(d * SR); lt = np.arange(n) / SR
    e_ = np.minimum(1, lt / 0.8) * np.clip((d - lt) / 1.2, 0, 1)
    return ((np.sin(2 * np.pi * f * lt) + 0.4 * np.sin(2 * np.pi * f * 1.5 * lt)) * e_).astype(np.float32)

def shimmer(d=3.0):
    out = np.zeros(int(d * SR), np.float32)
    for k, m in enumerate([86, 90, 93, 97, 98, 102]):
        b = bell(midi(m), d - k * 0.12, 0.35)
        i = int(k * 0.09 * SR); out[i:i + len(b)] += b[:len(out) - i]
    return out

def sfx():
    b = np.zeros((2, N), np.float32)
    place(b, rise(1.7), 0.0, 0.22)
    place(b, impact(), S.kw(1, "आठ"), 0.26)
    for s in TL["scenes"][1:]:
        place(b, whoosh(1.0), s["start"] - 0.55, 0.16, pan=0.35 + 0.3 * (s["id"] % 2))
    place(b, low_tone(4.0, 73.4), G(2, 0.0), 0.10)
    place(b, chime(1318.5), G(2, S.kw(2, "हाइड्रोजन")), 0.07)
    t88 = S.kw(3, "अठासी") - 0.3
    place(b, click(), G(3, t88 + 3.4), 0.30)
    place(b, low_tone(2.5, 55), G(4, S.kw(4, "चार") - 0.2), 0.14)
    place(b, chime(1174.7), G(5, S.kw(5, "इकहत्तर")), 0.06)
    place(b, whoosh(1.8, 200, 1500), G(6, S.kw(6, "ज्वालामुखी") - 0.9), 0.14)
    place(b, impact(41, 2.2), G(7, 0.25), 0.24)
    place(b, shimmer(3.2), G(8, 0.6), 0.10)
    place(b, chime(1760), G(9, S.kw(9, "अट्ठानवे") + 1.0), 0.06)
    place(b, chime(1567.98), G(10, S.kw(10, "हज़ार") - 0.4), 0.06)
    place(b, shimmer(2.5), G(10, S.kw(10, "साल") - 1.2), 0.06)
    return b

# ------------------------------------------------------------ mix
def main():
    bd = os.path.join(ROOT, "build")
    sr, vo = wavfile.read(os.path.join(bd, "vo_full.wav")); vo = vo.astype(np.float32) / 32768
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    print("synth music...")
    pads = pad() * pad_amt
    # moving low-pass for brightness automation (block-wise)
    blk = SR // 10
    for ch in range(2):
        for i in range(0, N, blk):
            fc = float(bright[i]); seg_ = pads[ch, max(0, i - 4096):i + blk]
            pads[ch, i:i + blk] = lp(seg_, fc)[-len(pads[ch, i:i + blk]):]
    music = pads + arps() + strings() * str_amt + air()
    music = reverb(music, 3.4, 0.4) + pulses()
    music = np.stack([hp(music[0], 35), hp(music[1], 35)])
    music /= np.abs(music).max() + 1e-9
    # duck music under speech (≈ -16 dB below VO at rest, extra -6 dB while talking)
    env = np.abs(vo); k = int(0.03 * SR)
    env = np.convolve(env, np.ones(k) / k, "same")
    act = np.clip(env / 0.02, 0, 1)
    sm = np.zeros_like(act); a_up, a_dn = 1 - math.exp(-1 / (0.05 * SR)), 1 - math.exp(-1 / (0.5 * SR)); y = 0.0
    for i in range(0, N, 64):           # attack/release follower (decimated)
        x = act[i]; y += ((a_up if x > y else a_dn) * 64) * (x - y); sm[i:i + 64] = y
    duck = 10 ** (-(6 * np.clip(sm, 0, 1)) / 20)
    music_lvl = 10 ** (-14 / 20)
    music = music * duck * music_lvl
    fx = sfx() * 1.0
    vo_st = np.stack([vo, vo])
    mix = vo_st * 0.9 + music + fx
    for name, x in (("stem_narration.wav", vo_st * 0.9), ("stem_music.wav", music), ("stem_sfx.wav", fx), ("mix_raw.wav", mix)):
        wavfile.write(os.path.join(bd, name), SR, (np.clip(x.T, -1, 1) * 32767).astype(np.int16))
    # two-pass EBU R128 loudness normalisation
    raw = os.path.join(bd, "mix_raw.wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af, "-ar", "48000", os.path.join(bd, "mix_final.wav")], check=True)
    print("measured input", js["input_i"], "LUFS")

if __name__ == "__main__":
    main()

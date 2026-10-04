"""Step 2: build the edit timeline from the *measured* narration, then write
the full-length voiceover WAV and the Hindi SRT. Scene lengths follow audio."""
import json, os, re, subprocess, sys
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCENES, display_text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VO = os.path.join(ROOT, "build", "vo")
SR = 48000
# lead-in before narration and hold after it, per scene (seconds)
PRE = {1: 1.6, 2: 0.6, 3: 0.7, 4: 0.6, 5: 0.6, 6: 0.6, 7: 0.9, 8: 0.7, 9: 0.6, 10: 0.6, 11: 0.6, 12: 0.5}
POST = {1: 0.9, 2: 0.6, 3: 0.6, 4: 0.6, 5: 0.6, 6: 2.6, 7: 0.6, 8: 0.6, 9: 0.6, 10: 1.6, 11: 1.4, 12: 3.4}
TRIM_HEAD = 0.08   # TTS adds ~0.1 s silence at the head

# never break a cue/line right after these words (keeps numbers & names whole)
NOBREAK = {"सौ", "एक", "दो", "चार", "दस", "लगभग", "कार्बन", "ग्रेट", "रेड", "हज़ार", "आइस", "प्रति", "करीब", "तीस", "अपनी", "बहुत", "कौन", "सबसे", "द", "क्लाउड", "माइंड", "ए", "रोचक"}

def split_cues(text, words, maxlen=56):
    """Sentence-first cue split; long sentences are divided at the most
    balanced point, preferring commas, so no cue ends on an orphan word."""
    toks = text.split()
    assert len(toks) == len(words), (len(toks), len(words), text)
    L = lambda ix: len(" ".join(toks[j] for j in ix))
    def rec(ix):
        if L(ix) <= maxlen or len(ix) < 4:
            return [ix]
        best = None
        for k in range(2, len(ix) - 1):
            a, b = ix[:k], ix[k:]
            score = max(L(a), L(b)) - (14 if toks[a[-1]].endswith(",") else 0) + (40 if toks[a[-1]] in NOBREAK else 0)
            if best is None or score < best[0]:
                best = (score, a, b)
        return rec(best[1]) + rec(best[2])
    sents, cur = [], []
    for i, tok in enumerate(toks):
        cur.append(i)
        if re.search(r"[।!?]$", tok):
            sents.append(cur); cur = []
    if cur: sents.append(cur)
    out = []
    for sx in sents:
        out += rec(sx)
    return [(" ".join(toks[j] for j in c), c[0], c[-1]) for c in out]

def wrap2(s, maxc=28):
    """Balance a cue into at most two lines."""
    if len(s) <= maxc:
        return [s]
    w = s.split(); best = None
    for k in range(1, len(w)):
        a, b = " ".join(w[:k]), " ".join(w[k:])
        sc = max(len(a), len(b)) + (40 if w[k - 1] in NOBREAK else 0) - (6 if w[k - 1].endswith(",") else 0)
        if best is None or sc < best[0]:
            best = (sc, [a, b])
    return best[1]

def fmt(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    t, scenes, cues, chunks = 0.0, [], [], []
    for s in SCENES:
        d = json.load(open(os.path.join(VO, f"scene{s['id']:02d}.json")))
        sr, a = wavfile.read(os.path.join(VO, f"scene{s['id']:02d}.wav"))
        a = a.astype(np.float32) / 32768.0
        speech_end = d["words"][-1]["t1"] + 0.12
        a = a[int(TRIM_HEAD * SR):int(speech_end * SR)]
        vo_start = t + PRE[s["id"]]
        dur = PRE[s["id"]] + len(a) / SR + POST[s["id"]]
        words = [dict(w=w["w"], t0=round(vo_start + w["t0"] - TRIM_HEAD, 3), t1=round(vo_start + w["t1"] - TRIM_HEAD, 3)) for w in d["words"]]
        chunks.append((vo_start, a))
        for txt, i0, i1 in split_cues(s["vo"], words):
            txt = display_text(txt)
            cues.append(dict(scene=s["id"], text=txt, lines=wrap2(txt), t0=words[i0]["t0"] - 0.05, t1=words[i1]["t1"] + 0.25))
        scenes.append(dict(id=s["id"], key=s["key"], start=round(t, 3), dur=round(dur, 3), vo_start=round(vo_start, 3), words=words))
        t += dur
    total = t
    # keep cues from overlapping and give each a readable minimum duration
    for a_, b_ in zip(cues, cues[1:]):
        a_["t1"] = min(max(a_["t1"], a_["t0"] + 1.0), b_["t0"] - 0.04)
    json.dump(dict(total=round(total, 3), fps=30, scenes=scenes, cues=cues),
              open(os.path.join(ROOT, "build", "timeline.json"), "w"), ensure_ascii=False, indent=1)
    # full-length narration track
    out = np.zeros(int(np.ceil(total * SR)) + SR, np.float32)
    for st, a in chunks:
        i = int(round(st * SR)); out[i:i + len(a)] += a
    out = out[:int(round(total * SR))]
    wavfile.write(os.path.join(ROOT, "build", "vo_full.wav"), SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
    with open(os.path.join(ROOT, "build", "Hindi_Subtitles.srt"), "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{fmt(c['t0'])} --> {fmt(c['t1'])}\n" + "\n".join(c["lines"]) + "\n\n")
    print("total", round(total, 2), "s;", len(cues), "cues")
    for s in scenes: print(s["id"], s["key"], s["start"], s["dur"])

if __name__ == "__main__":
    main()

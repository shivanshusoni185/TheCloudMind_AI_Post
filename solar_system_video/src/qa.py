"""Step 6: automated review of the exported video: specs, frame count, black /
frozen frames, A/V duration sync, subtitle timing vs narration, planet order
and on-screen copy vs the brief."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT
from script_data import SCENES, display_text

OUT = os.path.join(ROOT, "output")
TL = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
ok = True
def check(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg); ok &= bool(cond)

def probe(path):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-count_frames", "-of", "json", path]))

for name in ("Solar_System_Final.mp4", "Solar_System_Clean_Master_NoSubtitles.mp4"):
    p = os.path.join(OUT, name)
    j = probe(p); v = [s for s in j["streams"] if s["codec_type"] == "video"][0]; a = [s for s in j["streams"] if s["codec_type"] == "audio"][0]
    print(f"--- {name}")
    check(v["codec_name"] == "h264" and v["width"] == 1080 and v["height"] == 1920, f"H.264 1080x1920 ({v['codec_name']} {v['width']}x{v['height']})")
    check(v["r_frame_rate"] == "30/1", f"30 fps ({v['r_frame_rate']})")
    nf = int(v["nb_read_frames"]); exp = int(round(TL["total"] * 30))
    check(nf == exp, f"frame count {nf} == expected {exp} (no missing frames)")
    check(a["codec_name"] == "aac" and a["sample_rate"] == "48000", f"AAC 48 kHz ({a['codec_name']} {a['sample_rate']})")
    vd, ad = float(v["duration"]), float(a["duration"])
    check(abs(vd - ad) < 0.1, f"audio/video durations match ({vd:.2f}s vs {ad:.2f}s)")
    br = int(j["format"]["bit_rate"]) / 1e6
    print(f"     bitrate {br:.1f} Mb/s, duration {float(j['format']['duration']):.2f}s")

p = os.path.join(OUT, "Solar_System_Final.mp4")
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vf", "blackdetect=d=0.2:pix_th=0.04", "-an", "-f", "null", "-"], capture_output=True, text=True)
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)
bad = [b for b in blacks if float(b[0]) < TL["total"] - 1.5]
check(not bad, f"no black gaps inside the film (found {blacks})")
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vf", "freezedetect=n=0.0005:d=1.5", "-an", "-f", "null", "-"], capture_output=True, text=True)
fr = re.findall(r"freeze_start: ([\d.]+)", r.stderr)
check(not fr, f"no frozen stretches > 1.5 s (found {fr})")
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"], capture_output=True, text=True)
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)[-1])
check(abs(I + 14) < 1.0 and pk <= -1.0, f"loudness {I} LUFS (target -14), true peak {pk} dBFS (<= -1)")

# subtitles: every cue lies on narration words, in order, no overlaps, readable length
srt = open(os.path.join(OUT, "Hindi_Subtitles.srt"), encoding="utf-8").read()
cues = TL["cues"]
check(all(c["t1"] > c["t0"] + 0.6 for c in cues), "every subtitle cue >= 0.6 s")
check(all(a["t1"] <= b["t0"] for a, b in zip(cues, cues[1:])), "subtitle cues do not overlap")
check(all(len(c["lines"]) <= 2 for c in cues), "max two subtitle lines")
joined = {s["id"]: " ".join(c["text"] for c in cues if c["scene"] == s["id"]) for s in SCENES}
check(all(joined[s["id"]] == display_text(s["vo"]) for s in SCENES), "subtitle text == exact Hindi narration from the brief")
check(srt.count(" --> ") == len(cues), f"SRT has {len(cues)} cues")

# planet order and on-screen copy
src = open(os.path.join(ROOT, "src", "scenes.py"), encoding="utf-8").read()
order = re.findall(r'header\(cv, t, "(\d\d)", "([A-Z]+)", "([^"]+)"', src)
exp = [("01", "MERCURY", "बुध"), ("02", "VENUS", "शुक्र"), ("03", "EARTH", "पृथ्वी"), ("04", "MARS", "मंगल"),
       ("05", "JUPITER", "बृहस्पति"), ("06", "SATURN", "शनि"), ("07", "URANUS", "यूरेनस"), ("08", "NEPTUNE", "नेपच्यून")]
check(order == exp, f"planet order and names: {[o[1] for o in order]}")
copy = ["SOLAR SYSTEM", "आठ ग्रह, आठ अनोखी दुनिया", "Illustrative scale", "Our star", "Core: ≈{} million °C", "Smallest planet",
        "1 year ≈{} Earth days", "Hottest planet", "Surface ≈{} °C", "Only known planet with life", "The Red Planet",
        "Evidence of ancient liquid water", "Largest planet", "Rotation ≈{} hours", "Great Red Spot = giant storm",
        "Ice + rock rings", "1 year ≈{} Earth years", "Ice giant", "Axial tilt ≈{}°", "Winds can exceed {} km/h",
        "PLUTO = DWARF PLANET", "बौना ग्रह", "आपका पसंदीदा ग्रह", "कौन सा है?", "Water ≈", "Land ≈29%"]
missing = [c for c in copy if c not in src]
check(not missing, f"all brief on-screen text present (missing: {missing})")
print("\nOVERALL:", "PASS" if ok else "FAIL")

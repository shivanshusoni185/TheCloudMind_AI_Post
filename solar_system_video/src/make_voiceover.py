"""Step 1: synthesize the Hindi narration per scene (Microsoft Edge neural TTS,
voice hi-IN-MadhurNeural) and save word-boundary timings for subtitle sync."""
import asyncio, json, ssl, subprocess, sys, os
import edge_tts, edge_tts.communicate as comm_mod
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCENES

CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):  # sandbox TLS proxy
    comm_mod._SSL_CTX = ssl.create_default_context(cafile=CA)

VOICE, RATE, PITCH = "hi-IN-MadhurNeural", "+12%", "+0Hz"
OUT = os.path.join(os.path.dirname(__file__), "..", "build", "vo")
os.makedirs(OUT, exist_ok=True)

async def one(s):
    c = edge_tts.Communicate(s["vo"], VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    words, mp3 = [], os.path.join(OUT, f"scene{s['id']:02d}.mp3")
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append(dict(t0=ch["offset"] / 1e7, t1=(ch["offset"] + ch["duration"]) / 1e7, w=ch["text"]))
    wav = mp3.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", "48000", "-ac", "1", wav], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]))
    json.dump(dict(words=words, duration=dur), open(wav.replace(".wav", ".json"), "w"), ensure_ascii=False, indent=1)
    print(s["id"], round(dur, 2), len(words), "words")

async def main():
    for s in SCENES:
        await one(s)
asyncio.run(main())

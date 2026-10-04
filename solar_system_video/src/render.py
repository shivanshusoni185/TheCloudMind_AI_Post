"""Step 3: render frames. Usage:
  python render.py stills 1.0 5.2 ...      -> build/stills/*.png + contact sheet
  python render.py full [workers]          -> build/seg_*.mp4 (captioned + clean)
"""
import math, os, subprocess, sys, time
import numpy as np
from multiprocessing import Process
from PIL import Image
from common import ROOT, W, H, FPS, Canvas, BG_RGB, ease, seg
import scenes as S

TOTAL = S.TL["total"]
NFRAMES = int(round(TOTAL * FPS))
XF = 0.25   # half-length of scene crossfades (s)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.32 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2, 0, 1) ** 1.3)[..., None]
del yy, xx

def scene_at(g):
    sc = S.TL["scenes"]
    for i, s in enumerate(sc):
        if g < s["start"] + s["dur"] or i == len(sc) - 1:
            return i
    return len(sc) - 1

def draw_scene(i, g):
    s = S.TL["scenes"][i]
    cv = Canvas(); cv.fill(BG_RGB)
    S.SCENE_FUNCS[s["id"]](cv, g - s["start"])
    return cv.a

def frame(g):
    """Returns (clean, captioned) uint8 frames for global time g."""
    sc = S.TL["scenes"]
    i = scene_at(g)
    a = draw_scene(i, g)
    s = sc[i]
    # crossfade around each cut: [start - XF, start + XF]
    if i > 0 and g < s["start"] + XF:
        w = ease(seg(g, s["start"] - XF, s["start"] + XF))
        a = a * w + draw_scene(i - 1, g) * (1 - w)
    elif i < len(sc) - 1 and g > s["start"] + s["dur"] - XF:
        w = ease(seg(g, s["start"] + s["dur"] - XF, s["start"] + s["dur"] + XF))
        a = a * (1 - w) + draw_scene(i + 1, g) * w
    a = a * VIGNETTE
    clean = np.clip(a, 0, 1)
    cv = Canvas(clean.copy())
    S.captions(cv, g)
    to8 = lambda x: (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)
    return to8(clean), to8(cv.a)

def ff(path):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "14", "-pix_fmt", "yuv420p", "-g", "60", path], stdin=subprocess.PIPE)

def worker(k, f0, f1):
    out = os.path.join(ROOT, "build", "segs"); os.makedirs(out, exist_ok=True)
    pc, pk = ff(f"{out}/clean_{k:02d}.mp4"), ff(f"{out}/capt_{k:02d}.mp4")
    t0 = time.time()
    for f in range(f0, f1):
        c, cap = frame(f / FPS)
        pc.stdin.write(c.tobytes()); pk.stdin.write(cap.tobytes())
        if (f - f0) % 150 == 0:
            el = time.time() - t0
            print(f"[w{k}] {f - f0}/{f1 - f0} frames  {el:.0f}s", flush=True)
    for p in (pc, pk):
        p.stdin.close(); p.wait()
    print(f"[w{k}] done in {time.time() - t0:.0f}s", flush=True)

def full(nw):
    # interleaved chunks balance the uneven per-scene cost
    nchunk = nw * 4
    bounds = np.linspace(0, NFRAMES, nchunk + 1).astype(int)
    jobs = list(range(nchunk))
    def run(ids):
        for j in ids:
            worker(j, bounds[j], bounds[j + 1])
    ps = [Process(target=run, args=(jobs[w::nw],)) for w in range(nw)]
    [p.start() for p in ps]; [p.join() for p in ps]
    for kind in ("clean", "capt"):
        lst = os.path.join(ROOT, "build", "segs", f"{kind}.txt")
        with open(lst, "w") as f:
            for j in range(nchunk):
                f.write(f"file '{kind}_{j:02d}.mp4'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        os.path.join(ROOT, "build", f"video_{kind}.mp4")], check=True)
    print("frames", NFRAMES)

def stills(ts):
    out = os.path.join(ROOT, "build", "stills"); os.makedirs(out, exist_ok=True)
    ims = []
    for g in ts:
        t0 = time.time()
        _, cap = frame(g)
        im = Image.fromarray(cap); im.save(f"{out}/t{g:07.2f}.png"); ims.append(im)
        print(f"{g:.2f}s rendered in {time.time() - t0:.2f}s")
    n = len(ims); cols = min(n, 4); rows = math.ceil(n / cols)
    sheet = Image.new("RGB", (cols * 360, rows * 640))
    for j, im in enumerate(ims):
        sheet.paste(im.resize((360, 640), Image.LANCZOS), ((j % cols) * 360, (j // cols) * 640))
    sheet.save(f"{out}/sheet.jpg", quality=90)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills([float(x) for x in sys.argv[2:]])
    else:
        full(int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count())

"""The 11 scenes. Each scene function draws one frame at scene-local time t.
All titles, numbers, chips and labels are drawn here as overlays (edit freely);
reveal times are keyed to the measured narration words (see kw())."""
import json, math, os
import numpy as np
from common import *
from planet import (globe, ringed_globe, rings, saturn_ring, uranus_ring, sun, stars, sample, tex,
                    prominence_sprite, SUN_L, body_matrix, smoothstep)

TL = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
SC = {s["id"]: s for s in TL["scenes"]}
R2D = math.pi / 180

def kw(sid, token, n=0, end=False):
    """Scene-local time at which the n-th narration word containing token starts."""
    s = SC[sid]; hits = [w for w in s["words"] if token in w["w"]]
    if not hits:
        raise KeyError((sid, token))
    w = hits[min(n, len(hits) - 1)]
    return (w["t1"] if end else w["t0"]) - s["start"]

def vo_end(sid):
    s = SC[sid]; return s["words"][-1]["t1"] - s["start"]

def dur(sid):
    return SC[sid]["dur"]

# ------------------------------------------------------------ overlays
def header(cv, t, num, name, hindi, t_in=0.25, t_out=None, sid=None):
    t_out = t_out if t_out is not None else dur(sid) + 1
    a = window(t, t_in, t_out, 0.6, 0.4)
    if a <= 0: return
    dx = (1 - ease_out(seg(t, t_in, t_in + 0.8))) * -36
    y = MT + 6
    if num:
        cv.text(num, MX + dx, y, "latb", 34, CYAN, a, tracking=3)
        v = Vec(MX + 70, y + 10, 140, 20)
        v.line([(MX + 70, y + 22), (MX + 70 + 110 * ease_out(seg(t, t_in + 0.2, t_in + 1.0)), y + 22)], col(CYAN, 0.8), 2)
        v.composite(cv, a)
        y += 52
    cv.text(name, MX + dx * 1.3, y, "disp", 88, WHITE, a, tracking=4)
    cv.text(hindi, MX + dx * 1.6, y + 104, "devb", 58, GOLD, a * ease(seg(t, t_in + 0.25, t_in + 0.85)))

SLOT_Y = [1166, 1258]
def chip(cv, t, text, slot, t_in, t_out=None, accent=CYAN, sid=None, size=40, value=None):
    """Fact card. value=(final_number, fmt) animates a count-up that settles fast."""
    t_out = t_out if t_out is not None else dur(sid) + 1
    a = window(t, t_in, t_out, 0.45, 0.35)
    if a <= 0: return
    if value is not None:
        final, fmt_ = value
        p = ease_out(seg(t, t_in + 0.1, t_in + 0.9))
        text = text.format(fmt_(final * p))
    w = int(text_width(text, size)) + 64
    w = max(w, 200); h = 78
    y = SLOT_Y[slot] + (1 - ease_out(seg(t, t_in, t_in + 0.5))) * 22
    cv.blit(rrect_sprite(w, h, 16, fill=(8, 14, 34, 215), outline=col(accent, 0.55), ow=2, accent=col(accent), accent_w=9), MX, y, a)
    cv.text(text, MX + 34, y + h / 2 - 2, None, size, WHITE, a, anchor="lm", shadow=False)

def footnote(cv, text, x, y, a, anchor="lt", size=28, color=MUTED):
    cv.text(text, x, y, None, size, color, a, anchor=anchor)

def panel(cv, x0, y0, x1, y1, a, accent=CYAN, title=None):
    cv.blit(rrect_sprite(int(x1 - x0), int(y1 - y0), 22, fill=(6, 11, 28, 225), outline=col(accent, 0.45), ow=2), x0, y0, a)
    if title:
        cv.text(title, x0 + 22, y0 + 16, None, 26, MUTED, a)

def bg(cv, idx, t, bright=1.0):
    stars(cv, 40 + 30 * idx + 2.5 * t, 50 + 70 * idx + 1.2 * t, bright)

# ------------------------------------------------------------ solar-system map
PL = [  # name, hindi, texture, orbit radius (illustrative), marker size, start angle, kwargs
    ("MERCURY", "बुध", "2k_mercury.jpg", 70, 6, 35, {}),
    ("VENUS", "शुक्र", "2k_venus_atmosphere.jpg", 104, 9, 205, {}),
    ("EARTH", "पृथ्वी", "2k_earth_daymap.jpg", 142, 9.5, 118, dict(kind="earth", clouds="2k_earth_clouds.jpg")),
    ("MARS", "मंगल", "2k_mars.jpg", 180, 7.5, 300, {}),
    ("JUPITER", "बृहस्पति", "2k_jupiter.jpg", 282, 22, 62, dict(kind="gas")),
    ("SATURN", "शनि", "2k_saturn.jpg", 342, 18, 232, dict(kind="gas")),
    ("URANUS", "यूरेनस", "2k_uranus.jpg", 398, 13, 152, dict(kind="gas")),
    ("NEPTUNE", "नेपच्यून", "2k_neptune.jpg", 450, 13, 335, dict(kind="gas")),
]
_rng = np.random.default_rng(11)
BELT = np.stack([_rng.uniform(212, 252, 520), _rng.uniform(0, 2 * math.pi, 520), _rng.uniform(0.6, 1.6, 520)], 1)
KUIPER = np.stack([_rng.uniform(490, 1100, 1500) ** 1.0, _rng.uniform(0, 2 * math.pi, 1500), _rng.uniform(0.6, 1.5, 1500)], 1)

def planet_angle(i, t):
    r = PL[i][3]
    return PL[i][5] * R2D + 0.22 * (142 / r) ** 1.5 * t

def project(cam, r, th):
    x, y = r * math.cos(th + cam["phi"]), r * math.sin(th + cam["phi"])
    e = cam["e"]
    f = 1 + 0.10 * (y / 450) * math.cos(e)
    return cam["cx"] + cam["s"] * x * f, cam["cy"] + cam["s"] * y * math.sin(e) * f, f

def solar_map(cv, t, cam, orbit_prog=None, alpha=1.0, belt=0.0, kuiper=0.0, labels=0.0, hi=None,
              planet_alpha=None, sun_r=None, pluto=0.0, hide_planet=None):
    """Illustrative (not to scale) map. Returns screen positions of planets."""
    orbit_prog = orbit_prog if orbit_prog is not None else [1] * 8
    planet_alpha = planet_alpha if planet_alpha is not None else [1] * 8
    v = Vec()
    if kuiper > 0:
        for r, th, sz in KUIPER:
            x, y, f = project(cam, r, th + 0.004 * t)
            if -20 < x < W + 20 and -20 < y < H + 20:
                v.circle(x, y, sz * 0.9 * cam["s"] ** 0.5, fill=col("#AFC4D8", 0.6 * kuiper))
    if belt > 0:
        for r, th, sz in BELT:
            x, y, f = project(cam, r, th + 0.02 * t)
            v.circle(x, y, sz * cam["s"] ** 0.5, fill=col("#B9A58C", 0.55 * belt))
    for i, p in enumerate(PL):
        pr = orbit_prog[i]
        if pr <= 0: continue
        th0 = planet_angle(i, t)
        n = max(2, int(220 * pr))
        pts = [project(cam, p[3], th0 - 2 * math.pi * pr * k / (n - 1))[:2] for k in range(n)]
        hl = hi is not None and i == hi
        v.line(pts, col(CYAN if hl else "#7FB8D6", (0.9 if hl else 0.32) * alpha), 3.2 if hl else 1.8)
    if pluto > 0:  # eccentric, inclined dwarf-planet orbit (schematic)
        pts = []
        for k in range(181):
            E = 2 * math.pi * k / 180
            a_, e_ = 520, 0.25
            x_ = a_ * (math.cos(E) - e_); y_ = a_ * math.sqrt(1 - e_ ** 2) * math.sin(E)
            th = math.atan2(y_, x_) + 1.9; r = math.hypot(x_, y_)
            pts.append(project(cam, r, th)[:2])
        for k in range(0, 180, 4):
            v.line(pts[k:k + 3], col(GOLD, 0.55 * pluto), 1.6)
    v.composite(cv, alpha)
    # Sun
    sx, sy = cam["cx"], cam["cy"]
    sr = sun_r if sun_r is not None else 20 * cam["s"]
    sun(cv, sx, sy, sr, t, alpha=alpha, glow=0.9)
    pos = []
    order = sorted(range(8), key=lambda i: project(cam, PL[i][3], planet_angle(i, t))[1])
    for i in order:
        p = PL[i]
        x, y, f = project(cam, p[3], planet_angle(i, t))
        pos.append(None)
        R = p[4] * cam["s"] ** 0.75 * f
        L = np.array([sx - x, -(sy - y), max(30.0, 0.35 * math.hypot(sx - x, sy - y))])
        L = L / np.linalg.norm(L)
        pa = alpha * planet_alpha[i] * (0 if hide_planet == i else 1)
        if pa <= 0: continue
        if p[0] == "SATURN":
            ringed_globe(cv, x, y, R, p[2], saturn_ring(-0.1, 0.45), roll=-0.1, pitch=0.45, L=L, alpha=pa, kind="gas", ambient=0.05)
        else:
            globe(cv, x, y, R, p[2], spin=t * 0.3, L=L, alpha=pa, ambient=0.05, **p[6])
    out = [project(cam, p[3], planet_angle(i, t)) for i, p in enumerate(PL)]
    if labels > 0:
        for i, p in enumerate(PL):
            x, y, f = out[i]
            R = p[4] * cam["s"] ** 0.75 * f
            cv.text(p[1], x, y + R + 6, "dev", 26, WHITE, labels * alpha * planet_alpha[i], anchor="ct")
    return out

# ============================================================ SCENE 01 — hook
def s01(cv, t):
    sid = 1; D = dur(sid)
    bg(cv, 0, t)
    cam = dict(cx=540, cy=930, s=lerp(0.92, 1.0, ease(seg(t, 2, 9))), e=lerp(0.62, 0.86, ease_io(seg(t, 1.5, 10))),
               phi=-0.25 + 0.035 * t)
    # final push toward the Sun as the visual anchor
    push = ease_io(seg(t, D - 2.4, D + 0.3))
    cam["s"] *= lerp(1, 1.9, push)
    t_map = seg(t, 1.4, 4.0)
    prog = [ease_io(seg(t, 2.6 + 0.32 * i, 3.9 + 0.32 * i)) for i in range(8)]
    pa = [1.0] * 8; pa[2] = 0.0 if t_map < 1 else 1.0
    pos = solar_map(cv, t, cam, orbit_prog=prog, alpha=ease(seg(t, 1.6, 3.2)), planet_alpha=[ease(seg(t, 3.0 + 0.32 * i, 3.6 + 0.32 * i)) if i != 2 else (1.0 if t_map >= 1 else 0) for i in range(8)])
    # Earth limb pull-back into its orbit marker
    if t_map < 1:
        ex, ey, f = pos[2]
        Rm = PL[2][4] * cam["s"] ** 0.75 * f
        k = ease_io(t_map)
        R = math.exp(lerp(math.log(1500), math.log(Rm), k))
        cx = lerp(560, ex, k); cy = lerp(1920 + 1500 - 520, ey, k)
        L = SUN_L if k < 0.5 else np.array([cam["cx"] - ex, -(cam["cy"] - ey), 60.0]) / np.linalg.norm([cam["cx"] - ex, -(cam["cy"] - ey), 60.0])
        if 0.3 < k < 0.7:
            Lm = np.array([cam["cx"] - ex, -(cam["cy"] - ey), 60.0]); Lm /= np.linalg.norm(Lm)
            w = (k - 0.3) / 0.4; L = SUN_L * (1 - w) + Lm * w; L /= np.linalg.norm(L)
        globe(cv, cx, cy, R, "2k_earth_daymap.jpg", spin=1.35 - 0.02 * t, roll=-0.2, pitch=0.25, L=L,
              kind="earth", clouds="2k_earth_clouds.jpg", night="2k_earth_nightmap.jpg", atmo=(0.35, 0.6, 1.0), atmo_w=0.03)
    ta = kw(sid, "आठ")
    a = window(t, ta, D + 1, 0.8)
    yy = (1 - ease_out(seg(t, ta, ta + 1.0))) * 20
    cv.text("SOLAR SYSTEM", 540, 300 + yy, "disp", 104, WHITE, a, anchor="ct", tracking=8)
    cv.text("आठ ग्रह, आठ अनोखी दुनिया", 540, 438 + yy, "devb", 60, GOLD, a * ease(seg(t, ta + 0.5, ta + 1.3)), anchor="ct")
    footnote(cv, "Illustrative scale", 540, 1312, window(t, 3.4, D - 1.2), anchor="ct")

# ============================================================ SCENE 02 — Sun
def s02(cv, t):
    sid = 2; D = dur(sid)
    bg(cv, 1, t)
    tg = kw(sid, "गुरुत्वाकर्षण") - 0.4
    k = ease_io(seg(t, tg, tg + 2.6))
    R = lerp(lerp(600, 650, seg(t, 0, tg)), 120, k)
    cx = lerp(310, 540, k); cy = lerp(1300, 860, k)
    if k > 0:
        v = Vec()
        for i, r in enumerate([200, 250, 300, 350, 410, 460]):
            rr = r * ease_out(seg(t, tg + 0.8 + 0.12 * i, tg + 2.4 + 0.12 * i))
            if rr > R + 4:
                pts = [(cx + rr * math.cos(a_), cy + rr * 0.55 * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 200)]
                v.line(pts, col("#7FB8D6", 0.45), 1.8)
                th = 0.9 * i + t * 0.5 * (200 / r) ** 1.5
                v.circle(cx + rr * math.cos(th), cy + rr * 0.55 * math.sin(th), 6, fill=col(WHITE, 0.85))
        # inward gravity arrows
        ga = window(t, tg + 1.6, D + 1)
        for j in range(6):
            a_ = j * math.pi / 3 + 0.4
            p0 = (cx + 330 * math.cos(a_), cy + 330 * 0.55 * math.sin(a_)); p1 = (cx + 190 * math.cos(a_), cy + 190 * 0.55 * math.sin(a_))
            v.arrow(p0, p1, col(GOLD, 0.55 * ga), 2.2, 11)
        v.composite(cv, ease(seg(t, tg + 0.6, tg + 1.6)))
        footnote(cv, "Gravity keeps planets in orbit  ·  schematic", 540, 1112, window(t, tg + 2.0, D + 1), anchor="ct", size=27)
    sun(cv, cx, cy, R, t, glow=1.0)
    pa = (1 - k) * window(t, 0.3, D + 1, 1.5)
    if pa > 0:
        ps = prominence_sprite(int(R))
        ang = -0.62  # upper-right limb
        px, py = cx + R * 0.99 * math.cos(ang) , cy + R * 0.99 * math.sin(ang)
        rot = Image.fromarray((np.clip(ps, 0, 1) * 255).astype(np.uint8)).rotate(-math.degrees(ang) - 90 + 180 + 180, expand=True, resample=Image.BICUBIC)
        rs = np.asarray(rot, np.float32) / 255
        h, w = rs.shape[:2]
        cv.blit(np.concatenate([rs, np.zeros((h, w, 1), np.float32)], 2), px, py, pa * (0.85 + 0.15 * math.sin(t * 1.3)), anchor="cm", add=True)
    header(cv, t, None, "SUN", "सूर्य", sid=sid)
    chip(cv, t, "Our star", 0, kw(sid, "तारा") - 0.1, sid=sid, accent=GOLD)
    # core inset
    tc = kw(sid, "हाइड्रोजन") - 0.2
    ia = window(t, tc, tg + 0.4, 0.5, 0.5)
    if ia > 0:
        icx, icy, ir = 790, 640, 168
        panel(cv, icx - ir - 10, icy - ir - 10, icx + ir + 10, icy + ir + 50, ia, GOLD)
        v = Vec(icx - ir, icy - ir, 2 * ir, 2 * ir)
        v.circle(icx, icy, ir - 18, fill=col("#FF8A2A", 0.22), outline=col(GOLD, 0.7), width=2)
        v.circle(icx, icy, ir - 70, fill=col("#FFD27A", 0.25))
        lt = (t - tc) % 2.4
        mk = ease_io(seg(lt, 0.2, 1.1))
        for sgn in (-1, 1):
            hx = icx + sgn * lerp(80, 14, mk); hy = icy + sgn * lerp(-30, 0, mk)
            if lt < 1.15:
                v.circle(hx, hy, 15, fill=col(CYAN))
        if lt >= 1.1:
            fl = 1 - seg(lt, 1.1, 1.6)
            v.circle(icx, icy, 22 + 30 * (1 - fl), outline=col("#FFF3C4", fl), width=4)
            v.circle(icx, icy, 22, fill=col(GOLD))
            for j in range(8):
                a_ = j * math.pi / 4 + 0.2
                r0, r1 = 34 + 50 * seg(lt, 1.15, 2.0), 54 + 70 * seg(lt, 1.15, 2.0)
                v.line([(icx + r0 * math.cos(a_), icy + r0 * math.sin(a_)), (icx + r1 * math.cos(a_), icy + r1 * math.sin(a_))], col("#FFF3C4", 0.8 * (1 - seg(lt, 1.8, 2.3))), 3)
        v.composite(cv, ia)
        if lt < 1.15:
            for sgn in (-1, 1):
                hx = icx + sgn * lerp(80, 14, mk); hy = icy + sgn * lerp(-30, 0, mk)
                cv.text("H", hx, hy - 1, "latb", 22, "#06202A", ia, anchor="cm", shadow=False)
        else:
            cv.text("He", icx, icy - 1, "latb", 22, "#3A1C00", ia, anchor="cm", shadow=False)
        cv.text("H → He  +  energy", icx, icy + ir - 8, "lat", 28, WHITE, ia, anchor="ct")
        cv.text("Core (schematic)", icx, icy - ir + 4, "lat", 24, MUTED, ia, anchor="ct")
    chip(cv, t, "Core: ≈{} million °C", 1, tc + 0.3, sid=sid, accent=GOLD, value=(15, lambda x: f"{int(round(x))}"))

# ------------------------------------------------------------ helpers for globe scenes
def spin_fn(lon0_deg, rate, t):
    """Center longitude drifts east->: features move left to right (prograde)."""
    return lon0_deg * R2D - rate * t

# ============================================================ SCENE 03 — Mercury
def s03(cv, t):
    sid = 3; D = dur(sid)
    bg(cv, 2, t)
    t88 = kw(sid, "अठासी") - 0.3; tcr = kw(sid, "गड्ढे") - 1.4
    k = ease_io(seg(t, t88, t88 + 1.2)) * (1 - ease_io(seg(t, tcr, tcr + 1.4)))
    kc = ease_io(seg(t, tcr, tcr + 1.6))
    R = lerp(lerp(270, 300, seg(t, 0, t88)), 210, k) * lerp(1, 1.45, kc)
    cx = lerp(540, 300, k); cy = lerp(800, 790, k) + 120 * kc
    a0 = ease(seg(t, 0.0, 1.0))
    globe(cv, cx, cy, R * lerp(0.9, 1, a0), "2k_mercury.jpg", spin=spin_fn(40, 0.05, t), roll=0.03 * math.sin(t * 0.3),
          pitch=0.08, alpha=a0, ambient=0.012)
    ia = k
    if ia > 0.01:
        ocx, ocy, orr = 790, 800, 150
        v = Vec(ocx - 200, ocy - 200, 400, 400)
        v.circle(ocx, ocy, orr, outline=col("#7FB8D6", 0.35), width=2)
        p = ease_io(seg(t, t88 + 0.6, t88 + 3.4))
        n = max(2, int(200 * p))
        pts = [(ocx + orr * math.cos(-math.pi / 2 + 2 * math.pi * p * j / (n - 1)), ocy + orr * math.sin(-math.pi / 2 + 2 * math.pi * p * j / (n - 1))) for j in range(n)]
        v.line(pts, col(CYAN, 0.95), 3.5)
        v.composite(cv, ia)
        sun(cv, ocx, ocy, 26, t, alpha=ia, glow=0.6)
        th = -math.pi / 2 + 2 * math.pi * p
        globe(cv, ocx + orr * math.cos(th), ocy + orr * math.sin(th), 12, "2k_mercury.jpg",
              L=np.array([-math.cos(th), math.sin(th), 0.3]) / np.linalg.norm([-math.cos(th), math.sin(th), 0.3]), alpha=ia, ambient=0.08)
        days = int(round(88 * p))
        cv.text(f"{days}", ocx, ocy + orr + 26, "disp", 64, WHITE, ia, anchor="ct")
        cv.text("Earth days = 1 Mercury year", ocx, ocy + orr + 104, "lat", 24, MUTED, ia, anchor="ct")
        cv.text("Orbit schematic", ocx, ocy - orr - 50, "lat", 24, MUTED, ia, anchor="ct")
    header(cv, t, "01", "MERCURY", "बुध", sid=sid)
    chip(cv, t, "Smallest planet", 0, kw(sid, "छोटा") - 0.3, sid=sid)
    chip(cv, t, "1 year ≈{} Earth days", 1, t88 + 0.4, sid=sid, value=(88, lambda x: f"{int(round(x))}"))

# ============================================================ SCENE 04 — Venus
def s04(cv, t):
    sid = 4; D = dur(sid)
    bg(cv, 3, t)
    tg = kw(sid, "कार्बन") - 0.5
    k = ease_io(seg(t, tg, tg + 1.2))
    R = lerp(lerp(285, 315, seg(t, 0, tg)), 200, k)
    cx, cy = lerp(540, 290, k), lerp(800, 760, k)
    a0 = ease(seg(t, 0, 1))
    globe(cv, cx, cy, R * lerp(0.92, 1, a0), "2k_venus_atmosphere.jpg", spin=1.0 + 0.012 * t, alpha=a0,
          atmo=(0.95, 0.85, 0.6), atmo_w=0.05, ambient=0.01)
    if k > 0.01:
        x0, y0, x1, y1 = 520, 540, 975, 1140
        panel(cv, x0, y0, x1, y1, k, AMBER, "Greenhouse effect (schematic)")
        v = Vec(x0, y0, x1 - x0, y1 - y0)
        gy = 1040; cy0, cy1 = 690, 760
        v.rect(x0 + 20, gy, x1 - 20, gy + 40, fill=col("#7A4A2A", 0.9))
        v.rect(x0 + 20, cy0, x1 - 20, cy1, fill=col("#E8D3A2", 0.55))
        p = seg(t, tg + 0.6, tg + 2.0)
        for j in range(3):  # incoming sunlight
            xx = x0 + 70 + 60 * j
            v.arrow((xx, y0 + 70), (xx + 40, y0 + 70 + (gy - y0 - 80) * ease_out(p)), col(GOLD, 0.95), 3, 13)
        for j in range(3):  # outgoing infrared, absorbed and re-emitted
            q = seg(t, tg + 1.8 + 0.25 * j, tg + 3.0 + 0.25 * j)
            xx = x0 + 300 + 50 * j
            v.wave_arrow((xx, gy - 6), (xx, cy1 + 8), col(RED, 0.95), 3, 7, 4, 13, prog=q)
            q2 = seg(t, tg + 3.1 + 0.25 * j, tg + 4.2 + 0.25 * j)
            if q2 > 0:
                v.wave_arrow((xx + 22, cy1 + 4), (xx + 22, gy - 10), col(RED, 0.7), 3, 7, 4, 13, prog=q2)
        v.composite(cv, k)
        cv.text("CO₂-rich atmosphere", x1 - 30, cy0 - 40, "lat", 26, WHITE, k, anchor="rt")
        cv.text("Sunlight", x0 + 30, y0 + 46, "lat", 24, GOLD, k * seg(t, tg + 0.6, tg + 1.2))
        cv.text("Infrared trapped", x1 - 30, 1092, "lat", 24, RED, k * seg(t, tg + 2.0, tg + 2.6), anchor="rt")
        cv.text("Surface", x0 + 30, 1094, "lat", 22, MUTED, k)
    header(cv, t, "02", "VENUS", "शुक्र", sid=sid)
    chip(cv, t, "Hottest planet", 0, kw(sid, "गर्म") - 0.3, sid=sid, accent=AMBER)
    chip(cv, t, "Surface ≈{} °C", 1, kw(sid, "चार") - 0.2, sid=sid, accent=AMBER, value=(465, lambda x: f"{int(round(x))}"))

# ============================================================ SCENE 05 — Earth
def s05(cv, t):
    sid = 5; D = dur(sid)
    bg(cv, 4, t)
    a0 = ease(seg(t, 0, 1.0))
    R = lerp(300, 345, ease_io(seg(t, 0, D)))
    globe(cv, 540, 790 + 10 * math.sin(t * 0.2), R * lerp(0.92, 1, a0), "2k_earth_daymap.jpg", spin=spin_fn(95, 0.045, t),
          roll=-23.4 * R2D * 0.6, pitch=0.22, alpha=a0, kind="earth", clouds="2k_earth_clouds.jpg",
          cloud_spin=spin_fn(95, 0.05, t), night="2k_earth_nightmap.jpg", atmo=(0.35, 0.6, 1.0), atmo_w=0.045)
    t71 = kw(sid, "इकहत्तर") - 0.3
    ba = window(t, t71, D + 1, 0.5)
    if ba > 0:
        x0, x1, y0 = MX, W - MX, 1150
        p = ease_io(seg(t, t71 + 0.2, t71 + 1.4))
        panel(cv, x0, y0 - 8, x1, y0 + 104, ba, CYAN)
        v = Vec(x0, y0, x1 - x0, 110)
        bw = x1 - x0 - 40; bx = x0 + 20; by = y0 + 50
        v.rect(bx, by, bx + bw, by + 30, fill=col("#2A3346"), r=8)
        v.rect(bx, by, bx + bw * 0.71 * p, by + 30, fill=col("#2F86E0"), r=8)
        if p > 0.99:
            v.rect(bx + bw * 0.71, by, bx + bw, by + 30, fill=col("#B79A63"), r=8)
            v.rect(bx + bw * 0.71 - 8, by, bx + bw * 0.71 + 2, by + 30, fill=col("#2F86E0"))
        v.composite(cv, ba)
        cv.text(f"Water ≈{int(round(71 * p))}%", bx, y0 + 8, "latb", 30, "#8CC4FF", ba)
        cv.text("Land ≈29%", bx + bw, y0 + 8, "latb", 30, "#E3C88E", ba * seg(t, t71 + 1.3, t71 + 1.7), anchor="rt")
        cv.text("Surface coverage", 540, y0 + 12, "lat", 24, MUTED, ba, anchor="ct")
    header(cv, t, "03", "EARTH", "पृथ्वी", sid=sid)
    chip(cv, t, "Only known planet with life", 1, kw(sid, "पुष्टि") - 0.4, sid=sid)

# ============================================================ SCENE 06 — Mars
_MT = None
def mars_terrain_maps():
    global _MT
    if _MT is None:
        from PIL import ImageFilter as IF
        im = Image.fromarray((tex("2k_mars.jpg") * 255).astype(np.uint8)).filter(IF.GaussianBlur(1.6))
        T = np.asarray(im, np.float32) / 255
        hgt = np.asarray(im.convert("L").filter(IF.GaussianBlur(2.5)), np.float32) / 255
        gx = np.gradient(hgt, axis=1); gy = np.gradient(hgt, axis=0)
        _MT = (T, np.repeat(-gx[..., None], 3, 2) * 4, np.repeat(-gy[..., None], 3, 2) * 4)
    return _MT

def terrain(cv, t, alpha, river=0.0):
    """Perspective glide across a Mars surface region (texture-mapped ground plane)."""
    hz = 700; f = 900.0; h = 1.0
    ys = np.arange(hz + 1, H, dtype=np.float32) + 0.5
    xs = np.arange(W, dtype=np.float32) + 0.5 - W / 2
    z = h * f / (ys - hz)                      # forward distance per row
    X = xs[None, :] * z[:, None] / f           # lateral
    Z = np.broadcast_to(z[:, None], X.shape)
    head = 2.2 + 0.05 * t
    ch, sh = math.cos(head), math.sin(head)
    sc = 0.022
    cu, cv_ = 0.205 - 0.0016 * t * math.cos(head) * 0, 0.47 + 0.0
    cu = 0.215 + t * 0.004 * sh; cv_ = 0.50 - t * 0.004 * ch
    gu = cu + (X * ch + Z * sh) * sc * 0.5
    gv = cv_ + (X * sh - Z * ch) * sc
    T, GX, GY = mars_terrain_maps()
    uu, vv = gu.ravel() % 1, np.clip(gv.ravel(), 0, 1)
    c = sample(T, uu, vv).reshape(gu.shape + (3,))
    gx = sample(GX, uu, vv)[:, 0].reshape(gu.shape); gy_ = sample(GY, uu, vv)[:, 0].reshape(gu.shape)
    # relief from a smoothed luminance height field, lit from upper left
    shade = np.clip(1.0 + 9.0 * (gx * 0.8 + gy_ * 0.6), 0.55, 1.45)
    det = sample(tex("2k_mercury.jpg"), (gu.ravel() * 5) % 1, (gv.ravel() * 5) % 1).reshape(gu.shape + (3,)).mean(2)
    c = c * shade[..., None] * (0.82 + 0.4 * det[..., None]) * 0.95
    fog = (1 - np.exp(-z / 16.0))[:, None, None]
    sky_h = np.array([0.80, 0.60, 0.44], np.float32)
    c = c * (1 - fog) + sky_h * fog
    out = cv.a
    out[hz + 1:] = out[hz + 1:] * (1 - alpha) + c * alpha
    sky = np.linspace(0, 1, hz + 1, dtype=np.float32)[:, None, None]
    skyc = np.array([0.08, 0.07, 0.12], np.float32) * (1 - sky) + sky_h * sky ** 3
    out[:hz + 1] = out[:hz + 1] * (1 - alpha) + skyc * alpha
    if river > 0:
        # ancient watercourse: meandering path defined on the ground, projected
        pts = []
        for s in np.linspace(0, 1, 160)[: max(2, int(160 * river))]:
            Zw = 1.2 + s * 14
            Xw = 0.9 * math.sin(s * 9 + 0.6) + 0.5 * math.sin(s * 23) - 0.4
            if Zw > 0.2:
                pts.append((W / 2 + Xw * f / Zw, hz + h * f / Zw))
        v = Vec(); v.line(pts, col("#5FB8FF", 0.95 * alpha), 4.5); v.composite(cv)
        v = Vec(); v.line(pts, col("#5FB8FF", 0.5 * alpha), 12); v.composite(cv, blur=4)

def s06(cv, t):
    sid = 6; D = dur(sid)
    bg(cv, 5, t)
    tv = kw(sid, "ज्वालामुखी") - 0.6
    tr = kw(sid, "पुराने") - 0.2
    tm = vo_end(sid) + 0.15
    a_t = ease(seg(t, tv, tv + 0.8)) * (1 - ease(seg(t, tm, tm + 0.8)))
    a_m = ease(seg(t, tm, tm + 0.8))
    if t < tv + 1.0:
        a0 = ease(seg(t, 0, 1.0))
        globe(cv, 540, 800, lerp(280, 330, seg(t, 0, tv + 1)) * lerp(0.92, 1, a0), "2k_mars.jpg", spin=spin_fn(-75, 0.05, t),
              pitch=0.32, alpha=a0, atmo=(0.85, 0.55, 0.4), atmo_w=0.025, ambient=0.012)
    if a_m > 0:
        cam = dict(cx=540, cy=820, s=lerp(1.5, 1.7, seg(t, tm, D)), e=0.78, phi=0.3 + 0.02 * t)
        solar_map(cv, t, cam, belt=1.0, hi=None, alpha=a_m,
                  orbit_prog=[1, 1, 1, 1, 1, 0, 0, 0], planet_alpha=[1, 1, 1, 1, 1, 0, 0, 0])
        cv.text("Main asteroid belt", 540, 1112, "latb", 32, "#E3CFAE", a_m, anchor="ct")
        footnote(cv, "between Mars and Jupiter  ·  Illustrative scale", 540, 1160, a_m, anchor="ct", size=26)
    if a_t > 0:
        terrain(cv, t - tv, a_t, river=ease_io(seg(t, tr, tr + 2.4)))
        footnote(cv, "Surface view: illustrative", W - MX, 640, a_t, anchor="rt", size=26, color=WHITE)
        ra = a_t * seg(t, tr + 0.6, tr + 1.2)
        cv.text("Illustration of past water", 540, 1000, "latb", 30, "#9DD4FF", ra, anchor="ct")
    header(cv, t, "04", "MARS", "मंगल", sid=sid)
    chip(cv, t, "The Red Planet", 0, kw(sid, "लाल") - 0.4, tm + 0.1, sid=sid, accent=RED)
    chip(cv, t, "Evidence of ancient liquid water", 1, tr + 0.4, tm + 0.6, sid=sid, accent=BLUE)

# ============================================================ SCENE 07 — Jupiter
GRS_LON, GRS_LAT = (0.371 - 0.5) * 2 * math.pi, (0.5 - 0.617) * math.pi
def s07(cv, t):
    sid = 7; D = dur(sid)
    bg(cv, 6, t)
    tz = kw(sid, "ग्रेट") - 1.0; tb = kw(sid, "दस") - 0.6
    z = ease_io(seg(t, tz, tz + 2.6)) * (1 - ease_io(seg(t, tb, tb + 2.4)))
    pitch, roll = -0.12, 0.03
    lon_cam = -0.95 + 0.075 * t                 # GRS drifts from left toward centre
    spin = GRS_LON - lon_cam
    R0 = lerp(300, 320, seg(t, 0, tz))
    R = math.exp(lerp(math.log(R0), math.log(1100), z))
    # where the GRS lands on screen for a centred globe
    b = np.array([math.cos(GRS_LAT) * math.sin(lon_cam), math.sin(GRS_LAT), math.cos(GRS_LAT) * math.cos(lon_cam)])
    n = body_matrix(roll, pitch).T @ b
    cx = 540 - z * R * n[0]; cy = 800 + z * R * n[1]
    a0 = ease(seg(t, 0, 1.2))
    globe(cv, cx, cy, R * lerp(0.9, 1, a0), "2k_jupiter.jpg", spin=spin, roll=roll, pitch=pitch, alpha=a0, kind="gas", ambient=0.012)
    if z > 0.5:
        footnote(cv, "Great Red Spot — a giant storm", 540, 1110, ease(seg(z, 0.6, 0.9)), anchor="ct", size=28, color=WHITE)
    # spin axis + 10 h badge
    ax = window(t, tb + 1.6, D + 1)
    if ax > 0:
        a_ = body_matrix(roll, pitch).T @ np.array([0, 1.0, 0])
        v = Vec()
        p0 = (cx - a_[0] * R * 1.25, cy + a_[1] * R * 1.25); p1 = (cx + a_[0] * R * 1.25, cy - a_[1] * R * 1.25)
        v.line([p0, (cx - a_[0] * R * 1.0, cy + a_[1] * R * 1.0)], col(CYAN, 0.9), 3)
        v.arrow((cx + a_[0] * R * 0.98, cy - a_[1] * R * 0.98), p1, col(CYAN, 0.9), 3, 16)
        ang = np.linspace(0.3, 2 * math.pi - 0.6, 60)
        pts = [(p1[0] + 46 * math.cos(q), p1[1] + 50 + 14 * math.sin(q)) for q in ang]
        v.line(pts, col(CYAN, 0.9), 3)
        v.arrow(pts[-3], pts[-1], col(CYAN, 0.9), 3, 12)
        v.composite(cv, ax)
        cv.blit(rrect_sprite(150, 60, 30, fill=(8, 14, 34, 220), outline=col(CYAN, 0.8)), p1[0] + 70, p1[1] + 20, ax)
        cv.text("≈10 h", p1[0] + 145, p1[1] + 50, "latb", 32, CYAN, ax, anchor="cm", shadow=False)
    # true-scale size comparison (equatorial diameters 142,984 km vs 12,756 km)
    tc = kw(sid, "बड़ा") - 0.5
    ca = window(t, tc, tz + 0.2)
    if ca > 0:
        x0, y0, x1, y1 = 600, 236, 972, 548
        panel(cv, x0, y0, x1, y1, ca, CYAN)
        jr = 92; ecx = x0 + 60 + 2 * jr + 50
        globe(cv, x0 + 40 + jr, y0 + 40 + jr, jr, "2k_jupiter.jpg", spin=spin, kind="gas", alpha=ca, ambient=0.05)
        globe(cv, ecx, y0 + 40 + jr * 2 - jr * 12756 / 142984, jr * 12756 / 142984, "2k_earth_daymap.jpg", kind="earth", alpha=ca, ambient=0.05)
        cv.text("Earth", ecx, y0 + 40 + 2 * jr + 6, "lat", 22, WHITE, ca, anchor="ct")
        cv.text("Jupiter", x0 + 40 + jr, y0 + 40 + 2 * jr + 6, "lat", 22, WHITE, ca, anchor="ct")
        cv.text("Equatorial diameters to scale", (x0 + x1) / 2, y1 - 36, "lat", 22, MUTED, ca, anchor="ct")
    header(cv, t, "05", "JUPITER", "बृहस्पति", sid=sid)
    chip(cv, t, "Largest planet", 0, kw(sid, "बड़ा") - 0.3, tb + 0.3, sid=sid, accent=GOLD)
    chip(cv, t, "Rotation ≈{} hours", 0, tb + 0.6, sid=sid, value=(10, lambda x: f"{int(round(x))}"))
    chip(cv, t, "Great Red Spot = giant storm", 1, kw(sid, "ग्रेट") + 0.4, sid=sid, accent=RED)

# ============================================================ SCENE 08 — Saturn
def s08(cv, t):
    sid = 8; D = dur(sid)
    bg(cv, 7, t)
    up = ease_io(seg(t, 0.3, 7.5))
    pitch = lerp(0.045, 0.46, up); roll = -0.09
    R = lerp(175, 190, seg(t, 0, D))
    a0 = ease(seg(t, 0, 1.0))
    ring = saturn_ring(roll, pitch)
    ringed_globe(cv, 540, 800, R * lerp(0.94, 1, a0), "2k_saturn.jpg", ring, spin=-0.07 * t, roll=roll, pitch=pitch,
                 alpha=a0, kind="gas", ambient=0.015)
    ti = kw(sid, "छल्ले") - 0.2
    ia = window(t, ti, kw(sid, "दूसरा") + 0.2)
    if ia > 0:
        x0, y0, x1, y1 = 620, 236, 972, 560
        panel(cv, x0, y0, x1, y1, ia, CYAN)
        v = Vec(x0, y0, x1 - x0, y1 - y0)
        rng = np.random.default_rng(5)
        for j in range(26):
            px = x0 + 40 + rng.random() * (x1 - x0 - 80) + 10 * math.sin(t * 0.4 + j)
            py = y0 + 60 + rng.random() * (y1 - y0 - 150)
            ice = j % 3 != 0
            r = (6 + rng.random() * 18) if ice else (5 + rng.random() * 12)
            pts = [(px + r * (1 + 0.18 * math.sin(3 * q + j)) * math.cos(q), py + r * (1 + 0.18 * math.cos(2 * q + j)) * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 18)]
            v.poly(pts, fill=col("#DCEBFA", 0.95) if ice else col("#8C7B6B", 0.95))
        v.composite(cv, ia)
        cv.text("Ice", x0 + 30, y1 - 70, "latb", 26, "#DCEBFA", ia)
        cv.text("Rock", x0 + 100, y1 - 70, "latb", 26, "#BFA88F", ia)
        cv.text("Ring particles · magnified schematic", (x0 + x1) / 2, y1 - 34, "lat", 20, MUTED, ia, anchor="ct")
    header(cv, t, "06", "SATURN", "शनि", sid=sid)
    chip(cv, t, "Ice + rock rings", 0, ti + 0.2, sid=sid)
    chip(cv, t, "1 year ≈{} Earth years", 1, kw(sid, "चक्कर") - 0.4, sid=sid, accent=GOLD, value=(29.4, lambda x: f"{x:.1f}"))

# ============================================================ SCENE 09 — Uranus
def uranus_detail(c, u, v):
    lat = (0.5 - v) * math.pi
    band = 1 + 0.035 * np.sin(lat * 14) + 0.02 * np.sin(lat * 31 + 1)
    spot = np.exp(-(((u - 0.3) % 1 - 0.0) ** 2 / 0.0008 + (v - 0.38) ** 2 / 0.0006)) * 0.12
    spot += np.exp(-(((u - 0.72) % 1) ** 2 / 0.0012 + (v - 0.6) ** 2 / 0.0005)) * 0.08
    return c * band[:, None] + spot[:, None]

def s09(cv, t):
    sid = 9; D = dur(sid)
    bg(cv, 8, t)
    roll, pitch = 98 * R2D, 0.16        # axis 98° from orbital normal (screen vertical = normal)
    a0 = ease(seg(t, 0, 1.0))
    R = lerp(165, 180, seg(t, 0, D))
    ring = uranus_ring(roll, pitch)
    ringed_globe(cv, 540, 720, R * lerp(0.94, 1, a0), "2k_uranus.jpg", ring, spin=0.35 * t, roll=roll, pitch=pitch,
                 alpha=a0, kind="gas", atmo=(0.6, 0.85, 0.9), atmo_w=0.03, detail=uranus_detail, ambient=0.012)
    # orbital plane line + normal through the globe
    v = Vec()
    oa = window(t, 1.0, D + 1)
    v.line([(MX - 20, 720), (W - MX + 20, 720)], col("#7FB8D6", 0.35 * oa), 2)
    v.composite(cv)
    ta = kw(sid, "अट्ठानवे") - 0.6
    tm = kw(sid, "मीथेन") - 0.5
    da = window(t, ta, tm + 0.3)
    x0, y0, x1, y1 = MX, 945, W - MX, 1140
    if da > 0:
        panel(cv, x0, y0, x1, y1, da, CYAN)
        ox, oy = 300, 1052
        v = Vec(x0, y0, x1 - x0, y1 - y0)
        v.line([(ox - 150, oy), (ox + 150, oy)], col("#7FB8D6", 0.9), 2.5)
        for k in range(0, 10):
            v.line([(ox, oy - 78 + k * 16), (ox, oy - 70 + k * 16)], col(WHITE, 0.7), 2)
        p = ease_out(seg(t, ta + 0.4, ta + 1.6))
        ang = 98 * p * R2D
        tip = (ox + 84 * math.sin(ang), oy - 84 * math.cos(ang))
        v.arrow((ox - 70 * math.sin(ang), oy + 70 * math.cos(ang)), tip, col(GOLD), 3.5, 14)
        arc = [(ox + 42 * math.sin(q), oy - 42 * math.cos(q)) for q in np.linspace(0, ang, 40)]
        v.line(arc, col(GOLD, 0.9), 2.5)
        v.composite(cv, da)
        cv.text(f"{int(round(98 * p))}°", ox + 40, oy - 92, "latb", 34, GOLD, da)
        cv.text("orbital normal", ox - 14, oy - 92, "lat", 22, WHITE, da, anchor="rt")
        cv.text("orbital plane", ox - 150, oy + 10, "lat", 22, "#9FD3EA", da)
        cv.text("Axis tilt measured", 640, 990, "latb", 28, WHITE, da, anchor="ct")
        cv.text("from the orbital normal", 640, 1030, "lat", 26, WHITE, da, anchor="ct")
        cv.text("(schematic)", 640, 1072, "lat", 22, MUTED, da, anchor="ct")
    ma = window(t, tm, D + 1)
    if ma > 0:
        panel(cv, x0, y0, x1, y1, ma, CYAN)
        v = Vec(x0, y0, x1 - x0, y1 - y0)
        v.rect(560, 975, 700, 1112, fill=col("#7FD3DE", 0.25), r=10)
        p = seg(t, tm + 0.3, tm + 1.6)
        cols = ["#FF5A4E", "#FFB347", "#FFF27A", "#7BEA8A", "#59C9F2", "#6F7BFF"]
        for j, c_ in enumerate(cols):
            yy = 990 + j * 20
            v.line([(150, yy), (150 + 410 * ease_out(p), yy)], col(c_, 0.9), 5)
        q = seg(t, tm + 1.5, tm + 2.8)
        for j, c_ in enumerate(cols[1:], 1):
            yy = 990 + j * 20
            if q > 0:
                v.line([(700, yy), (700 + 230 * ease_out(q), yy)], col(c_, 0.9 if j >= 3 else 0.35), 5)
        v.composite(cv, ma)
        cv.text("Sunlight", 150, 958, "lat", 22, WHITE, ma)
        cv.text("Methane", 630, 950, "latb", 24, "#BFF3F7", ma, anchor="ct")
        cv.text("absorbs red", 630, 1114, "lat", 22, RED, ma * seg(t, tm + 1.4, tm + 1.9), anchor="ct")
        cv.text("blue-green out", 960, 1114, "lat", 22, "#8FF0E0", ma * q, anchor="rt")
    header(cv, t, "07", "URANUS", "यूरेनस", sid=sid)
    chip(cv, t, "Ice giant", 0, kw(sid, "आइस") - 0.2, sid=sid)
    chip(cv, t, "Axial tilt ≈{}°", 1, ta + 0.4, sid=sid, accent=GOLD, value=(98, lambda x: f"{int(round(x))}"))

# ============================================================ SCENE 10 — Neptune
def s10(cv, t):
    sid = 10; D = dur(sid)
    bg(cv, 9, t)
    tm = kw(sid, "साल") - 1.3
    a_m = ease(seg(t, tm, tm + 0.8))
    if a_m < 1:
        a0 = ease(seg(t, 0, 1.0)) * (1 - a_m)
        R = lerp(290, 320, seg(t, 0, tm))
        cx, cy = 540, 800
        roll, pitch = -0.1, 0.12
        globe(cv, cx, cy, R * lerp(0.92, 1, a0), "2k_neptune.jpg", spin=spin_fn(-30, 0.06, t), roll=roll, pitch=pitch,
              alpha=a0, kind="gas", atmo=(0.35, 0.55, 1.0), atmo_w=0.04, ambient=0.012, gain=0.92)
        tw = kw(sid, "हवाएँ") - 0.4
        wa = window(t, tw, tm + 0.3) * a0
        if wa > 0:
            v = Vec()
            M = body_matrix(roll, pitch).T
            for lat_d in (-55, -38, -22, -6, 12, 30, 48):
                lat = lat_d * R2D
                speed = 0.9 if abs(lat_d) < 25 else -0.6
                for d in range(3):
                    ph = (t * 0.35 * speed + d * 0.7 + lat_d * 0.05) % (2 * math.pi)
                    pts = []
                    for q in np.linspace(ph - 0.42, ph, 22):
                        lon = q - math.pi
                        b = np.array([math.cos(lat) * math.sin(lon), math.sin(lat), math.cos(lat) * math.cos(lon)])
                        n = M @ b
                        if n[2] > 0.08:
                            pts.append((cx + R * 1.01 * n[0], cy - R * 1.01 * n[1]))
                    if len(pts) > 2:
                        v.line(pts, col(WHITE, 0.75), 2.6)
                        v.arrow(pts[-2], pts[-1], col(WHITE, 0.75), 2.6, 9)
            v.composite(cv, wa)
            footnote(cv, "Illustrative wind flow", 540, 1112, wa, anchor="ct", size=28, color=WHITE)
    if a_m > 0:
        cam = dict(cx=lerp(330, 290, seg(t, tm, D)), cy=800, s=1.15, e=0.8, phi=-0.55 + 0.01 * t)
        prog = [1] * 7 + [0]
        pos = solar_map(cv, t, cam, orbit_prog=[0.55] * 7 + [ease_io(seg(t, tm + 0.6, tm + 3.6))], alpha=a_m, hi=7,
                        sun_r=9, belt=0.0)
        nx, ny, f = pos[7]
        cv.text("8", nx + 26, ny - 50, "disp", 44, CYAN, a_m * ease(seg(t, tm + 0.6, tm + 1.2)))
        footnote(cv, "Illustrative scale", W - MX, 1112, a_m, anchor="rt", size=26)
    header(cv, t, "08", "NEPTUNE", "नेपच्यून", sid=sid)
    chip(cv, t, "Winds can exceed {} km/h", 0, kw(sid, "हज़ार") - 0.6, sid=sid, value=(2000, lambda x: f"{int(round(x / 10) * 10):,}"))
    chip(cv, t, "1 year ≈{} Earth years", 1, kw(sid, "पैंसठ") - 0.6, sid=sid, accent=GOLD, value=(165, lambda x: f"{int(round(x))}"))

# ============================================================ SCENE 11 — Pluto + close
def s11(cv, t):
    sid = 11; D = dur(sid)
    bg(cv, 10, t)
    tq = kw(sid, "आपको") - 0.3
    k = ease_io(seg(t, 0, 6))
    cam = dict(cx=540, cy=800, s=lerp(1.0, 0.78, k), e=lerp(0.85, 0.72, k), phi=-0.7 + 0.02 * t)
    dim = 1 - 0.45 * ease(seg(t, tq, tq + 1.2))
    solar_map(cv, t, cam, alpha=dim, kuiper=ease(seg(t, 1.5, 3.5)), labels=window(t, 0.6, tq + 0.4), pluto=ease(seg(t, 1.0, 2.5)))
    ka = window(t, 2.0, tq + 0.4)
    cv.text("Kuiper Belt →", W - MX, 1035, "latb", 30, "#C9D8E6", ka, anchor="rt")
    footnote(cv, "continues beyond Neptune  ·  Illustrative scale", W - MX, 1076, ka, anchor="rt", size=24)
    tp = kw(sid, "प्लूटो") - 0.2
    pa = window(t, tp, tq + 0.4)
    if pa > 0:
        x0, y0, x1, y1 = MX, MT + 10, W - MX, MT + 250
        panel(cv, x0, y0, x1, y1, pa, GOLD)
        globe(cv, x0 + 125, (y0 + y1) / 2, 95, "pluto", spin=1.3 * 0 + 0.1 * t, pitch=0.15, alpha=pa, ambient=0.02)
        cv.text("PLUTO = DWARF PLANET", x0 + 250, y0 + 58, "disp", 44, WHITE, pa)
        cv.text("बौना ग्रह", x0 + 250, y0 + 122, "devb", 52, GOLD, pa)
        cv.text("Separate inset · not to scale", x0 + 250, y0 + 192, "lat", 22, MUTED, pa)
    qa = window(t, tq, D + 1, 0.8)
    if qa > 0:
        yy = (1 - ease_out(seg(t, tq, tq + 1.0))) * 24
        cv.text("आपका पसंदीदा ग्रह", 540, 1100 + yy, "devb", 66, WHITE, qa, anchor="ct")
        cv.text("कौन सा है?", 540, 1190 + yy, "devb", 66, GOLD, qa, anchor="ct")
# ============================================================ SCENE 12 — channel outro
YT_RED = "#FF0033"; CHANNEL = "TheCloudMindAI"; HANDLE = "@TheCloudMindAI"

def avatar(cv, cx, cy, R, t, a):
    """Channel mark: Earth inside a rotating cyan-gold ring with an orbiting moon."""
    v = Vec(cx - R - 40, cy - R - 40, 2 * R + 80, 2 * R + 80)
    v.circle(cx, cy, R, fill=col("#0A1430", 0.96))
    seg_n = 90; rot = t * 0.9
    for k in range(seg_n):
        q0 = rot + 2 * math.pi * k / seg_n; q1 = q0 + 2 * math.pi / seg_n + 0.01
        f = 0.5 + 0.5 * math.cos(q0 - rot)
        c = tuple(int(lerp(x, y, f)) for x, y in zip(hexc(GOLD)[:3], hexc(CYAN)[:3]))
        v.line([(cx + (R + 2) * math.cos(q0), cy + (R + 2) * math.sin(q0)), (cx + (R + 2) * math.cos(q1), cy + (R + 2) * math.sin(q1))], c + (255,), 7)
    v.composite(cv, a)
    # orbit (back half), globe, orbit (front half) for correct depth
    th = t * 1.4
    orb = lambda q: (cx + R * 0.78 * math.cos(q), cy + R * 0.26 * math.sin(q) - R * 0.04)
    for half in (0, 1):
        if half == 1:
            globe(cv, cx, cy, R * 0.52, "2k_earth_daymap.jpg", spin=1.4 - 0.25 * t, roll=-0.3, pitch=0.25, alpha=a,
                  kind="earth", clouds="2k_earth_clouds.jpg", night="2k_earth_nightmap.jpg", atmo=(0.35, 0.6, 1.0), atmo_w=0.06)
        v = Vec(cx - R, cy - R, 2 * R, 2 * R)
        qs = np.linspace(math.pi, 2 * math.pi, 60) if half == 0 else np.linspace(0, math.pi, 60)
        v.line([orb(q) for q in qs], col(CYAN, 0.75), 3)
        mq = th % (2 * math.pi)
        if (mq > math.pi) == (half == 0):
            mx, my = orb(mq); v.circle(mx, my, 9, fill=col(GOLD))
        v.composite(cv, a)

def bell_icon(v, x, y, s, ang, fill, stroke):
    """Notification bell; ang swings it about its top pivot."""
    pts = []
    for q in np.linspace(math.pi, 2 * math.pi, 24):          # dome
        pts.append((0.62 * math.cos(q), -0.25 + 0.75 * math.sin(q)))
    pts += [(0.62, 0.25), (0.82, 0.55), (-0.82, 0.55), (-0.62, 0.25)]
    c, si = math.cos(ang), math.sin(ang)
    tr = lambda p: (x + s * (p[0] * c - (p[1] + 1) * si), y + s * (p[0] * si + (p[1] + 1) * c - 1))
    v.poly([tr(p) for p in pts], fill=fill, outline=stroke, width=2)
    kx, ky = tr((0, -1.05)); v.circle(kx, ky, s * 0.13, fill=stroke)
    bx, by = tr((0.0 + 0.25 * si, 0.78)); v.circle(bx, by, s * 0.17, fill=stroke)

def cursor(cv, x, y, a, press=0.0):
    v = Vec(x - 10, y - 10, 90, 110)
    k = 1 - 0.12 * press
    pts = [(0, 0), (0, 62), (15, 48), (27, 74), (37, 69), (25, 44), (45, 44)]
    v.poly([(x + px * k, y + py * k) for px, py in pts], fill=col(WHITE), outline=col("#0B1020"), width=3)
    v.composite(cv, a)

def s12(cv, t):
    sid = 12; D = dur(sid)
    bg(cv, 11, t)
    # faint concentric orbits behind the mark
    ra = ease(seg(t, 0, 1.2))
    v = Vec()
    for i, r in enumerate([230, 300, 380, 470]):
        pts = [(540 + r * math.cos(q), 600 + r * 0.32 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 160)]
        v.line(pts, col("#7FB8D6", 0.16), 1.6)
        q = t * 0.25 * (230 / r) ** 1.5 + i * 1.7
        v.circle(540 + r * math.cos(q), 600 + r * 0.32 * math.sin(q), 5 - i * 0.6, fill=col(WHITE, 0.6))
    v.composite(cv, ra)
    a0 = ease_out(seg(t, 0.1, 1.0))
    avatar(cv, 540, 600 - 20 * (1 - a0), 165, t, a0)
    # glow pulse behind avatar on reveal
    if t < 2.0:
        v = Vec(); p = seg(t, 0.3, 1.8)
        v.circle(540, 600, 170 + 120 * p, outline=col(CYAN, 0.5 * (1 - p)), width=4); v.composite(cv)
    na = ease(seg(t, 0.55, 1.2)); dy = (1 - ease_out(seg(t, 0.55, 1.3))) * 26
    w1 = text_width("TheCloudMind", 92, "disp"); w2 = text_width("AI", 92, "disp")
    x = 540 - (w1 + w2) / 2
    cv.text("TheCloudMind", x, 820 + dy, "disp", 92, WHITE, na)
    cv.text("AI", x + w1, 820 + dy, "disp", 92, CYAN, na)
    cv.text(HANDLE, 540, 938 + dy, "lat", 34, MUTED, ease(seg(t, 0.9, 1.5)), anchor="ct")
    cv.text("ऐसी ही रोचक जानकारी के लिए", 540, 1006, "devb", 46, GOLD, ease(seg(t, kw(sid, "ऐसी") - 0.2, kw(sid, "ऐसी") + 0.4)), anchor="ct")
    # --- buttons
    tf, ts, tb = kw(sid, "फॉलो") + 0.15, kw(sid, "सब्सक्राइब") + 0.35, kw(sid, "बेल") + 0.35
    by0 = 1092; bh = 100
    sx0, sw = 262, 432; bx = sx0 + sw + 24
    ba = ease(seg(t, 1.0, 1.5)); bdy = (1 - ease_out(seg(t, 1.0, 1.6))) * 30
    subd = t >= ts
    fill_s = (58, 62, 74, 255) if subd else hexc(YT_RED)
    cv.blit(rrect_sprite(sw, bh, 50, fill=fill_s), sx0, by0 + bdy, ba)
    if subd:
        cv.text("SUBSCRIBED ✓", sx0 + sw / 2, by0 + bdy + bh / 2 - 2, "latb", 38, "#E8EAED", ba, anchor="cm", shadow=False)
    else:
        v = Vec(sx0, by0, 120, bh + 40)
        px, py = sx0 + 52, by0 + bdy + bh / 2
        v.rect(px - 22, py - 16, px + 22, py + 16, fill=col(WHITE), r=8)
        v.poly([(px - 7, py - 9), (px - 7, py + 9), (px + 9, py)], fill=hexc(YT_RED))
        v.composite(cv, ba)
        cv.text("SUBSCRIBE", sx0 + sw / 2 + 30, by0 + bdy + bh / 2 - 2, "latb", 40, WHITE, ba, anchor="cm", shadow=False)
    # bell button
    bell_on = t >= tb
    cv.blit(rrect_sprite(bh, bh, 50, fill=(58, 62, 74, 255) if bell_on else (24, 30, 48, 255), outline=col(WHITE, 0.35)), bx, by0 + bdy, ba)
    sw_ang = 0.45 * math.sin((t - tb) * 22) * math.exp(-(t - tb) * 2.6) if bell_on else 0.0
    v = Vec(bx, by0, bh, bh + 40)
    bell_icon(v, bx + bh / 2, by0 + bdy + bh / 2 + 2, 26, sw_ang, hexc(GOLD) if bell_on else col(WHITE, 0.0), hexc(GOLD) if bell_on else hexc(WHITE))
    v.composite(cv, ba)
    # follow button
    fy = by0 + bh + 22; fw = sw + 24 + bh
    fol = t >= tf
    fa = ease(seg(t, 1.2, 1.7)); fdy = (1 - ease_out(seg(t, 1.2, 1.8))) * 30
    cv.blit(rrect_sprite(fw, bh, 50, fill=(103, 223, 242, 255) if fol else (8, 14, 34, 200), outline=col(CYAN), ow=3), sx0, fy + fdy, fa)
    cv.text("FOLLOWING ✓" if fol else "FOLLOW  +", sx0 + fw / 2, fy + fdy + bh / 2 - 2, "latb", 40, "#05222A" if fol else CYAN, fa, anchor="cm", shadow=False)
    # click ripples
    for tc, (rx, ry) in ((tf, (sx0 + fw / 2, fy + bh / 2)), (ts, (sx0 + sw / 2, by0 + bh / 2)), (tb, (bx + bh / 2, by0 + bh / 2))):
        p = seg(t, tc, tc + 0.6)
        if 0 < p < 1:
            v = Vec(); v.circle(rx, ry, 20 + 90 * ease_out(p), outline=col(WHITE, 0.7 * (1 - p)), width=4); v.composite(cv)
    # cursor path: enter -> follow -> subscribe -> bell -> exit
    keys = [(tf - 1.1, (930, 1560)), (tf - 0.1, (sx0 + fw / 2 + 40, fy + bh / 2 + 10)),
            (ts - 0.25, (sx0 + sw / 2 + 60, by0 + bh / 2 + 6)), (tb - 0.25, (bx + bh / 2 + 6, by0 + bh / 2 + 8)),
            (tb + 1.0, (bx + bh / 2 + 60, by0 + bh / 2 + 180)), (tb + 1.6, (1150, 1500))]
    if keys[0][0] <= t <= keys[-1][0]:
        for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                k = ease_io(seg(t, t0, t1)); cx_, cy_ = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
        press = max(max(0.0, 1 - abs(t - tc) / 0.12) for tc in (tf, ts, tb))
        cursor(cv, cx_, cy_, ease(seg(t, keys[0][0], keys[0][0] + 0.3)) * (1 - ease(seg(t, keys[-1][0] - 0.3, keys[-1][0]))), press)
    la = window(t, vo_end(sid) + 0.3, D + 1, 0.6)
    cv.text("लाइक   •   शेयर   •   कमेंट", 540, 1440, "devb", 44, WHITE, la, anchor="ct")
    cv.text("Like  ·  Share  ·  Comment", 540, 1506, "lat", 28, MUTED, la, anchor="ct")
    fo = ease(seg(t, D - 0.9, D))
    if fo > 0:
        cv.a[:] = cv.a * (1 - fo) + BG_RGB * fo

SCENE_FUNCS = {1: s01, 2: s02, 3: s03, 4: s04, 5: s05, 6: s06, 7: s07, 8: s08, 9: s09, 10: s10, 11: s11, 12: s12}

# ------------------------------------------------------------ captions
def captions(cv, g):
    for c in TL["cues"]:
        if c["t0"] - 0.15 <= g <= c["t1"] + 0.15:
            a = ease(seg(g, c["t0"] - 0.12, c["t0"] + 0.05)) * (1 - ease(seg(g, c["t1"] - 0.05, c["t1"] + 0.12)))
            lines = c["lines"]
            size = 46
            lw = max(text_width(l, size, "devb") for l in lines)
            bh = 72 * len(lines) + 28
            y_bot = 1530
            bw = int(min(W - 2 * MX + 40, lw + 56))
            cv.blit(rrect_sprite(bw, bh, 18, fill=(4, 7, 20, 175)), 540 - bw / 2, y_bot - bh, a)
            for i, l in enumerate(lines):
                cv.text(l, 540, y_bot - bh + 14 + 72 * i + 36, "devb", size, WHITE, a, anchor="cm", shadow=False)

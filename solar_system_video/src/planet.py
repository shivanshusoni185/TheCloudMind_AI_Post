"""Procedural renderer: textured, lit spheres (orthographic ray cast),
atmospheres, Saturn/Uranus rings with mutual shadows, Sun, starfield."""
import functools, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import ROOT, W, H, BG_RGB

TEX = os.path.join(ROOT, "assets", "textures")
# One sunlight direction for every hero shot (camera space: x right, y up, z to viewer)
SUN_L = np.array([-0.72, 0.30, 0.62]); SUN_L = SUN_L / np.linalg.norm(SUN_L)

@functools.lru_cache(None)
def tex(name):
    if name == "pluto":
        return pluto_tex()
    p = os.path.join(TEX, name)
    return np.asarray(Image.open(p).convert("RGB"), np.float32) / 255.0

def sample(t, u, v):
    """Bilinear sample, u wraps, v clamps. u, v flat arrays in [0,1]."""
    h, w = t.shape[:2]
    x = u * w - 0.5; y = np.clip(v * h - 0.5, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int32); y0 = y.astype(np.int32)
    fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    x0 %= w; x1 = (x0 + 1) % w; y1 = np.minimum(y0 + 1, h - 1)
    return ((t[y0, x0] * (1 - fx) + t[y0, x1] * fx) * (1 - fy) +
            (t[y1, x0] * (1 - fx) + t[y1, x1] * fx) * fy)

def rot_x(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_z(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def body_matrix(roll, pitch):
    """Camera->body rotation. Body north pole in camera space = M.T @ (0,1,0).
    pitch>0 tips the north pole toward the viewer; roll rotates it clockwise on screen."""
    return rot_x(-pitch) @ rot_z(roll)

def axis_vec(roll, pitch):
    return body_matrix(roll, pitch).T @ np.array([0.0, 1.0, 0.0])

def smoothstep(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)

def globe(cv, cx, cy, R, texname, spin=0.0, roll=0.0, pitch=0.0, L=SUN_L, alpha=1.0,
          kind="rocky", atmo=None, atmo_w=0.06, clouds=None, cloud_spin=None, night=None,
          ring=None, ambient=0.018, limb=0.0, gain=1.0, emissive=False, detail=None):
    """Render a planet into canvas cv (in place). Returns nothing.
    kind: rocky | gas | earth. ring: dict for ring shadows on the globe."""
    if R < 0.5 or alpha <= 0.003:
        return
    halo = (1 + atmo_w * 1.6) if atmo is not None else 1.0
    ext = R * halo + 2
    x0, x1 = int(max(0, math.floor(cx - ext))), int(min(W, math.ceil(cx + ext)))
    y0, y1 = int(max(0, math.floor(cy - ext))), int(min(H, math.ceil(cy + ext)))
    if x0 >= x1 or y0 >= y1:
        return
    xs = (np.arange(x0, x1, dtype=np.float32) + 0.5 - cx) / R
    ys = -(np.arange(y0, y1, dtype=np.float32) + 0.5 - cy) / R
    X, Y = np.meshgrid(xs, ys)
    r2 = X * X + Y * Y
    rr = np.sqrt(r2)
    dst = cv.a[y0:y1, x0:x1]
    cov = np.clip((1 - rr) * R + 0.5, 0, 1) * alpha        # anti-aliased disk coverage
    inside = cov > 0
    L = np.asarray(L, np.float32)
    if inside.any():
        Xi, Yi = X[inside], Y[inside]
        Zi = np.sqrt(np.clip(1 - Xi * Xi - Yi * Yi, 0, 1))
        N = np.stack([Xi, Yi, Zi], 1)
        M = body_matrix(roll, pitch).astype(np.float32)
        B = N @ M.T
        lat = np.arcsin(np.clip(B[:, 1], -1, 1))
        lon = np.arctan2(B[:, 0], B[:, 2])
        u = ((lon + spin) / (2 * math.pi) + 0.5) % 1.0
        v = 0.5 - lat / math.pi
        c = sample(tex(texname), u, v)
        if detail is not None:
            c = detail(c, u, v)
        d = N @ L
        if emissive:
            shade = (0.42 + 0.58 * Zi ** 0.55)[:, None]
            col = c * shade * gain
        else:
            diff = np.clip(d, 0, 1) ** 0.9 * smoothstep(-0.04, 0.12, d)
            if kind == "gas":
                diff = diff * (0.55 + 0.45 * Zi ** 0.35)
            if clouds is not None:
                cu = ((lon + (cloud_spin if cloud_spin is not None else spin)) / (2 * math.pi) + 0.5) % 1.0
                cl = sample(tex(clouds), cu, v)[:, :1]
                cl = np.clip((cl - 0.08) * 1.15, 0, 1)
                c = c * (1 - cl * 0.92) + cl * 0.97
            if ring is not None:
                diff = diff * ring_shadow(N, L, ring)
            col = c * (diff[:, None] * gain + ambient)
            if kind == "earth":
                ocean = np.clip((c[:, 2] - c[:, 0] * 1.1 - 0.06) * 4, 0, 1)
                if clouds is not None:
                    ocean = ocean * (1 - cl[:, 0])
                Hh = L + np.array([0, 0, 1], np.float32); Hh = Hh / np.linalg.norm(Hh)
                spec = np.clip(N @ Hh, 0, 1) ** 60 * 0.55 * ocean
                col = col + spec[:, None] * np.array([1.0, 0.95, 0.85])
                if night is not None:
                    nl = sample(tex(night), u, v)
                    nl = np.clip((nl - 0.08) * 1.6, 0, 1) * np.array([1.0, 0.82, 0.55])
                    col = col + nl * (1 - smoothstep(-0.15, 0.05, d))[:, None] * 0.9
            if atmo is not None:
                rim = (1 - Zi) ** 2.6 * np.clip(d + 0.35, 0, 1.2)
                col = col * (1 - rim[:, None] * 0.25) + rim[:, None] * np.asarray(atmo) * 0.9
        a = cov[inside][:, None]
        sub = dst[inside]
        dst[inside] = sub * (1 - a) + np.clip(col, 0, 4) * a
    if atmo is not None and not emissive:
        out = (rr >= 0.985) & (rr < halo)
        if out.any():
            h_ = (rr[out] - 1) / (halo - 1)
            nx, ny = X[out] / rr[out], Y[out] / rr[out]
            lit = np.clip(nx * L[0] + ny * L[1] + 0.25, 0, 1)
            g = np.exp(-np.clip(h_, 0, None) * 5.5) * lit * alpha * 0.85
            dst[out] += g[:, None] * np.asarray(atmo, np.float32)

def ring_shadow(N, L, ring):
    """Fraction of light reaching sphere points N after passing the ring plane."""
    A = ring["axis"]
    den = L @ A
    if abs(den) < 1e-4:
        return np.ones(len(N), np.float32)
    s = -(N @ A) / den
    q = N + s[:, None] * L[None, :]
    r = np.linalg.norm(q, axis=1)
    a = ring_alpha_at(r, ring)
    return np.where(s > 0, 1 - a * 0.85, 1.0)

@functools.lru_cache(None)
def saturn_ring_profile():
    im = np.asarray(Image.open(os.path.join(TEX, "2k_saturn_ring_alpha.png")).convert("RGBA"), np.float32) / 255
    prof = im[im.shape[0] // 2]
    return prof  # (2048, 4) inner -> outer

@functools.lru_cache(None)
def uranus_ring_profile():
    n = 1024; r = np.linspace(0, 1, n); a = np.zeros(n)
    for c, wdt, s in [(0.08, .010, .35), (0.16, .008, .3), (0.24, .008, .3), (0.42, .010, .35), (0.55, .009, .35),
                      (0.63, .012, .4), (0.72, .012, .4), (0.95, .03, .75)]:
        a += s * np.exp(-((r - c) / wdt) ** 2)
    rgb = np.ones((n, 3)) * np.array([0.55, 0.6, 0.62])
    return np.concatenate([rgb, np.clip(a, 0, 1)[:, None]], 1).astype(np.float32)

def ring_alpha_at(r, ring):
    prof = ring["profile"]; r_in, r_out = ring["r_in"], ring["r_out"]
    t = (r - r_in) / (r_out - r_in)
    ok = (t >= 0) & (t < 1)
    idx = np.clip((t * (len(prof) - 1)).astype(np.int32), 0, len(prof) - 1)
    return np.where(ok, prof[idx, 3] * ring.get("opacity", 1.0), 0.0)

def rings(cv, cx, cy, R, ring, part, L=SUN_L, alpha=1.0):
    """Draw the 'back' (z<0) or 'front' (z>0) half of a ring system."""
    A = ring["axis"]; prof = ring["profile"]; r_in, r_out = ring["r_in"], ring["r_out"]
    ext = R * r_out + 2
    x0, x1 = int(max(0, cx - ext)), int(min(W, cx + ext))
    # vertical extent of the projected ellipse
    ey = ext * math.sqrt(max(1 - A[1] ** 2, 0.0)) + 3 if abs(A[2]) > 1e-3 else 4
    ey = max(ey, R * r_out * abs(A[0]) + 4) if abs(A[1]) < 0.999 else ey
    ey = min(ext, ey + R * r_out * 0.02 + 4)
    y0, y1 = int(max(0, cy - ext)), int(min(H, cy + ext))
    if x0 >= x1 or y0 >= y1 or abs(A[2]) < 1e-3:
        return
    xs = (np.arange(x0, x1, dtype=np.float32) + 0.5 - cx) / R
    ys = -(np.arange(y0, y1, dtype=np.float32) + 0.5 - cy) / R
    X, Y = np.meshgrid(xs, ys)
    Z = -(A[0] * X + A[1] * Y) / A[2]
    r = np.sqrt(X * X + Y * Y + Z * Z)
    t = (r - r_in) / (r_out - r_in)
    m = (t >= 0) & (t < 1) & ((Z < 0) if part == "back" else (Z >= 0))
    if not m.any():
        return
    # sample with a small radial footprint to reduce aliasing of thin gaps
    fp = np.clip(1.0 / (R * (r_out - r_in)) / max(abs(A[2]), 0.05), 0, 0.05)
    tt = t[m]
    acc = 0
    for o in (-0.5, -0.17, 0.17, 0.5):
        idx = np.clip(((tt + o * fp) * (len(prof) - 1)).astype(np.int32), 0, len(prof) - 1)
        acc = acc + prof[idx]
    s = acc / 4
    a = s[:, 3] * ring.get("opacity", 1.0) * alpha
    q = np.stack([X[m], Y[m], Z[m]], 1)
    b = q @ L; c = (q * q).sum(1) - 1
    disc = b * b - c
    shadow = (disc > 0) & ((-b + np.sqrt(np.clip(disc, 0, None))) > 0) & (b < 0)
    lit = 0.35 + 0.65 * abs(float(L @ A)) ** 0.5
    col = s[:, :3] * ring.get("tint", 1.0) * lit * np.where(shadow, 0.08, 1.0)[:, None]
    dst = cv.a[y0:y1, x0:x1]
    sub = dst[m]
    dst[m] = sub * (1 - a[:, None]) + col * a[:, None]

def ringed_globe(cv, cx, cy, R, texname, ring, spin=0.0, roll=0.0, pitch=0.0, L=SUN_L, alpha=1.0, **kw):
    rings(cv, cx, cy, R, ring, "back", L, alpha)
    globe(cv, cx, cy, R, texname, spin=spin, roll=roll, pitch=pitch, L=L, alpha=alpha, ring=ring, **kw)
    rings(cv, cx, cy, R, ring, "front", L, alpha)

def saturn_ring(roll, pitch):
    return dict(axis=axis_vec(roll, pitch).astype(np.float32), profile=saturn_ring_profile(),
                r_in=1.239, r_out=2.27, opacity=0.95, tint=np.array([1.0, 0.97, 0.9], np.float32))

def uranus_ring(roll, pitch):
    return dict(axis=axis_vec(roll, pitch).astype(np.float32), profile=uranus_ring_profile(),
                r_in=1.60, r_out=2.02, opacity=0.8, tint=np.array([0.7, 0.75, 0.78], np.float32))

# ------------------------------------------------------------------ Sun
def sun(cv, cx, cy, R, t, alpha=1.0, glow=1.0):
    """Emissive photosphere with limb darkening, slow granulation drift and glow."""
    ext = R * 2.6
    x0, x1 = int(max(0, cx - ext)), int(min(W, cx + ext))
    y0, y1 = int(max(0, cy - ext)), int(min(H, cy + ext))
    if x0 < x1 and y0 < y1 and glow > 0:
        xs = (np.arange(x0, x1, dtype=np.float32) + 0.5 - cx) / R
        ys = (np.arange(y0, y1, dtype=np.float32) + 0.5 - cy) / R
        rr = np.sqrt(xs[None, :] ** 2 + ys[:, None] ** 2)
        g = (np.exp(-np.clip(rr - 1, 0, None) * 3.2) * 0.55 + np.exp(-np.clip(rr - 1, 0, None) * 0.9) * 0.18)
        g *= (rr > 0.97) * glow * alpha * np.clip(1 - (rr - 1) / 1.6, 0, 1) ** 2
        cv.a[y0:y1, x0:x1] += g[..., None] * np.array([1.0, 0.62, 0.25], np.float32)
    def gran(c, u, v):
        c2 = sample(tex("2k_sun.jpg"), (u * 1.0 + 0.37 + t * 0.004) % 1, (v + 0.11) % 1)
        w = 0.5 + 0.5 * math.sin(t * 0.7)
        c = c * (0.6 + 0.4 * w) + c2 * (0.4 - 0.4 * w)
        lum = c.mean(1, keepdims=True)
        m = lum.mean()
        lum = m + (lum - m) * 0.45          # restrained contrast: plasma, not campfire
        fine = sample(tex("2k_mercury.jpg"), (u * 6 + t * 0.002) % 1, (v * 6) % 1).mean(1, keepdims=True)
        lum = lum + (fine - 0.45) * 0.12    # fine granulation texture
        warm = np.concatenate([np.ones_like(lum) * 1.0, 0.62 + lum * 0.38, 0.22 + lum * 0.5], 1)
        return np.clip(warm * (0.82 + lum * 0.42), 0, 1.3)
    globe(cv, cx, cy, R, "2k_sun.jpg", spin=t * 0.03, alpha=alpha, emissive=True, gain=1.15, detail=gran)

@functools.lru_cache(None)
def prominence_sprite(R):
    """Restrained looping prominence, rendered once per radius (additive RGB)."""
    s = int(R * 0.7); img = Image.new("RGB", (s * 2, s * 2), (0, 0, 0)); d = ImageDraw.Draw(img)
    for k, (hh, ww, wd, c) in enumerate([(0.62, 0.30, 0.030, (255, 150, 60)), (0.48, 0.22, 0.020, (255, 190, 90)), (0.7, 0.36, 0.012, (255, 120, 40))]):
        pts = [(s + s * ww * math.cos(a), s - s * hh * math.sin(a) + 4 * math.sin(a * 5 + k)) for a in np.linspace(-0.25, math.pi + 0.25, 100)]
        d.line(pts, fill=c, width=max(2, int(s * wd)), joint="curve")
    img = img.filter(ImageFilter.GaussianBlur(max(2, s * 0.025)))
    return np.asarray(img, np.float32) / 255 * 0.75

# ------------------------------------------------------------------ stars
@functools.lru_cache(None)
def starfield(seed=7, scale=1.5):
    rng = np.random.default_rng(seed)
    Hs, Ws = int(H * scale), int(W * scale)
    a = np.zeros((Hs, Ws, 3), np.float32)
    # faint nebular haze (low frequency noise)
    small = rng.random((Hs // 160 + 2, Ws // 160 + 2, 3)).astype(np.float32)
    neb = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((Ws, Hs), Image.BICUBIC), np.float32) / 255
    neb = np.clip(neb - 0.45, 0, 1) * np.array([0.05, 0.035, 0.09], np.float32)
    a += BG_RGB + neb
    n = int(Hs * Ws / 900)
    ys, xs = rng.integers(0, Hs, n), rng.integers(0, Ws, n)
    mag = rng.random(n) ** 6
    tint = np.stack([0.85 + 0.15 * rng.random(n), 0.88 + 0.1 * rng.random(n), 0.95 + 0.05 * rng.random(n)], 1)
    for (y, x, m, c) in zip(ys, xs, mag, tint):
        b = 0.08 + 0.75 * m
        a[y, x] += c * b
        if m > 0.35:
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < Hs and 0 <= xx < Ws:
                    a[yy, xx] += c * b * 0.3
    return a

def stars(cv, ox, oy, bright=1.0):
    """Copy a subpixel-shifted window of the starfield into cv."""
    sf = starfield()
    Hs, Ws = sf.shape[:2]
    ox = (ox % (Ws - W - 2)); oy = (oy % (Hs - H - 2))
    ix, iy = int(ox), int(oy); fx, fy = ox - ix, oy - iy
    a = (sf[iy:iy + H, ix:ix + W] * (1 - fx) + sf[iy:iy + H, ix + 1:ix + 1 + W] * fx) * (1 - fy) + \
        (sf[iy + 1:iy + 1 + H, ix:ix + W] * (1 - fx) + sf[iy + 1:iy + 1 + H, ix + 1:ix + 1 + W] * fx) * fy
    if bright != 1.0:
        a = BG_RGB + (a - BG_RGB) * bright
    cv.a[:] = a

# ------------------------------------------------------------------ Pluto texture (procedural)
def pluto_tex():
    rng = np.random.default_rng(3)
    h, w = 512, 1024
    base = np.zeros((h, w), np.float32)
    for k, amp in [(8, 0.5), (16, 0.25), (32, 0.15), (64, 0.1)]:
        n = rng.random((k // 2 + 2, k + 2)).astype(np.float32)
        base += amp * np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    v, u = np.mgrid[0:h, 0:w].astype(np.float32)
    lon = (u / w - 0.5) * 360; lat = 90 - v / h * 180
    # heart (Tombaugh Regio) centred near lon 180 -> map at lon 0 here, lat +20
    x = (lon - 0) / 38; y = (lat - 18) / 34
    heart = (x ** 2 + (1.25 * y - np.sqrt(np.abs(x)) * 0.9) ** 2) < 1.0
    hm = np.asarray(Image.fromarray(heart.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    rgb = np.stack([0.55 + 0.25 * base, 0.42 + 0.2 * base, 0.32 + 0.15 * base], -1)
    dark = np.clip((np.abs(lat + 5) < 18) * (np.abs(lon + 70) < 60), 0, 1).astype(np.float32)
    dark = np.asarray(Image.fromarray((dark * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), np.float32)[..., None] / 255
    rgb = rgb * (1 - dark * 0.6) * np.array([1, 0.85, 0.75]) ** dark
    rgb = rgb * (1 - hm[..., None]) + np.array([0.93, 0.88, 0.80]) * hm[..., None]
    return np.clip(rgb, 0, 1).astype(np.float32)

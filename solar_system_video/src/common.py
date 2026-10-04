"""Shared constants, easing, text sprites (HarfBuzz/Raqm-shaped Devanagari),
vector drawing and premultiplied-alpha compositing on float32 frames."""
import functools, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W, H, FPS = 1080, 1920, 30
SS = 2  # supersampling factor for vector graphics

def hexc(h, a=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(round(a * 255)),)

BG = "#050816"; WHITE = "#F5F7FA"; CYAN = "#67DFF2"; GOLD = "#FFBD69"; AMBER = "#FF9A4D"
MUTED = "#9AA7B8"; RED = "#FF6B5E"; BLUE = "#4FA3FF"
BG_RGB = np.array(hexc(BG)[:3], np.float32) / 255

# layout guides (10% sides, 12% top, 20% bottom)
MX, MT, MB = 108, 230, 1536

FONT_DIR = "/usr/share/fonts/truetype/noto"
FONTS = {
    "dev": "NotoSansDevanagari-Regular.ttf", "devb": "NotoSansDevanagari-Bold.ttf",
    "lat": "NotoSans-Regular.ttf", "latb": "NotoSans-Bold.ttf", "disp": "NotoSansDisplay-Bold.ttf",
    "displ": "NotoSansDisplay-Regular.ttf",
}

@functools.lru_cache(None)
def font(kind, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[kind]), size, layout_engine=ImageFont.Layout.RAQM)

def is_dev(s):
    return any("ऀ" <= c <= "ॿ" for c in s)

# ---------------------------------------------------------------- easing
def clamp01(x):
    return max(0.0, min(1.0, x))

def seg(t, a, b):
    return clamp01((t - a) / (b - a)) if b != a else float(t >= a)

def ease(x):
    x = clamp01(x); return x * x * (3 - 2 * x)

def ease_io(x):  # quintic-ish smoother in-out
    x = clamp01(x); return x * x * x * (x * (x * 6 - 15) + 10)

def ease_out(x):
    x = clamp01(x); return 1 - (1 - x) ** 3

def lerp(a, b, x):
    return a + (b - a) * x

def window(t, t_in, t_out, d_in=0.45, d_out=0.45):
    """0→1 fade in at t_in, 1→0 fade out ending at t_out."""
    return ease(seg(t, t_in, t_in + d_in)) * (1 - ease(seg(t, t_out - d_out, t_out)))

# ---------------------------------------------------------------- sprites
FALLBACK = {False: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", True: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}

@functools.lru_cache(None)
def cmap(kind):
    from fontTools.ttLib import TTFont
    return set(TTFont(os.path.join(FONT_DIR, FONTS[kind]), lazy=True).getBestCmap())

@functools.lru_cache(None)
def fb_font(bold, size):
    return ImageFont.truetype(FALLBACK[bold], int(size * 0.92), layout_engine=ImageFont.Layout.RAQM)

def runs(text, kind, size, tracking=0):
    """Split into (string, font, x) runs; glyphs missing from the Noto face use DejaVu."""
    f = font(kind, size); cm = cmap(kind); fb = fb_font(kind in ("devb", "latb", "disp"), size)
    segs, cur, cur_fb = [], "", None
    for ch in text:
        isfb = ord(ch) not in cm and ch != " "
        if tracking and not is_dev(text):
            segs.append((ch, isfb)); continue
        if cur and isfb != cur_fb:
            segs.append((cur, cur_fb)); cur = ""
        cur += ch; cur_fb = isfb
    if cur: segs.append((cur, cur_fb))
    out, x = [], 0.0
    for sgm, isfb in segs:
        ft = fb if isfb else f
        lang = "hi" if is_dev(sgm) else None
        out.append((sgm, ft, x, lang))
        x += ft.getlength(sgm, language=lang) + (tracking if tracking and not is_dev(text) else 0)
    return out, x

@functools.lru_cache(4096)
def text_sprite(text, kind, size, color=WHITE, tracking=0, shadow=True):
    """Premultiplied float32 RGBA of shaped text (Raqm/HarfBuzz) with soft shadow."""
    f = font(kind, size)
    rs, wtot = runs(text, kind, size, tracking)
    asc, desc = f.getmetrics()
    h = asc + desc + 12
    pad = 14 if shadow else 0
    img = Image.new("RGBA", (int(wtot) + 8 + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    def put(dr, fill):
        for sgm, ft, x, lang in rs:
            yoff = (asc - ft.getmetrics()[0]) if ft is not f else 0
            dr.text((pad + 4 + x, pad + 4 + yoff), sgm, font=ft, fill=fill, language=lang)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        put(ImageDraw.Draw(sh), (0, 0, 0, 170))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(5)))
    put(ImageDraw.Draw(img), hexc(color) if isinstance(color, str) else color)
    return premul(img)

def premul(img):
    a = np.asarray(img, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a

@functools.lru_cache(512)
def rrect_sprite(w, h, r, fill=(8, 14, 34, 200), outline=None, ow=2, accent=None, accent_w=8):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=fill,
                        outline=outline, width=ow * SS if outline else 0)
    if accent:
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=255)
        bar = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(bar).rectangle([0, 0, accent_w * SS, h * SS], fill=accent)
        bar.putalpha(Image.fromarray(np.minimum(np.asarray(bar)[..., 3], np.asarray(m))))
        img = Image.alpha_composite(img, bar)
    return premul(img.reduce(SS))

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, arr=None):
        self.a = arr if arr is not None else np.empty((H, W, 3), np.float32)

    def fill(self, rgb):
        self.a[:] = rgb

    def blit(self, spr, x, y, alpha=1.0, anchor="lt", add=False):
        """Composite premultiplied RGBA sprite. anchor: l/c/r + t/m/b."""
        if alpha <= 0.003:
            return
        h, w = spr.shape[:2]
        x = int(round(x - (w / 2 if anchor[0] == "c" else w if anchor[0] == "r" else 0)))
        y = int(round(y - (h / 2 if anchor[1] == "m" else h if anchor[1] == "b" else 0)))
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x0 >= x1 or y0 >= y1:
            return
        s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
        dst = self.a[y0:y1, x0:x1]
        if add:
            dst += s[..., :3] * alpha
        else:
            dst *= 1 - s[..., 3:4] * alpha
            dst += s[..., :3] * alpha

    def text(self, s, x, y, kind=None, size=40, color=WHITE, alpha=1.0, anchor="lt", tracking=0, shadow=True):
        kind = kind or ("dev" if is_dev(s) else "lat")
        spr = text_sprite(s, kind, size, color, tracking, shadow)
        pad = 14 if shadow else 0
        # compensate sprite padding so (x, y) is the visual text box corner
        h, w = spr.shape[:2]
        if anchor[0] == "l": x -= pad + 4
        elif anchor[0] == "r": x += pad
        if anchor[1] == "t": y -= pad + 4
        elif anchor[1] == "b": y += pad
        self.blit(spr, x, y, alpha, anchor)
        return w - 2 * pad - 8

def text_width(s, size, kind=None, tracking=0):
    kind = kind or ("dev" if is_dev(s) else "lat")
    return runs(s, kind, size, tracking)[1]

class Vec:
    """2x supersampled RGBA vector layer covering a region of the frame."""
    def __init__(self, x0=0, y0=0, w=W, h=H):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def P(self, x, y):
        return ((x - self.x0) * SS, (y - self.y0) * SS)

    def line(self, pts, color, width=2, joint="curve"):
        if len(pts) >= 2:
            self.d.line([self.P(*p) for p in pts], fill=color, width=max(1, int(round(width * SS))), joint=joint)

    def poly(self, pts, fill=None, outline=None, width=1):
        self.d.polygon([self.P(*p) for p in pts], fill=fill, outline=outline, width=int(width * SS))

    def circle(self, x, y, r, fill=None, outline=None, width=1):
        X, Y = self.P(x, y)
        self.d.ellipse([X - r * SS, Y - r * SS, X + r * SS, Y + r * SS], fill=fill, outline=outline, width=int(round(width * SS)))

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1, r=0):
        a, b = self.P(x0, y0); c, d = self.P(x1, y1)
        self.d.rounded_rectangle([a, b, c, d], r * SS, fill=fill, outline=outline, width=int(width * SS))

    def arrow(self, p0, p1, color, width=3, head=14):
        self.line([p0, p1], color, width)
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        a1, a2 = ang + 2.6, ang - 2.6
        self.poly([p1, (p1[0] + head * math.cos(a1), p1[1] + head * math.sin(a1)),
                   (p1[0] + head * math.cos(a2), p1[1] + head * math.sin(a2))], fill=color)

    def wave_arrow(self, p0, p1, color, width=3, amp=8, waves=4, head=14, prog=1.0):
        n = 60
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
        pts = []
        for i in range(int(n * prog) + 1):
            s = i / n
            o = amp * math.sin(s * waves * 2 * math.pi) * min(1, (1 - s) * 5)
            pts.append((p0[0] + dx * s + nx * o, p0[1] + dy * s + ny * o))
        self.line(pts, color, width)
        if prog >= 0.98:
            self.arrow(pts[-2], p1, color, width, head)

    def composite(self, cv, alpha=1.0, blur=0):
        if alpha <= 0.003:
            return
        img = self.img.reduce(SS)
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(blur))
        cv.blit(premul(img), self.x0, self.y0, alpha)

def col(h, a=1.0):
    return hexc(h, a)

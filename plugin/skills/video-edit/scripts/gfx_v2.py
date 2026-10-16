# Vlog graphics, style v2 (from Vlog 3): clean editorial lower-thirds, Claude comment bubbles, pop words,
# slide-in tip cards and a tracked-out title. Replaces the v1 terminal look for 16:9 vlogs (shorts keep v1).
# Every generator yields RGBA PIL frames; captions.py writes them to alpha .mov files and places them.
# Static layers (text + soft shadow) are drawn once, then only moved / masked / scaled per frame.
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

from fonts import font
WHITE = (255, 255, 255); INK = (24, 24, 27); ORANGE = (217, 119, 87); ACCENT = (255, 138, 76)

def bahn(px, style="Bold"):
    f = font("bahnschrift.ttf", px)
    try: f.set_variation_by_name(style)
    except Exception: pass
    return f
def segoe(px, w="sb"): return font({"sb": "seguisb.ttf", "b": "segoeuib.ttf", "bl": "seguibl.ttf", "r": "segoeui.ttf"}[w], px)

clamp = lambda x: max(0.0, min(1.0, x))
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3
def ease_back(t, s=1.70158):
    t = clamp(t) - 1; return 1 + (s + 1) * t ** 3 + s * t ** 2

def tw(f, t): b = f.getbbox(t); return b[2] - b[0] if t else 0

def text_layer(text, font, fill=WHITE, shadow=150, blur=10, stroke=0, stroke_fill=(0, 0, 0), tracking=0, pad=40):
    """text (optionally letter-spaced) on a transparent layer with a soft drop shadow"""
    asc, desc = font.getmetrics()
    chars = list(text) if tracking else [text]
    widths = [font.getlength(c) for c in chars]
    w = int(sum(widths) + tracking * max(0, len(chars) - 1)) + 2 * pad + 2 * stroke
    h = asc + desc + 2 * pad + 2 * stroke
    fg = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fg); x = pad + stroke
    for c, cw in zip(chars, widths):
        d.text((x, pad + stroke), c, font=font, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_fill + (255,) if stroke else None)
        x += cw + tracking
    if not shadow: return fg
    a = fg.split()[3]
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: v * shadow // 255))
    sh = ImageChops.offset(sh, 0, 6).filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.alpha_composite(sh); out.alpha_composite(fg)
    return out

def fade(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * max(0.0, a)))); return im

def scaled(base, s, box=None):
    """base scaled by s about its centre, on a canvas of box (default base size)"""
    W, H = box or base.size
    if abs(s - 1) < 1e-3 and (W, H) == base.size: return base
    im = base.resize((max(1, int(base.width * s)), max(1, int(base.height * s))), Image.BICUBIC)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(im, ((W - im.width) // 2, (H - im.height) // 2)) if im.width <= W and im.height <= H else \
        out.paste(im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H)), (0, 0))
    return out

def claude_mark(r, col=ORANGE):
    """Claude-style starburst glyph, radius r"""
    S = 4; R = r * S; im = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(12):
        ang = i * math.pi / 6 + 0.13; L = R * (0.98 if i % 2 == 0 else 0.78); wdt = R * 0.17
        ex, ey = R + math.cos(ang) * L, R + math.sin(ang) * L
        d.line((R, R, ex, ey), fill=col + (255,), width=int(wdt))
        d.ellipse((ex - wdt / 2, ey - wdt / 2, ex + wdt / 2, ey + wdt / 2), fill=col + (255,))
    d.ellipse((R - wdt, R - wdt, R + wdt, R + wdt), fill=col + (255,))
    return im.resize((2 * r, 2 * r), Image.LANCZOS)

# ------------------------------------------------------------------ stamp: section lower-third
def frames_stamp(text, nf, fps):
    t = text.lstrip("\u25cf ").strip()
    time_s, label = ([x.strip() for x in t.split("//", 1)] if "//" in t else ("", t))
    ft, fl = bahn(70, "SemiBold"), bahn(168, "Bold Condensed")
    L_time = text_layer(time_s.upper(), ft, fill=(235, 235, 235), tracking=10, shadow=170, blur=8) if time_s else None
    L_lab = text_layer(label.upper(), fl, shadow=170, blur=12, tracking=2)
    pad = 40; gap = -58
    th = L_time.height if L_time else 0
    W = max(L_lab.width, (L_time.width + 70) if L_time else 0) + 80; H = th + L_lab.height + gap
    bx, bw = pad + 4, 12                     # accent bar
    tx = bx + bw + 6                          # text area starts right of the bar
    top_lab = th + gap if L_time else 0
    bar_top, bar_bot = pad + 26, H - pad - 34
    out_n = int(0.4 * fps)
    for k in range(nf):
        ko = nf - 1 - k                       # frames left
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        bin_ = ease_out(k / 7); bout = ease_in(1 - ko / out_n) if ko < out_n else 0
        bp = bin_ * (1 - bout)
        if bp > 0:
            mid = (bar_top + bar_bot) / 2; hh = (bar_bot - bar_top) / 2 * bp
            d.rounded_rectangle((bx, mid - hh, bx + bw, mid + hh), 6, fill=ACCENT + (255,))
        area = Image.new("RGBA", (W - tx, H), (0, 0, 0, 0))
        for L, y, st in ((L_time, 0, 3), (L_lab, top_lab, 6)):
            if L is None: continue
            p_in = ease_out((k - st) / 11); p_out = ease_in((out_n - ko) / (out_n * 0.8)) if ko < out_n else 0
            off = int(-(1 - p_in) * L.width * 0.9 - p_out * L.width)
            if p_in > 0 and p_out < 1: area.alpha_composite(L, (max(off, -L.width + 1) if off < 0 else off, y)) if off >= 0 else \
                area.alpha_composite(L.crop((-off, 0, L.width, L.height)), (0, y))
        if L_time is not None:   # live REC dot after the time
            ko_ok = ko >= out_n and k > 12
            if ko_ok and (k // int(fps * 0.5)) % 2 == 0:
                cx = L_time.width - 40 + 30; cy = pad + ft.getmetrics()[0] * 0.62
                ImageDraw.Draw(area).ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=(255, 64, 56, 255))
        im.alpha_composite(area, (tx, 0))
        yield im

# ------------------------------------------------------------------ claude: comment bubble
def frames_claude(text, nf, fps):
    t = text[1:].strip() if text.startswith(">") else text.strip()
    f = segoe(76, "sb"); asc, desc = f.getmetrics()
    r = 34; padx, pady = 44, 28; gap = 28
    w_txt = int(f.getlength(t)); bw = padx + 2 * r + gap + w_txt + padx + 6; bh = asc + desc + 2 * pady
    m = 50; W, H = bw + 2 * m, bh + 2 * m
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((m, m + 10, m + bw, m + bh + 10), bh // 2, fill=(0, 0, 0, 120))
    bub.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(bub).rounded_rectangle((m, m, m + bw, m + bh), bh // 2, fill=(250, 248, 244, 246))
    bub.alpha_composite(claude_mark(r), (m + padx, m + (bh - 2 * r) // 2))
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x0 = m + padx + 2 * r + gap
    ImageDraw.Draw(txt).text((x0, m + pady - 4), t, font=f, fill=INK + (255,))
    reveal = max(6, min(int(0.6 * fps), len(t)))
    soft = 90
    for k in range(nf):
        ko = nf - 1 - k
        s = 0.55 + 0.45 * ease_back(k / 9, 2.2)
        if ko < 6: s *= 1 - 0.08 * (1 - ko / 6)
        a = clamp((k + 1) / 4) * (clamp(ko / 6) if ko < 6 else 1)
        # soft left-to-right wipe reveals the words
        edge = x0 + (w_txt + soft) * ease_out((k - 3) / reveal)
        mask = Image.linear_gradient("L").rotate(90).resize((soft, H))   # 255 -> 0 left to right
        ml = Image.new("L", (W, H), 0); ml.paste(255, (0, 0, max(0, int(edge - soft)), H)); ml.paste(mask, (int(edge - soft), 0))
        tt = txt.copy(); tt.putalpha(ImageChops.multiply(tt.split()[3], ml))
        fr = bub.copy(); fr.alpha_composite(tt)
        yield fade(scaled(fr, s), a)

# ------------------------------------------------------------------ cap: bold on-screen text
def frames_cap(text, nf, fps):
    t = text[1:].strip() if text.startswith(">") else text.strip()
    L = text_layer(t, bahn(118, "Bold"), stroke=7, stroke_fill=(10, 10, 12), shadow=160, blur=12)
    for k in range(nf):
        ko = nf - 1 - k
        s = 0.7 + 0.3 * ease_back(k / 8, 2.4)
        a = clamp((k + 1) / 3) * (clamp(ko / 6) if ko < 6 else 1)
        yield fade(scaled(L, s), a)

# ------------------------------------------------------------------ pop: comedic punch word
def frames_pop(text, nf, fps):
    L = text_layer(text.upper(), bahn(250, "Bold Condensed"), fill=(255, 255, 255), stroke=14, stroke_fill=(12, 12, 14), shadow=180, blur=14)
    L = L.rotate(-5, resample=Image.BICUBIC, expand=True)
    W, H = int(L.width * 1.2), int(L.height * 1.2)
    for k in range(nf):
        ko = nf - 1 - k
        s = 1.0 + 0.9 * (1 - ease_out(k / 5))
        if ko < 5: s *= 1 + 0.25 * (1 - ko / 5)
        a = clamp((k + 1) / 2) * (clamp(ko / 5) if ko < 5 else 1)
        fr = scaled(L, s, (W, H))
        if 4 <= k < 12:   # small impact shake
            dx, dy = int(10 * math.sin(k * 2.7)), int(8 * math.cos(k * 3.3))
            fr = ImageChops.offset(fr, dx, dy)
        yield fade(fr, a)

# ------------------------------------------------------------------ card: tip / list card
def frames_card(text, nf, fps):
    lines = text.split("|"); title, body = lines[0], lines[1:]
    title = title.rsplit(".", 1)[0].replace("_", " ").upper() if "." in title[-5:] else title.upper()
    fh, fa, fb = segoe(50, "b"), segoe(64, "b"), segoe(64, "sb")
    rows = []
    for l in body:
        parts = [p for p in l.split("  ") if p.strip()]
        rows.append((parts[0].strip(), "  ".join(p.strip() for p in parts[1:])) if len(parts) > 1 else ("", l.strip()))
    colw = max([fa.getlength(a) for a, _ in rows] + [0]); colw = colw + 60 if colw else 0
    asc, desc = fb.getmetrics(); lh = asc + desc + 22
    inner = max([colw + fb.getlength(b) for _, b in rows] + [fh.getlength(title) * 1.15])
    padx = 70; W = int(inner + 2 * padx + 30); hdr = 120; H = hdr + lh * len(rows) + 50
    m = 50; CW_, CH_ = W + 2 * m, H + 2 * m
    bg = Image.new("RGBA", (CW_, CH_), (0, 0, 0, 0))
    sh = Image.new("RGBA", (CW_, CH_), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((m, m + 12, m + W, m + H + 12), 34, fill=(0, 0, 0, 140))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(bg); d.rounded_rectangle((m, m, m + W, m + H), 34, fill=(17, 17, 20, 222))
    d.rounded_rectangle((m, m, m + 14, m + H), 7, fill=ACCENT + (255,))
    bg.alpha_composite(claude_mark(22), (m + padx, m + 42))
    x = m + padx + 64
    for c in title: d.text((x, m + 38), c, font=fh, fill=(205, 205, 210, 255)); x += fh.getlength(c) + 6
    d.line((m + padx, m + hdr - 6, m + W - padx, m + hdr - 6), fill=(255, 255, 255, 40), width=3)
    row_l = []
    for i, (a_, b_) in enumerate(rows):
        L = Image.new("RGBA", (W, lh + 10), (0, 0, 0, 0)); dd = ImageDraw.Draw(L)
        last = i == len(rows) - 1
        if a_: dd.text((padx, 0), a_, font=fa, fill=ACCENT + (255,))
        dd.text((padx + colw, 0), b_, font=fb, fill=(ACCENT if last and not a_ else WHITE) + (255,))
        row_l.append(L)
    per = max(4, int(0.28 * fps))
    for k in range(nf):
        ko = nf - 1 - k
        p = ease_out(k / 12); po = ease_in((8 - ko) / 8) if ko < 8 else 0
        fr = bg.copy()
        for i, L in enumerate(row_l):
            q = ease_out((k - 8 - i * per) / 8)
            if q <= 0: break
            fr.alpha_composite(fade(L, q), (m, m + hdr + 20 + i * lh + int(24 * (1 - q))))
        dx = int(-(1 - p) * 260 - po * 200)
        out = Image.new("RGBA", fr.size, (0, 0, 0, 0)); out.alpha_composite(fr, (0, 0))
        out = ImageChops.offset(out, dx, 0) if dx else out
        if dx < 0: ImageDraw.Draw(out).rectangle((out.width + dx, 0, out.width, out.height), fill=(0, 0, 0, 0))
        yield fade(out, clamp(p * 1.4) * (1 - po))

# ------------------------------------------------------------------ big: title with tracking-in
def frames_big(text, nf, fps):
    f = bahn(330, "Bold"); chars = list(text.upper()); asc, desc = f.getmetrics()
    widths = [f.getlength(c) for c in chars]
    tr0, tr1 = 150, 26
    W = int(sum(widths) + tr0 * (len(chars) - 1)) + 200; H = asc + desc + 220
    for k in range(nf):
        ko = nf - 1 - k
        p = ease_out(k / int(1.1 * fps)); tr = tr0 + (tr1 - tr0) * p
        if ko < 10: tr += 40 * ease_in(1 - ko / 10)
        fg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fg)
        tot = sum(widths) + tr * (len(chars) - 1); x = (W - tot) / 2
        for i, (c, cw) in enumerate(zip(chars, widths)):
            a = clamp((k - i * 1.5) / 6)
            if a > 0: d.text((x, 70), c, font=f, fill=(255, 255, 255, int(255 * a)))
            x += cw + tr
        ul = ease_out((k - 10) / 12)    # accent line grows from the centre
        if ul > 0:
            lw = (tot * 0.32) * ul; y = 70 + asc + desc + 24
            d.rounded_rectangle((W / 2 - lw, y, W / 2 + lw, y + 12), 6, fill=ACCENT + (255,))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(fg.split()[3].point(lambda v: v * 200 // 255))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(ImageChops.offset(sh, 0, 10).filter(ImageFilter.GaussianBlur(18))); out.alpha_composite(fg)
        yield fade(out, clamp(ko / 10) if ko < 10 else 1)

# ------------------------------------------------------------------ sub: title subline
def frames_sub(text, nf, fps):
    t = text[1:].strip() if text.startswith(">") else text.strip()
    t = "   \u2022   ".join(p.strip() for p in t.split("//")).upper()
    T = text_layer(t, segoe(70, "sb"), fill=(245, 245, 245), tracking=9, shadow=230, blur=6)
    L = Image.new("RGBA", (T.width + 160, T.height + 40), (0, 0, 0, 0))     # soft dark band keeps it legible on bright shots
    band = Image.new("RGBA", L.size, (0, 0, 0, 0)); ImageDraw.Draw(band).rounded_rectangle((60, 40, L.width - 60, L.height - 40), 60, fill=(0, 0, 0, 120))
    L.alpha_composite(band.filter(ImageFilter.GaussianBlur(30))); L.alpha_composite(T, (80, 20))
    delay = int(0.55 * fps)
    for k in range(nf):
        ko = nf - 1 - k
        q = ease_out((k - delay) / 12)
        a = q * (clamp(ko / 10) if ko < 10 else 1)
        out = Image.new("RGBA", (L.width, L.height + 40), (0, 0, 0, 0))
        if a > 0: out.alpha_composite(fade(L, a), (0, int(40 * (1 - q))))
        yield out

GEN = {"stamp": frames_stamp, "claude": frames_claude, "cap": frames_cap, "pop": frames_pop, "card": frames_card,
       "big": frames_big, "sub": frames_sub}

def place(kind, w, h, lane, CW=3840, text=""):
    """top-left position on the 3840x2160 canvas; lane stacks overlapping bottom captions"""
    if kind == "stamp": return 120, 2010 - h
    if kind == "claude": return (CW - w) // 2, 1990 - h - lane * 250
    if kind == "cap": return (CW - w) // 2, 1940 - h - lane * 250
    if kind == "pop": return int(CW * 0.64 - w / 2), 200
    if kind == "card": return 90, 110
    if kind == "big": return (CW - w) // 2, 1080 - h + 120
    if kind == "sub": return (CW - w) // 2, 1150
    return (CW - w) // 2, 120

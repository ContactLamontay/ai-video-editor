# Renders caption overlays as small alpha clips (QuickTime Animation) laid out on a 3840x2160 canvas.
# master.py burns them in (scaled /3 for the 720p preview). Landscape style: terminal stamps,
# orange "> claude" cameos with typewriter + cursor, terminal-window cards, big Bahnschrift title.
#   python captions.py   -> CACHE/caps/cNN.mov + WORK/caps.json
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont
from common import WORK, CACHE, FPS, FPS_STR, SHORT, FW as CW, FH as CH
import gfx_v2
V2 = not SHORT and os.environ.get("CAPSTYLE", "v2") == "v2"   # vlogs use the v2 look (Vlog 3+); CAPSTYLE=v1 for the old terminal look
SM = CACHE + "/caps"; os.makedirs(SM, exist_ok=True)
P = json.load(open(WORK + "/plan.json"))
from fonts import font
MONO_PX = 50 if SHORT else 74                     # canvas is 1080x1920 for shorts, 3840x2160 for vlogs
mono = font("consolab.ttf", MONO_PX)
mono_s = font("consolab.ttf", 42 if SHORT else 64)
big = font("bahnschrift.ttf", 170 if SHORT else 340)
try: big.set_variation_by_name("Bold")
except Exception: pass
WHITE = (245, 245, 245, 255); ORANGE = (236, 132, 64, 255); RED = (255, 70, 60, 255); DIM = (150, 150, 150, 255)
BOX = (12, 12, 14, 200)

def text_w(f, t): return f.getbbox(t)[2] if t else 0

def frames_bar(text, kind, nf):
    """terminal bar caption with typewriter + cursor"""
    col = ORANGE if kind == "claude" else WHITE
    mono, px = globals()["mono"], MONO_PX
    while px > 24 and text_w(mono, text) + 108 > CW * 0.92:     # shrink long lines to fit the frame
        px -= 2; mono = font("consolab.ttf", px)
    pad_x, pad_y = (24, 14) if SHORT else (34, 20)
    tw = text_w(mono, text); asc, desc = mono.getmetrics(); th = asc + desc
    w, h = tw + pad_x * 2 + 40, th + pad_y * 2
    type_frames = max(4, min(int(0.55 * FPS), len(text)))
    for k in range(nf):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        a = min(1.0, (nf - 1 - k) / 5) if k > nf - 6 else 1.0
        pop = min(1.0, (k + 1) / 3)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 12, fill=BOX[:3] + (int(BOX[3] * a * pop),))
        nchar = len(text) if kind == "stamp" and k >= 3 else int(len(text) * min(1, k / type_frames))
        shown = text[:nchar]
        x = pad_x
        if kind == "stamp" and shown.startswith("\u25cf"):
            on = (k // 15) % 2 == 0
            d.text((x, pad_y), "\u25cf", font=mono, fill=RED[:3] + (int(255 * a * (1 if on else 0.35)),))
            x += text_w(mono, "\u25cf"); shown = shown[1:]
        d.text((x, pad_y), shown, font=mono, fill=col[:3] + (int(255 * a),))
        if kind == "claude" and ((k // 8) % 2 == 0 or nchar < len(text)):
            cx = x + text_w(mono, shown) + 6
            d.rectangle((cx, pad_y + 8, cx + 30, pad_y + asc), fill=col[:3] + (int(220 * a),))
        yield im

def frames_card(text, nf):
    lines = text.split("|"); title, body = lines[0], lines[1:]
    asc, desc = mono_s.getmetrics(); lh = asc + desc + 14
    w = max(text_w(mono_s, l) for l in body + [title]) + 140
    bar = 70; h = bar + 30 + lh * len(body) + 30
    per = max(3, int(0.45 * FPS))
    for k in range(nf):
        a = min(1.0, (nf - 1 - k) / 5) if k > nf - 6 else 1.0
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 18, fill=(14, 14, 16, int(215 * a)))
        d.rounded_rectangle((0, 0, w - 1, bar), 18, fill=(40, 40, 44, int(235 * a)))
        d.rectangle((0, bar - 18, w - 1, bar), fill=(40, 40, 44, int(235 * a)))
        for j, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse((26 + j * 44, 22, 52 + j * 44, 48), fill=c + (int(255 * a),))
        d.text((170, 10), title, font=mono_s, fill=DIM[:3] + (int(255 * a),))
        for i, l in enumerate(body):
            st = 4 + i * per
            if k < st: break
            n = int(len(l) * min(1, (k - st) / max(1, per - 2)))
            d.text((60, bar + 30 + i * lh), l[:n], font=mono_s, fill=(ORANGE if i == len(body) - 1 else WHITE)[:3] + (int(255 * a),))
        yield im

def frames_big(text, nf):
    big, px = globals()["big"], 170 if SHORT else 340
    while px > 60 and big.getbbox(text)[2] + 60 > CW * 0.94:
        px -= 6; big = font("bahnschrift.ttf", px)
        try: big.set_variation_by_name("Bold")
        except Exception: pass
    bb = big.getbbox(text); w, h = bb[2] + 60, bb[3] + 80
    for k in range(nf):
        a = min(1.0, (nf - 1 - k) / 6) if k > nf - 7 else 1.0
        s = 1.0 + 0.18 * max(0, 1 - k / 5) ** 2
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((38, 52), text, font=big, fill=(0, 0, 0, int(140 * a)))
        d.text((30, 40), text, font=big, fill=(255, 255, 255, int(255 * a)))
        if s != 1.0:
            sw, sh = int(w * s), int(h * s)
            im2 = im.resize((sw, sh), Image.LANCZOS); im = im2.crop(((sw - w) // 2, (sh - h) // 2, (sw - w) // 2 + w, (sh - h) // 2 + h))
        yield im

def frames_chip(text, nf):
    """flow pills 'A > B > C', revealed left to right (reference-creator style context graphics)"""
    items = [t.strip() for t in text.split(">")]
    f = font("seguisb.ttf", 38 if SHORT else 64)
    pad, gap, arrow = (22, 14, 44) if SHORT else (36, 22, 70)
    ws = [text_w(f, t) + 2 * pad for t in items]; asc, desc = f.getmetrics(); h = asc + desc + 2 * pad - 8
    W_ = sum(ws) + (len(items) - 1) * (arrow + 2 * gap) + 8
    if W_ > CW * 0.94:   # too wide: stack vertically is ugly, so shrink instead
        k = CW * 0.94 / W_; f = font("seguisb.ttf", int((38 if SHORT else 64) * k))
        ws = [text_w(f, t) + 2 * pad for t in items]; asc, desc = f.getmetrics(); h = asc + desc + 2 * pad - 8
        W_ = sum(ws) + (len(items) - 1) * (arrow + 2 * gap) + 8
    step = max(4, int(0.35 * FPS))
    for k in range(nf):
        a = min(1.0, (nf - 1 - k) / 5) if k > nf - 6 else 1.0
        im = Image.new("RGBA", (W_, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
        for i, (t, w) in enumerate(zip(items, ws)):
            p = min(1.0, max(0.0, (k - i * step) / 4))
            if p <= 0: break
            al = int(255 * a * p)
            d.rounded_rectangle((x, 4, x + w, 4 + h), h // 2, fill=(20, 22, 28, int(al * 0.85)), outline=(255, 255, 255, int(al * 0.25)), width=2)
            d.text((x + pad, 4 + pad - 6), t, font=f, fill=(255, 255, 255, al))
            x += w
            if i + 1 < len(items) and k >= (i + 1) * step:
                d.text((x + gap, 4 + pad - 8), "→", font=f, fill=(255, 255, 255, int(200 * a)))
            x += arrow + 2 * gap
        yield im

def frames_img(path, nf):
    """screenshot / UI card (chat window, profile, app screen): rounded, shadowed, pops in"""
    src = Image.open(path).convert("RGBA"); maxw = int(CW * (0.84 if SHORT else 0.4)); maxh = int(CH * (0.3 if SHORT else 0.45))
    k_ = min(maxw / src.width, maxh / src.height); src = src.resize((int(src.width * k_), int(src.height * k_)), Image.LANCZOS)
    r = 26 if SHORT else 40; mask = Image.new("L", src.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, *src.size), r, fill=255)
    card = Image.new("RGBA", src.size, (0, 0, 0, 0)); card.paste(src, (0, 0), mask)
    m = 30; base = Image.new("RGBA", (src.width + 2 * m, src.height + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + src.width, m + src.height + 8), r, fill=(0, 0, 0, 150))
    from PIL import ImageFilter
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14))); base.alpha_composite(card, (m, m))
    for k in range(nf):
        a = min(1.0, (nf - 1 - k) / 5) if k > nf - 6 else min(1.0, (k + 1) / 4)
        s_ = 0.92 + 0.08 * min(1.0, (k + 1) / 5)
        im = base.resize((int(base.width * s_), int(base.height * s_)), Image.LANCZOS)
        out = Image.new("RGBA", base.size, (0, 0, 0, 0)); out.alpha_composite(im, ((base.width - im.width) // 2, (base.height - im.height) // 2))
        if a < 1: out.putalpha(out.split()[3].point(lambda v: int(v * a)))
        yield out

def place(kind, w, h, lane):
    if SHORT:   # top safe zone, clear of the word captions in the lower third and the platform UI
        if kind == "big": return (CW - w) // 2, 250
        if kind == "sub": return (CW - w) // 2, 250 + 200
        if kind == "card": return (CW - w) // 2, 330
        if kind in ("chip", "img"): return (CW - w) // 2, 200
        if kind == "stamp": return 60, 300 + lane * 110
        return (CW - w) // 2, 330 + lane * 110
    if kind in ("chip", "img"): return (CW - w) // 2, 120
    if kind == "stamp": return 170, 1990 - h - lane * 150
    if kind == "card": return 170, 170
    if kind == "big": return (3840 - w) // 2, 1080 - h + 60
    if kind == "sub": return (3840 - w) // 2, 1190
    return (3840 - w) // 2, 1990 - h - lane * 150

caps = [e for e in P["events"] if e["type"] == "cap"]
# lanes so overlapping bottom captions stack
busy = []
meta = []
for i, e in enumerate(caps):
    t0, t1 = e["tl"], e["tl"] + e["dur"]
    lane = 0
    if e["kind"] in ("stamp", "cap", "claude"):
        while any(b0 < t1 and t0 < b1 and l == lane for b0, b1, l in busy): lane += 1
        busy.append((t0, t1, lane))
    nf = int(round(e["dur"] * FPS))
    k_ = e["kind"]
    if V2 and k_ in gfx_v2.GEN:
        gen = gfx_v2.GEN[k_](e["text"], nf, FPS); first = next(gen); w, h = first.size; x, y = gfx_v2.place(k_, w, h, lane, CW, e["text"])
    else:
        gen = None
    if gen is None:
      gen = (frames_big(e["text"], nf) if k_ == "big" else frames_card(e["text"], nf) if k_ == "card" else
           frames_chip(e["text"], nf) if k_ == "chip" else frames_img(e["text"], nf) if k_ == "img" else
           frames_bar(e["text"], "claude" if k_ == "sub" else k_, nf))
      first = next(gen); w, h = first.size; x, y = place(e["kind"], w, h, lane)
    small = os.path.join(SM, f"c{i:02d}.mov")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", FPS_STR,
                          "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", small], stdin=subprocess.PIPE)
    p.stdin.write(first.tobytes())
    for im in gen: p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    meta.append(dict(i=i, tl=t0, nf=nf, x=x, y=y, small=small, text=e["text"], kind=e["kind"]))
    print(i, e["kind"], round(t0, 2), e["text"][:40], flush=True)
json.dump(meta, open(WORK + "/caps.json", "w"), indent=1)

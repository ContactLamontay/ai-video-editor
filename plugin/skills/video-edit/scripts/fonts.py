# Font lookup that works on Windows and Mac. Scripts ask for the Windows file name they were designed with
# ("seguisb.ttf"); on a Mac the closest built-in font is used instead. Brand fonts dropped into
# ~/.ai-video-editor/fonts/ win over everything (same file name, or set FONT_<NAME> in config).
import os
from PIL import ImageFont

HOME = os.path.expanduser("~")
DIRS = [os.path.join(HOME, ".ai-video-editor", "fonts"),
        "C:/Windows/Fonts", os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft/Windows/Fonts"),
        "/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts", os.path.join(HOME, "Library/Fonts")]
MAC = {
    "consolab.ttf": ["Menlo.ttc", "Courier New Bold.ttf"],
    "bahnschrift.ttf": ["DIN Condensed Bold.ttf", "Avenir Next Condensed.ttc", "Arial Narrow Bold.ttf", "HelveticaNeue.ttc"],
    "seguisb.ttf": ["Avenir Next.ttc", "HelveticaNeue.ttc", "Arial Bold.ttf"],
    "segoeuib.ttf": ["Avenir Next.ttc", "HelveticaNeue.ttc", "Arial Bold.ttf"],
    "seguibl.ttf": ["Avenir Next.ttc", "Arial Black.ttf", "Arial Bold.ttf"],
    "segoeui.ttf": ["Avenir Next.ttc", "HelveticaNeue.ttc", "Arial.ttf"],
    "arialbd.ttf": ["Arial Bold.ttf", "Arial.ttf", "Helvetica.ttc"],
}
_cache = {}

def path(name):
    if name not in _cache:
        hit = None
        for n in [name] + MAC.get(name, []):
            hit = next((os.path.join(d, n) for d in DIRS if d and os.path.exists(os.path.join(d, n))), None)
            if hit: break
        _cache[name] = hit
    return _cache[name]

def font(name, px):
    p = path(name)
    return ImageFont.truetype(p, px) if p else ImageFont.load_default(px)

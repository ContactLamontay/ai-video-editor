# Shared paths/settings for the edit scripts. Per-editor settings come from ~/.ai-video-editor/config.json
# (written by the setup script); env vars of the same name in upper case override them.
#   VLOG_DIR    the edit's project folder, e.g. ~/Video Edits/Product UGC 01 (required). The clips for this
#               edit are copied into it from the footage library.
#   FORMAT      "short" (9:16 Reels/TikTok/Shorts) or "vlog" (16:9 landscape YouTube). prep.py stores it in
#               Edit/_work/meta.json, so later steps don't need it again.
#   SRC_DIR     footage folder when it differs from VLOG_DIR (e.g. a second cut from the same shoot)
#   PREVIEW=1   small preview render (the default way to show an edit)
#   config.json keys: footage_dir, projects_dir, output_dir, music_dir, sfx_dir, brand_file, elevenlabs_api_key
# Small working files (transcripts, plan) live in <VLOG_DIR>/Edit/_work. Heavy renders live in a local cache
# (%LOCALAPPDATA%/ai-video-editor/... or ~/ai-video-editor-cache/...).
import os, glob, json, re, hashlib
from fractions import Fraction

CFG_DIR = os.path.join(os.path.expanduser("~"), ".ai-video-editor")
CFG_F = os.path.join(CFG_DIR, "config.json")
CFG = json.load(open(CFG_F, encoding="utf-8-sig")) if os.path.exists(CFG_F) else {}

def setting(key, default=""):
    v = os.environ.get(key.upper()) or CFG.get(key) or default
    return v.replace("\\", "/").rstrip("/")

HOME = os.path.expanduser("~").replace("\\", "/")
PROJECTS = setting("projects_dir", HOME + "/Video Edits")
FOOTAGE = setting("footage_dir")
MUSIC = setting("music_dir", PROJECTS + "/Music") + "/"
SFX = setting("sfx_dir", PROJECTS + "/Sound FX") + "/"
OUTPUT_CHOSEN = bool(setting("output_dir")) and os.path.isdir(setting("output_dir"))   # asked on the first video
FINISHED = setting("output_dir", PROJECTS + "/Finished")
BRAND = setting("brand_file")

VLOG = os.environ["VLOG_DIR"].replace("\\", "/").rstrip("/")
NAME = os.path.basename(VLOG)                      # e.g. "Product UGC 01"
ED = VLOG + "/Edit"
WORK = ED + "/_work"
_cache_root = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "ai-video-editor-cache")
CACHE = (_cache_root.replace("\\", "/") + "/ai-video-editor/"
         + re.sub(r"[^A-Za-z0-9]+", "_", NAME) + "_" + hashlib.md5(VLOG.lower().encode()).hexdigest()[:6])
PREVIEW = os.environ.get("PREVIEW") == "1"
for d in (ED, WORK, CACHE): os.makedirs(d, exist_ok=True)

META_F = WORK + "/meta.json"
META = json.load(open(META_F)) if os.path.exists(META_F) else {}
FORMAT = os.environ.get("FORMAT") or META.get("format", "short")
FPS_STR = META.get("fps", "30000/1001")           # footage frame rate, e.g. "30000/1001", "24/1", "30/1"
FPS = float(Fraction(FPS_STR))
SHORT = FORMAT == "short"
# raw_audio: true in meta.json (or RAW_AUDIO=1) passes the camera audio through untouched - no denoise, EQ,
# compression or loudness normalisation. Use when the source audio is already mixed (e.g. a creator's own UGC).
RAW_AUDIO = os.environ.get("RAW_AUDIO") == "1" or bool(META.get("raw_audio"))
FW, FH = (1080, 1920) if SHORT else (3840, 2160)   # final size
PW, PH = (540, 960) if SHORT else (1280, 720)      # preview size
RW, RH = (PW, PH) if PREVIEW else (FW, FH)         # size for this run
TAG = ("p" if PREVIEW else "f") + ("_short" if SHORT else "")

VIDEO_EXT = (".mp4", ".mov", ".mxf", ".mkv", ".m4v")

def clip_key(path):
    """DJI_20261014080240_0001_D.MP4 -> '0001'; A001_06182306_C046.mov (Blackmagic Camera) -> 'C046'; else file stem"""
    stem = os.path.splitext(os.path.basename(path))[0]; parts = stem.split("_")
    if stem.startswith("DJI_") and len(parts) >= 3: return parts[2]
    if re.fullmatch(r"[A-Z]\d{3}_\d{8}_C\d{3}", stem): return parts[2]
    return stem

SRC = os.environ.get("SRC_DIR", VLOG).replace("\\", "/").rstrip("/")   # footage folder if it differs from VLOG_DIR

def clips():
    """{key: {'mp4': main file|None, 'lrf': DJI low-res copy|None}} for every recording directly in SRC_DIR (default VLOG_DIR)"""
    out = {}
    for p in sorted(glob.glob(SRC + "/*")):
        ext = os.path.splitext(p)[1].lower()
        if ext == ".lrf": out.setdefault(clip_key(p), {"mp4": None, "lrf": None})["lrf"] = p
        elif ext in VIDEO_EXT: out.setdefault(clip_key(p), {"mp4": None, "lrf": None})["mp4"] = p
    return dict(sorted(out.items()))

def src_video(key, preview=PREVIEW):
    c = clips()[key]
    return (c["lrf"] or c["mp4"]) if preview else (c["mp4"] or c["lrf"])

def src_audio(key):
    c = clips()[key]
    return c["mp4"] or c["lrf"]

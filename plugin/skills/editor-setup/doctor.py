# Checks that this computer is ready for the AI video editor. Prints one line per check and exits 1 if anything
# required is missing. Never prints the API key.   python doctor.py [--quiet]
import json, os, shutil, subprocess, sys
_BIN = os.path.join(os.path.expanduser("~"), ".ai-video-editor", "bin")   # Mac setup puts ffmpeg/python here
if os.path.isdir(_BIN) and _BIN not in os.environ.get("PATH", "").split(os.pathsep):
    os.environ["PATH"] = _BIN + os.pathsep + os.environ.get("PATH", "")

CFG_F = os.path.join(os.path.expanduser("~"), ".ai-video-editor", "config.json")
ok_all = True
quiet = "--quiet" in sys.argv

def line(ok, what, fix="", required=True):
    global ok_all
    if not ok and required: ok_all = False
    if quiet and ok: return
    mark = "OK  " if ok else ("FAIL" if required else "WARN")
    print(f"[{mark}] {what}" + (f"  ->  {fix}" if not ok and fix else ""))

line(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "install Python 3.10+")
for exe in ("ffmpeg", "ffprobe"):
    line(bool(shutil.which(exe)), exe, "re-run the setup script")
for mod, req in (("PIL", True), ("numpy", True), ("rembg", False)):
    try: __import__(mod); ok = True
    except Exception: ok = False
    line(ok, f"python package {mod}" + ("" if req else " (auto-framing for 9:16; optional)"), "re-run the setup script", req)

cfg = {}
if os.path.exists(CFG_F):
    try: cfg = json.load(open(CFG_F, encoding="utf-8-sig"))
    except ValueError: line(False, "config file readable", f"delete {CFG_F} and re-run setup")
line(bool(cfg), f"config {CFG_F}", "run the setup script")
if cfg:
    line(bool(cfg.get("elevenlabs_api_key") or os.environ.get("ELEVENLABS_API_KEY")), "ElevenLabs key set", "re-run setup and paste the key")
    fd = cfg.get("footage_dir", "")
    line(bool(fd) and os.path.isdir(fd), f"footage library {fd or '(not set)'}",
         "install Google Drive for Desktop, sign in with the company account, then re-run setup")
    p = cfg.get("projects_dir", ""); line(bool(p) and os.path.isdir(p), f"projects_dir {p or '(not set)'}", "re-run setup")
    p = cfg.get("output_dir", "")
    line(bool(p) and os.path.isdir(p), f"finished videos folder {p or '(not chosen yet)'}",
         "the AI asks where finished videos should go on the first video" if not p else "folder is missing - the AI asks again on the next video", False)
    bf = cfg.get("brand_file", "")
    line(bool(bf) and os.path.isfile(bf), f"brand rules {bf or '(not set)'}", "re-run setup and point it at the brand.md you were given", False)
    for k in ("music_dir", "sfx_dir"):
        p = cfg.get(k, ""); line(bool(p) and os.path.isdir(p), f"{k} {p or '(not set)'}", "set it in setup to use music/SFX", False)

if shutil.which("ffmpeg"):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video-edit", "scripts"))
    try:
        import enc; line(True, f"video encoder: {enc.name()}")
    except Exception as e:
        line(False, f"video encoder check ({e})", required=False)

print("READY" if ok_all else "NOT READY - fix the FAIL lines above")
sys.exit(0 if ok_all else 1)

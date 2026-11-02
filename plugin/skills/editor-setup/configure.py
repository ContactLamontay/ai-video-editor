# Writes ~/.ai-video-editor/config.json. Needs nothing typed except, once, the NAME of the footage folder.
#
# Footage folder (first match wins):
#   --footage "<name or path>"  e.g. --footage "Bracelet": searched for by name in Google Drive (My Drive + shared
#                               drives, up to 5 folders deep); a full path works too
#   "footage_dir" in the settings file (relative to the brand.md folder, or absolute)
#   the folder above an "AI video editor" folder holding brand.md in Google Drive, or the folder holding brand.md
#   the previous setting
# Brand rules + key: brand.md and ai-video-editor.json, found in (first match wins)
#   ~/Downloads, ~/Desktop, ~/Documents   e.g. saved from an email - copied into ~/.ai-video-editor/ so the copy in
#                                         Downloads can be deleted; a newer download replaces the stored copy
#   Google Drive (searched for brand.md, see above)
#   ~/.ai-video-editor/ (stored copy from an earlier run)
# ai-video-editor.json: {"elevenlabs_api_key": "...", "music_dir": "Music", "sfx_dir": "Sound FX", "output_dir": "..."}
#   (folders relative to the footage folder, or absolute). Without output_dir, the AI asks where finished videos go
#   the first time the user makes a video.
#
#   python configure.py [--footage NAME]          asks, with everything it found filled in as defaults
#   python configure.py --auto [--footage NAME]   asks nothing - for the AI. Prints "NEED: <what>" lines and exits 2
#                                                 when something only the user can provide is missing.
#   --local                                       no Google Drive: footage is a folder on this computer (a full
#                                                 path, or a name found in Videos / Movies / Desktop / Documents /
#                                                 Downloads / Pictures). Remembered in the config; --drive switches back.
#                                                 With no brand.md, a blank one is made for the user to fill in.
#   --drive-root <dir>                            search this folder instead of Google Drive (repeatable; testing)
import getpass, glob, json, os, re, shutil, string, sys

HOME = os.path.expanduser("~")
CFG_DIR = os.path.join(HOME, ".ai-video-editor"); CFG_F = os.path.join(CFG_DIR, "config.json")
BRAND, SETTINGS = "brand.md", "ai-video-editor.json"
MAX_DEPTH, MAX_DIRS = 6, 40000
KIT_NAME = re.compile(r"^ai[\s_-]*video[\s_-]*editor\b", re.I)   # "AI video editor", "AI-Video-Editor files", ...
args = sys.argv[1:]
AUTO = "--auto" in args
def arg(name): return next((args[i + 1] for i, a in enumerate(args) if a == name and i + 1 < len(args)), "")
FORCED = [args[i + 1] for i, a in enumerate(args) if a == "--drive-root" and i + 1 < len(args)]
WANT = arg("--footage").strip().strip('"')
BLOCKED = []   # folders macOS wouldn't let us read (privacy permission)
HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIRS = ("Videos", "Movies", "Desktop", "Documents", "Downloads", "Pictures")

# Google Drive's own folder names depend on the computer's language ("My Drive" / "Mijn Drive" / "Meine Ablage"...)
MY_NAMES = {"my drive", "mijn drive", "meine ablage", "mon drive", "mi unidad", "il mio drive", "meu drive", "min enhet",
            "mitt drev", "min drev", "oma drive", "mój dysk"}
SHARED_NAMES = {"shared drives", "gedeelde drives", "geteilte ablagen", "drive partagés", "unidades compartidas",
                "drive condivisi", "drives compartilhados", "delade enheter", "delte drev", "jaetut drivet", "dyski współdzielone"}
MOUNTS = []

def win_label(letter):
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(261)
        ok = ctypes.windll.kernel32.GetVolumeInformationW(f"{letter}:\\", buf, 261, None, None, None, None, 0)
        return buf.value if ok else ""
    except Exception:
        return ""

def drive_roots():
    """top-level folders of Google Drive for Desktop (My Drive, the shared drives folder, ...) in any language"""
    if FORCED: return FORCED
    mounts = []
    if os.name == "nt":
        for d in string.ascii_uppercase:
            root = f"{d}:\\"
            if not os.path.isdir(root): continue
            try: names = {n.casefold() for n in os.listdir(root)}
            except OSError: continue
            if names & (MY_NAMES | SHARED_NAMES) or win_label(d).casefold() == "google drive": mounts.append(root)
    else:
        cs = os.path.join(HOME, "Library", "CloudStorage")
        try: mounts = [os.path.join(cs, d) for d in sorted(os.listdir(cs)) if d.startswith("GoogleDrive-")]
        except PermissionError: BLOCKED.append(cs)
        except OSError: pass
    MOUNTS[:] = mounts
    roots = []
    for m in mounts:   # every top folder of the mount, whatever it's called - the search walks below them
        try: roots += [os.path.join(m, d) for d in sorted(os.listdir(m)) if not d.startswith((".", "$")) and os.path.isdir(os.path.join(m, d))]
        except PermissionError: BLOCKED.append(m)
    for r in roots:
        try: os.listdir(r)
        except PermissionError: BLOCKED.append(r)
    return roots

def visible(roots):
    """what this computer can see in Google Drive: top folders and shared drive names"""
    out = []
    for r in roots:
        try: kids = [e.name for e in os.scandir(r) if e.is_dir() and not e.name.startswith(".")][:15]
        except OSError: kids = []
        out += [pretty(os.path.join(r, k)) for k in kids] or [pretty(r)]
    return ", ".join(out) or "nothing yet"

def walk(roots):
    """breadth-first (dir, entries) over Google Drive, shallowest first; Drive lists folders without downloading files"""
    level, seen = [(r, 0) for r in roots], 0
    while level and seen < MAX_DIRS:
        nxt = []
        for d, depth in level:
            try: entries = [e for e in os.scandir(d) if not e.name.startswith((".", "$"))]
            except OSError: continue
            seen += 1
            yield d, entries
            nxt += [(e.path, depth + 1) for e in entries if depth < MAX_DEPTH and e.is_dir()]
        level = nxt

def find_brand(roots):
    hits = [d for d, es in walk(roots) if any(e.is_file() and e.name.lower() == BRAND for e in es)][:10]
    return sorted(hits, key=lambda d: (not os.path.isfile(os.path.join(d, SETTINGS)), d.count(os.sep), d))

def find_folder(roots, name):
    """folders called <name> (any case); falls back to names containing it"""
    want = name.casefold(); exact, partial = [], []
    for r in roots:                       # the folder may be a whole shared drive ("Shared drives/Bracelet")
        n = os.path.basename(os.path.normpath(r)).casefold()
        if n == want: exact.append(r)
        elif want in n and n not in MY_NAMES: partial.append(r)
    for d, es in walk(roots):
        for e in es:
            if e.is_dir():
                n = e.name.casefold()
                if n == want: exact.append(e.path)
                elif want in n: partial.append(e.path)
        if len(exact) >= 5: break
    return exact or partial[:5]

def pretty(p):
    """path as the user sees it in Google Drive ("Gedeelde drives/Bracelet")"""
    for m in MOUNTS + FORCED:
        m = os.path.normpath(m)
        if os.path.normpath(p).startswith(m): return os.path.relpath(p, m).replace("\\", "/")
    return p.replace("\\", "/")

def load(p):
    try: return json.load(open(p, encoding="utf-8-sig"))
    except (OSError, ValueError): return {}

def resolve(base, v):
    return "" if not v else os.path.normpath(v if os.path.isabs(v) else os.path.join(base, v))

def ask(q, default=""):
    if AUTO: return default
    a = input(f"{q}" + (f" [{default}]" if default else "") + ": ").strip().strip('"')
    return os.path.expanduser(a) if a else default

def newest(pattern_dirs, patterns):
    files = [f for d in pattern_dirs for p in patterns for f in glob.glob(os.path.join(d, p))]
    return max(files, key=os.path.getmtime) if files else ""

old = load(CFG_F)
LOCAL = "--local" in args or (bool(old.get("local")) and "--drive" not in args)
need = []
os.makedirs(CFG_DIR, exist_ok=True)
if LOCAL:   # footage on this computer: search the usual home folders instead of Google Drive
    roots = [os.path.join(HOME, d) for d in LOCAL_DIRS if os.path.isdir(os.path.join(HOME, d))]
    print("No Google Drive - footage is in a folder on this computer")
else:
    roots = drive_roots()
if not roots and not FORCED and not LOCAL:
    need.append("google-drive: Google Drive for Desktop isn't signed in on this computer (no My Drive / Shared drives found)")
if BLOCKED:
    need.append("drive-permission: the Mac isn't letting Claude / Codex read Google Drive. Open System Settings -> Privacy & "
                "Security -> Files and Folders (or Full Disk Access), turn on access for the Claude / Codex app, quit and "
                "reopen it, then run setup again")

# ---- brand rules + settings: from Downloads (e.g. an email attachment) > Google Drive > stored copy ----
local_brand, local_settings = os.path.join(CFG_DIR, BRAND), os.path.join(CFG_DIR, SETTINGS)
dl_dirs = [os.path.join(HOME, d) for d in ("Downloads", "Desktop", "Documents")]
dl_brand = newest(dl_dirs, ["brand.md", "brand (*).md", "brand-*.md", "*-brand.md"])   # brand.md, brand (1).md, fitsleeps-brand.md
dl_settings = newest(dl_dirs, ["ai-video-editor.json", "ai-video-editor (*).json", "ai-video-editor*.json"])
drive_kit = ""
if not (dl_brand and dl_settings) and roots and not LOCAL:
    hits = find_brand(roots)
    if hits:
        drive_kit = os.path.normpath(hits[0])
        if len(hits) > 1: print("  (brand.md is in more than one Drive folder - using " + pretty(drive_kit) + ")")
for src, dst in ((dl_brand or (drive_kit and os.path.join(drive_kit, BRAND)), local_brand),
                 (dl_settings or (drive_kit and os.path.join(drive_kit, SETTINGS)), local_settings)):
    if src and os.path.isfile(src) and (not os.path.isfile(dst) or os.path.getmtime(src) > os.path.getmtime(dst)):
        shutil.copy2(src, dst); print(f"Saved a private copy of {os.path.basename(src)} (from {pretty(os.path.dirname(src))})")
s = load(local_settings)
if LOCAL and not os.path.isfile(local_brand) and os.path.isfile(os.path.join(HERE, "blank-brand.md")):
    shutil.copy2(os.path.join(HERE, "blank-brand.md"), local_brand)   # a blank style file the user fills in over time
    print(f"Made a blank style file for you to fill in: {local_brand}")
brand = local_brand if os.path.isfile(local_brand) else ""

# ---- footage folder ----
footage = ""
if WANT:
    if os.path.isdir(os.path.expanduser(WANT)):
        footage = os.path.normpath(os.path.expanduser(WANT))
    elif roots:
        found = find_folder(roots, WANT)
        if len(found) == 1:
            footage = os.path.normpath(found[0])
        elif found:
            need.append(f"footage-choose: more than one folder matches \"{WANT}\": " + " | ".join(pretty(f) for f in found)
                        + " - ask the user which one, then run setup again with that full path")
        elif LOCAL:
            need.append(f"footage-not-found: no folder called \"{WANT}\" in {', '.join(LOCAL_DIRS)} on this computer. "
                        "Ask the user where the folder is (they can drag it into the chat, or copy its path from File "
                        "Explorer / Finder), then run setup again with that full path")
        else:
            need.append(f"footage-not-found: no folder called \"{WANT}\" in Google Drive. What this computer can see: "
                        f"{visible(roots)}. Check the spelling with the user (or Google Drive may still be loading - wait "
                        "a minute). If the folder is under \"Shared with me\" in drive.google.com, they add a shortcut to "
                        "it in My Drive first, then run setup again")
if not footage and s.get("footage_dir"):
    footage = resolve(drive_kit or CFG_DIR, s["footage_dir"])
if not footage and drive_kit:
    footage = os.path.dirname(drive_kit) if KIT_NAME.match(os.path.basename(drive_kit)) else drive_kit
if not footage and old.get("footage_dir") and os.path.isdir(old["footage_dir"]):
    footage = old["footage_dir"]
if not AUTO:
    while True:
        a = ask("Footage folder - its full path, or its name if it's in " + "/".join(LOCAL_DIRS) if LOCAL
                else "Footage folder - its name in Google Drive, or the full path", footage)
        if a and os.path.isdir(a): footage = a; break
        found = find_folder(roots, a) if a and roots else []
        if len(found) == 1: footage = found[0]; print("Found " + pretty(footage)); break
        print("Several matches: " + " | ".join(pretty(f) for f in found) if found else "Can't find that folder - try again.")
    need = [n for n in need if not n.startswith("footage")]
if footage:
    print("Footage folder: " + pretty(footage))
elif LOCAL and not any(n.startswith("footage") for n in need):
    need.append("footage-folder: ask the user which folder on this computer holds their footage (its name if it's in "
                "Videos / Desktop / Documents, otherwise the full path), then run setup again with it")
elif roots and not any(n.startswith("footage") for n in need):
    need.append("footage-folder: ask the user which Google Drive folder holds their footage (just its name, e.g. "
                "\"Bracelet\"), then run setup again with that name")

# ---- the rest ----
projects = ask("Where to keep edit projects on this computer", old.get("projects_dir") or os.path.join(HOME, "Video Edits"))
output = ask("Where finished videos go (Enter = the AI asks on the first video)", resolve(footage, s.get("output_dir")) or old.get("output_dir", ""))
music = ask("Music folder (Enter to skip)", resolve(footage, s.get("music_dir")) or old.get("music_dir", ""))
sfx = ask("Sound effects folder (Enter to skip)", resolve(footage, s.get("sfx_dir")) or old.get("sfx_dir", ""))
key = s.get("elevenlabs_api_key") or old.get("elevenlabs_api_key", "")
if not AUTO:
    k = getpass.getpass("ElevenLabs API key (hidden; Enter keeps " + ("the current one" if key else "it empty") + "): ").strip()
    key = k or key
if not brand:
    need.append(f"brand-file: no {BRAND} on this computer yet - the user saves the {BRAND} file they were sent (e.g. the "
                "email attachment) to their Downloads folder, then run setup again")
if not key and LOCAL:
    need.append(f"elevenlabs-key: no ElevenLabs key yet. The user signs up at elevenlabs.io, creates an API key (Developers "
                f"-> API keys), then runs the setup themselves in a terminal so they can paste it hidden: the same setup "
                f"command without -Auto / --auto. Never ask for the key in chat")
elif not key:
    need.append(f"elevenlabs-key: no ElevenLabs key - the user saves the {SETTINGS} file they were sent (e.g. the email "
                "attachment) to their Downloads folder, then run setup again")

for d in [x for x in (projects, output) if x]:
    try: os.makedirs(d, exist_ok=True)
    except OSError as e: need.append(f"folder: can't create {d} ({e})")

cfg = {"footage_dir": footage, "projects_dir": projects, "output_dir": output, "music_dir": music, "sfx_dir": sfx,
       "brand_file": brand, "elevenlabs_api_key": key, "local": LOCAL}
if footage or not AUTO:   # never write a config without footage in auto mode - the setup check would think it's done
    json.dump(cfg, open(CFG_F, "w", encoding="utf-8"), indent=2)
    for f in (CFG_F, local_settings):
        try: os.chmod(f, 0o600)
        except OSError: pass
    print(f"Saved settings to {CFG_F}")
    print(f"  finished videos: {output or '(not chosen yet - the AI asks on the first video)'}\n  brand file: {brand or '(none)'}")

for n in need: print("NEED: " + n)
sys.exit(2 if need else 0)

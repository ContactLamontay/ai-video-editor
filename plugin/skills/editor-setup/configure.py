# Writes ~/.ai-video-editor/config.json. Finds the footage library by itself: it searches Google Drive for the
# brand file (brand.md). The footage folder is:
#   - the folder that holds brand.md, or
#   - the folder above it, when brand.md sits in its own "AI video editor" folder (any case, spaces/-/_ allowed), or
#   - "footage_dir" from the settings file (relative to the brand.md folder, e.g. "..", or absolute).
# An optional ai-video-editor.json next to brand.md supplies the rest, so nobody has to type paths or keys:
#   {"elevenlabs_api_key": "...", "music_dir": "Music", "sfx_dir": "Sound FX", "output_dir": "Finished"}
#   (music/sfx/output folders are relative to the footage folder, or absolute). Without output_dir, the AI asks the
#   user where finished videos should go the first time they make a video.
#
#   python configure.py           asks, with everything it found filled in as defaults (Enter accepts)
#   python configure.py --auto    asks nothing - for the AI to run. Prints "NEED: <what>" lines and exits 2 when
#                                 something only the user can do is missing.
#   --drive-root <dir>            search this folder instead of the detected Google Drive (repeatable; for testing)
import getpass, json, os, re, string, sys

HOME = os.path.expanduser("~")
CFG_DIR = os.path.join(HOME, ".ai-video-editor"); CFG_F = os.path.join(CFG_DIR, "config.json")
BRAND, SETTINGS = "brand.md", "ai-video-editor.json"
MAX_DEPTH = 5
KIT_NAME = re.compile(r"^ai[\s_-]*video[\s_-]*editor\b", re.I)   # "AI video editor", "AI-Video-Editor files", ...
args = sys.argv[1:]
AUTO = "--auto" in args
FORCED = [args[i + 1] for i, a in enumerate(args) if a == "--drive-root" and i + 1 < len(args)]

def drive_roots():
    """top-level folders of Google Drive for Desktop: My Drive and each shared drive"""
    if FORCED: return FORCED
    mounts = []
    if os.name == "nt":
        mounts = [f"{d}:\\" for d in string.ascii_uppercase if os.path.isdir(f"{d}:\\My Drive") or os.path.isdir(f"{d}:\\Shared drives")]
    else:
        cs = os.path.join(HOME, "Library", "CloudStorage")
        if os.path.isdir(cs): mounts = [os.path.join(cs, d) for d in sorted(os.listdir(cs)) if d.startswith("GoogleDrive-")]
    roots = []
    for m in mounts:
        if os.path.isdir(os.path.join(m, "My Drive")): roots.append(os.path.join(m, "My Drive"))
        sd = os.path.join(m, "Shared drives")
        if os.path.isdir(sd): roots += [os.path.join(sd, d) for d in sorted(os.listdir(sd)) if os.path.isdir(os.path.join(sd, d))]
    return roots

def find_brand(roots):
    """breadth-first search for brand.md, shallowest first (Drive lists folders without downloading files)"""
    hits, level = [], [(r, 0) for r in roots]
    while level and len(hits) < 10:
        nxt = []
        for d, depth in level:
            try: entries = list(os.scandir(d))
            except OSError: continue
            for e in entries:
                if e.name.startswith(".") or e.name.startswith("$"): continue
                if e.is_file() and e.name.lower() == BRAND: hits.append(d)
                elif e.is_dir() and depth < MAX_DEPTH: nxt.append((e.path, depth + 1))
        level = nxt
    # prefer the folder that also has the settings file
    return sorted(hits, key=lambda d: (not os.path.isfile(os.path.join(d, SETTINGS)), d.count(os.sep), d))

def load(p):
    try: return json.load(open(p, encoding="utf-8-sig"))
    except (OSError, ValueError): return {}

def resolve(base, v):
    return "" if not v else os.path.normpath(v if os.path.isabs(v) else os.path.join(base, v))

def ask(q, default=""):
    if AUTO: return default
    a = input(f"{q}" + (f" [{default}]" if default else "") + ": ").strip().strip('"')
    return os.path.expanduser(a) if a else default

old = load(CFG_F)
need = []
roots = drive_roots()
if not roots and not FORCED:
    need.append("google-drive: Google Drive for Desktop isn't signed in on this computer (no My Drive / Shared drives found)")

hits = find_brand(roots) if roots else []
footage = old.get("footage_dir", "") if old.get("footage_dir") and os.path.isdir(old.get("footage_dir")) else ""
kit = os.path.dirname(old.get("brand_file", "")) if old.get("brand_file") else ""   # folder holding brand.md + settings
if hits:
    kit = os.path.normpath(hits[0])
    ks = load(os.path.join(kit, SETTINGS))
    if ks.get("footage_dir"):                                   # settings file says where the footage is
        footage = resolve(kit, ks["footage_dir"])
    elif KIT_NAME.match(os.path.basename(kit)):                 # brand.md in its own "AI video editor" folder
        footage = os.path.dirname(kit)
    else:                                                       # brand.md right in the footage folder
        footage = kit
    print(f"Found the brand file in: {kit}")
    if footage != kit: print(f"Footage folder: {footage}")
    if len(hits) > 1: print("  (also found brand.md in: " + "; ".join(hits[1:4]) + " - using the first)")
elif roots:
    need.append(f"brand-file: no {BRAND} found in Google Drive (searched {len(roots)} drive(s), {MAX_DEPTH} folders deep). "
                f"If the footage folder was shared with this person, it only shows up on this computer after they add a "
                f"shortcut to it in My Drive. Otherwise: wrong Google account, or Drive is still loading - run setup again")

if not AUTO:
    while True:
        footage = ask("Footage folder (the top folder with all the footage)", footage)
        if footage and os.path.isdir(footage): break
        print("Can't find that folder - copy its path from File Explorer / Finder.")
    need = [n for n in need if not n.startswith("brand-file")]

kit = kit or footage
s = load(os.path.join(kit, SETTINGS)) if kit else {}
if s: print(f"Using settings from {os.path.join(kit, SETTINGS)}")
brand = os.path.join(kit, BRAND) if kit and os.path.isfile(os.path.join(kit, BRAND)) else old.get("brand_file", "")
projects = ask("Where to keep edit projects on this computer", old.get("projects_dir") or os.path.join(HOME, "Video Edits"))
output = ask("Where finished videos go (Enter = the AI asks on the first video)", resolve(footage, s.get("output_dir")) or old.get("output_dir", ""))
music = ask("Music folder (Enter to skip)", resolve(footage, s.get("music_dir")) or old.get("music_dir", ""))
sfx = ask("Sound effects folder (Enter to skip)", resolve(footage, s.get("sfx_dir")) or old.get("sfx_dir", ""))
key = s.get("elevenlabs_api_key") or old.get("elevenlabs_api_key", "")
if not AUTO:
    k = getpass.getpass("ElevenLabs API key (hidden; Enter keeps " + ("the current one" if key else "it empty") + "): ").strip()
    key = k or key
if not key and footage:   # the key lives next to brand.md, so only ask once that's found
    need.append(f"elevenlabs-key: no ElevenLabs key - add \"elevenlabs_api_key\" to {SETTINGS} next to {BRAND} in Google Drive")

for d in [x for x in (projects, output) if x]:
    try: os.makedirs(d, exist_ok=True)
    except OSError as e: need.append(f"folder: can't create {d} ({e})")

cfg = {"footage_dir": footage, "projects_dir": projects, "output_dir": output, "music_dir": music, "sfx_dir": sfx,
       "brand_file": brand, "elevenlabs_api_key": key}
if footage or not AUTO:   # never write an empty config in auto mode - the setup check would think it's done
    os.makedirs(CFG_DIR, exist_ok=True)
    json.dump(cfg, open(CFG_F, "w", encoding="utf-8"), indent=2)
    try: os.chmod(CFG_F, 0o600)
    except OSError: pass
    print(f"Saved settings to {CFG_F}")
    print(f"  footage: {footage}\n  finished videos: {output or '(not chosen yet - the AI asks on the first video)'}\n  projects: {projects}\n  brand file: {brand or '(none)'}")

for n in need: print("NEED: " + n)
sys.exit(2 if need else 0)

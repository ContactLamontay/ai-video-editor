# Read or change one setting in ~/.ai-video-editor/config.json (never prints the API key).
#   python settings.py                         show the current settings
#   python settings.py output_dir "<folder>"   where finished videos go (created if missing)
# Settable: output_dir, music_dir, sfx_dir, projects_dir. Folders may be absolute, or relative to the footage folder.
import json, os, sys

CFG_F = os.path.join(os.path.expanduser("~"), ".ai-video-editor", "config.json")
KEYS = ("output_dir", "music_dir", "sfx_dir", "projects_dir")
cfg = json.load(open(CFG_F, encoding="utf-8-sig")) if os.path.exists(CFG_F) else {}

if len(sys.argv) == 1:
    for k, v in cfg.items():
        print(f"{k}: {'(set)' if k == 'elevenlabs_api_key' and v else v or '(not set)'}")
    sys.exit()
if len(sys.argv) != 3 or sys.argv[1] not in KEYS:
    sys.exit(f"usage: python settings.py [{'|'.join(KEYS)} \"<folder>\"]")
if not cfg:
    sys.exit("This computer isn't set up yet - run the editor-setup skill first.")

key, val = sys.argv[1], os.path.expanduser(sys.argv[2].strip().strip('"'))
if val and not os.path.isabs(val):
    val = os.path.join(cfg.get("footage_dir") or os.getcwd(), val)
val = os.path.normpath(val) if val else ""
if val:
    try: os.makedirs(val, exist_ok=True)
    except OSError as e: sys.exit(f"Can't create {val}: {e}")
cfg[key] = val
json.dump(cfg, open(CFG_F, "w", encoding="utf-8"), indent=2)
print(f"{key} = {val or '(cleared)'}")

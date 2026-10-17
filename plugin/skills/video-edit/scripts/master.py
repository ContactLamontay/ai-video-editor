# Joins the cuts, burns in captions (+ word captions for shorts), lays in the master mix.
#   PREVIEW=1 python master.py  -> Edit/Previews/<name>_preview_r<N>.mp4 + .edits.json + .words.json
#                                  (the video-review screen reads these; N increments each round)
#   python master.py            -> <output_dir>/<name> - Final.mp4 (landscape) / <name> - Short.mp4 (short)
#                                  only after the editor approves the preview
import json, os, sys, glob, shutil, subprocess
import enc
from common import VLOG, ED, WORK, CACHE, PREVIEW, FPS, FPS_STR, NAME, FINISHED, OUTPUT_CHOSEN, SHORT, FW, RW, TAG, clips
if not PREVIEW and not OUTPUT_CHOSEN:
    sys.exit('No finished-videos folder chosen yet. Ask the user where finished videos should go, save it with\n'
             '  python settings.py output_dir "<folder>"\nthen run master.py again.')
P = json.load(open(WORK + "/plan.json")); C = json.load(open(WORK + "/caps.json")) if os.path.exists(WORK + "/caps.json") else []
SEGD = f"{CACHE}/segments_{TAG}"; K = FW / RW
WORDS = SHORT or os.environ.get("WORDCAPS") == "1"
if WORDS:
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "subs.py")], check=True)
    shutil.copy(WORK + "/words.ass", CACHE + "/words.ass")      # libass path: relative, run from CACHE

if PREVIEW:
    PV = ED + "/Previews"; os.makedirs(PV, exist_ok=True)
    rnd = 1 + max([int(p.rsplit("_r", 1)[1].split(".")[0]) for p in glob.glob(f"{PV}/{NAME}_preview_r*.mp4")] or [0])
    OUTF = f"{PV}/{NAME}_preview_r{rnd}.mp4"
else:
    os.makedirs(FINISHED, exist_ok=True); OUTF = f"{FINISHED}/{NAME} - {'Short' if SHORT else 'Final'}.mp4"

lst = CACHE + "/concat.txt"
with open(lst, "w") as f:
    for i in range(len(P["segs"])): f.write(f"file '{SEGD}/s{i:03d}.mov'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-map", "0:v", "-c", "copy", CACHE + "/video_only.mp4"], check=True)
cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-hwaccel", "auto", "-i", CACHE + "/video_only.mp4", "-i", CACHE + "/master_mix.wav"]
fg, last = [], "0:v"
for k, c in enumerate(C):
    cmd += ["-itsoffset", f"{round(c['tl'] * FPS) / FPS:.4f}", "-i", c["small"]]
    src = f"[{k + 2}:v]"
    if K != 1: fg.append(f"{src}scale=iw/{K}:ih/{K}[c{k}]"); src = f"[c{k}]"
    fg.append(f"[{last}]{src}overlay={int(c['x'] / K)}:{int(c['y'] / K)}:eof_action=pass[v{k}]"); last = f"v{k}"
tail = "subtitles=words.ass," if WORDS else ""
tail += "" if SHORT else f"fade=t=out:st={P['total'] / FPS - 0.8:.3f}:d=0.8,"     # shorts loop: no fade
fg.append(f"[{last}]{tail}format=yuv420p[vout]")
br = ("4M", "6M") if PREVIEW and SHORT else ("8M", "12M") if PREVIEW else ("16M", "24M") if SHORT else ("60M", "80M")
cmd += ["-filter_complex", ";".join(fg), "-map", "[vout]", "-map", "1:a", "-r", FPS_STR,
        *enc.bitrate_args(br[0], br[1]),
        "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", OUTF]
subprocess.run(cmd, check=True, cwd=CACHE)

if PREVIEW:   # sidecars for the video-review screen
    T = json.load(open(WORK + "/t_el.json")); CL = clips(); pic = []
    for i, s in enumerate(P["segs"]):
        txt = " ".join(w[2].strip() for seg in T.get(s["c"], []) for w in seg["w"] if s["a"] <= w[0] < s["b"] and not w[2].strip().startswith("("))
        vc, vin = (s["ov"] if s.get("ov") else (s["c"], s["a"] + s["vo"]))
        src = CL.get(vc, {}).get("mp4") or ""
        pic.append({"start": round(s["rec"] / FPS, 3), "end": round((s["rec"] + s["n"]) / FPS, 3),
                    "label": f"{i:03d} {s['c']} " + (txt[:40] if txt else f"b-roll {s['z']}"),
                    "source": os.path.relpath(src, VLOG).replace("\\", "/") if src else "", "src_in": round(vin, 3)})
    gfx = [{"start": c["tl"], "end": round(c["tl"] + c["nf"] / FPS, 3), "label": c["text"][:40]} for c in C]
    mus = [{"start": c["tl0"], "end": c["tl1"], "label": os.path.basename(c["f"])[:40]} for c in P["cues"]]
    sfx = [{"start": e["tl"], "end": e["tl"] + 0.5, "label": os.path.basename(e["f"])[:30]} for e in P["events"] if e["type"] == "sfx"]
    total = round(P["total"] / FPS, 3)
    tracks = [{"name": "Picture", "kind": "aroll" if SHORT else "video", "items": pic},
              {"name": "Graphics", "kind": "graphics", "items": gfx},
              {"name": "Dialogue", "kind": "audio", "items": [{"start": 0.0, "end": total, "label": "Dialogue mix"}]},
              {"name": "Music", "kind": "music", "items": mus}, {"name": "SFX", "kind": "sfx", "items": sfx}]
    base = OUTF[:-4]
    json.dump({"fps": FPS, "tracks": tracks}, open(base + ".edits.json", "w"), indent=1)
    words = json.load(open(WORK + "/words_timeline.json")) if os.path.exists(WORK + "/words_timeline.json") else []
    if not words:   # vlog without word captions: still give the review screen word timings
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "subs.py")], check=True)
        words = json.load(open(WORK + "/words_timeline.json"))
    json.dump(words, open(base + ".words.json", "w"))
print("EXPORT DONE ->", OUTF)

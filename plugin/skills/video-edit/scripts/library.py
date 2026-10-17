# B-roll / footage library index for the shared Google Drive folder (config footage_dir).
#   python library.py scan [subfolder] [--thumbs]  -> ~/.ai-video-editor/library/index.json (+ thumbs/<id>.jpg strips)
#   python library.py find wrist closeup            -> clips whose path, description or tags match every word
#   python library.py tag <id> "<description>" tag1 tag2 ...   -> store what's in a clip (after looking at its thumb strip)
# Scans are incremental (path + size + mtime). Probing reads only file headers; --thumbs pulls 5 frames per clip,
# which makes Google Drive stream part of each file - fine for a folder, slow for the whole library on first run.
import hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("VLOG_DIR", os.path.join(os.path.expanduser("~"), ".ai-video-editor", "library"))
from common import FOOTAGE, FINISHED, CFG_DIR, VIDEO_EXT

LIB = os.path.join(CFG_DIR, "library"); TH = os.path.join(LIB, "thumbs"); IDX = os.path.join(LIB, "index.json")
os.makedirs(TH, exist_ok=True)
idx = json.load(open(IDX, encoding="utf8")) if os.path.exists(IDX) else {}

def save(): json.dump(idx, open(IDX, "w", encoding="utf8"), indent=1)

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                        "-of", "json", p], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout); st = j["streams"][0]
        return {"dur": round(float(j["format"]["duration"]), 2), "w": st["width"], "h": st["height"], "fps": st["r_frame_rate"]}
    except (ValueError, KeyError, IndexError):
        return {"dur": 0}

def thumbs(cid, p, dur):
    out = os.path.join(TH, cid + ".jpg")
    if os.path.exists(out) or not dur: return
    ts = [dur * f for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
    args = sum([["-ss", f"{t:.2f}", "-i", p] for t in ts], [])
    fc = "".join(f"[{i}:v]scale=240:-2,setsar=1[t{i}];" for i in range(5)) + "".join(f"[t{i}]" for i in range(5)) + "hstack=5"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-frames:v", "1", out], capture_output=True)

def scan(sub="", with_thumbs=False):
    root = os.path.join(FOOTAGE, sub) if sub else FOOTAGE
    if not root or not os.path.isdir(root): sys.exit(f"footage folder not found: {root!r} (check footage_dir in {CFG_DIR}/config.json)")
    skip = os.path.normcase(os.path.realpath(FINISHED))      # finished videos can live inside the footage folder
    files = []
    for d, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and os.path.normcase(os.path.realpath(os.path.join(d, x))) != skip]
        files += [os.path.join(d, f) for f in fs if f.lower().endswith(VIDEO_EXT) and not f.startswith(".")]
    todo = []
    for p in files:
        st = os.stat(p); cid = hashlib.md5(p.lower().encode()).hexdigest()[:10]
        e = idx.get(cid)
        if not e or e.get("size") != st.st_size or e.get("mtime") != int(st.st_mtime): todo.append((cid, p, st))
    def one(t):
        cid, p, st = t; info = probe(p)
        if with_thumbs: thumbs(cid, p, info.get("dur"))
        old = idx.get(cid, {})
        return cid, {"path": os.path.relpath(p, FOOTAGE).replace("\\", "/"), "size": st.st_size, "mtime": int(st.st_mtime), **info,
                     "desc": old.get("desc", ""), "tags": old.get("tags", [])}
    with ThreadPoolExecutor(6) as ex:
        for n, (cid, e) in enumerate(ex.map(one, todo), 1):
            idx[cid] = e
            if n % 25 == 0: save(); print(f"{n}/{len(todo)}", flush=True)
    if with_thumbs:
        with ThreadPoolExecutor(4) as ex: list(ex.map(lambda c: thumbs(c, os.path.join(FOOTAGE, idx[c]["path"]), idx[c].get("dur")),
                                                     [c for c in idx if idx[c]["path"].startswith(sub.replace("\\", "/"))]))
    save(); untagged = sum(1 for e in idx.values() if not e["desc"])
    print(f"{len(files)} clips in {root} ({len(todo)} new/changed). index: {IDX}  untagged: {untagged}  thumbs: {TH}")

def find(words):
    ws = [w.lower() for w in words]
    for cid, e in idx.items():
        hay = (e["path"] + " " + e["desc"] + " " + " ".join(e["tags"])).lower()
        if all(w in hay for w in ws):
            print(f"{cid}  {e.get('dur', 0):6.1f}s  {e.get('w', '?')}x{e.get('h', '?')}  {os.path.join(FOOTAGE, e['path'])}  | {e['desc']}")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__ if __doc__ else "usage: library.py scan|find|tag")
    if a[0] == "scan": scan(next((x for x in a[1:] if not x.startswith("--")), ""), "--thumbs" in a)
    elif a[0] == "find": find(a[1:])
    elif a[0] == "tag": idx[a[1]]["desc"] = a[2]; idx[a[1]]["tags"] = a[3:]; save(); print("tagged", a[1])

# Step 1: per-clip audio, labelled contact sheets, ElevenLabs Scribe transcript, footage frame rate.
#   python prep.py                -> WORK/audio/*.wav, WORK/sheets/*.jpg, WORK/t_el.json, WORK/transcript.txt, WORK/meta.json
#   FORMAT=short python prep.py   -> also WORK/centers.json (where the speaker sits in each landscape clip, for 9:16 crops)
# Re-running skips finished pieces (safe to resume). Needs the ElevenLabs key (setup script stores it, or ELEVENLABS_API_KEY env var).
import os, sys, json, glob, subprocess, uuid, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from common import WORK, META_F, FORMAT, CFG, clips
from fonts import font

AUD = WORK + "/audio"; SH = WORK + "/sheets"; FR = WORK + "/_frames"
for d in (AUD, SH, FR): os.makedirs(d, exist_ok=True)
C = clips()

def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0

def audio(k):
    out = f"{AUD}/{k}.wav"
    if not os.path.exists(out):
        src = C[k]["lrf"] or C[k]["mp4"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", out])
    return out

def sheet(k):
    if glob.glob(f"{SH}/{k}_*.jpg"): return
    src = C[k]["lrf"] or C[k]["mp4"]; d = f"{FR}/{k}"; os.makedirs(d, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "fps=0.5,scale=320:-2", "-q:v", "4", f"{d}/%04d.jpg"])
    ims = sorted(glob.glob(f"{d}/*.jpg"))
    if not ims: return
    lab = font("arialbd.ttf", 22)
    for si in range(0, len(ims), 30):
        chunk = ims[si:si + 30]; w, h = Image.open(chunk[0]).size; rows = (len(chunk) + 5) // 6
        s = Image.new("RGB", (6 * w, rows * h)); dr = ImageDraw.Draw(s)
        for i, p in enumerate(chunk):
            x, y = (i % 6) * w, (i // 6) * h; s.paste(Image.open(p), (x, y))
            dr.text((x + 6, y + 4), f"{k} {(si + i) * 2}s", font=lab, fill="yellow", stroke_width=2, stroke_fill="black")
        s.save(f"{SH}/{k}_{si // 30 + 1:02d}.jpg", quality=80)

def stt(path, model="scribe_v2"):
    key = os.environ.get("ELEVENLABS_API_KEY") or CFG.get("elevenlabs_api_key")
    if not key: sys.exit("No ElevenLabs key - run the editor-setup skill"); b = uuid.uuid4().hex; body = b""
    for f, v in [("model_id", model), ("timestamps_granularity", "word"), ("diarize", "true"), ("tag_audio_events", "true"), ("language_code", "en")]:
        body += f"--{b}\r\nContent-Disposition: form-data; name=\"{f}\"\r\n\r\n{v}\r\n".encode()
    body += f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    body += open(path, "rb").read() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=600))

def convert(raw):
    """Scribe output -> {clip: [{s,e,t,spk,w:[[start,end,text],...]}]} split on 0.6s gaps"""
    out = {}
    for k, r in raw.items():
        segs, cur = [], None
        for w in (x for x in r.get("words", []) if x["type"] in ("word", "audio_event")):
            txt = (" " + w["text"]) if w["type"] == "word" else f" ({w['text'].strip('()')})"
            item = [round(w["start"], 2), round(w["end"], 2), txt]
            if cur is None or w["start"] - cur["e"] > 0.6:
                cur = {"s": item[0], "e": item[1], "w": [], "spk": w.get("speaker_id", "")[-1:]}; segs.append(cur)
            cur["w"].append(item); cur["e"] = item[1]
        for s in segs: s["t"] = "".join(x[2] for x in s["w"]).strip()
        out[k] = segs
    return out

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,width,height:stream_side_data=rotation",
                        "-of", "json", p], capture_output=True, text=True)
    st = json.loads(r.stdout)["streams"][0]; rot = 0
    for sd in st.get("side_data_list", []): rot = int(sd.get("rotation", 0))
    w, h = st["width"], st["height"]
    if abs(rot) == 90: w, h = h, w
    return st["r_frame_rate"], w, h

def speaker_x(k):
    """horizontal centre of the person in a landscape clip (0..1), from a background-removal mask on 3 frames"""
    try:
        from rembg import remove, new_session
        import numpy as np
    except ImportError:
        return 0.5
    global _S
    if "_S" not in globals(): _S = new_session("isnet-general-use")
    src = C[k]["lrf"] or C[k]["mp4"]; D = dur(src); xs = []
    for f in (0.25, 0.5, 0.75):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{D * f:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=640:-2",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if not r.stdout: continue
        import io
        m = np.asarray(remove(Image.open(io.BytesIO(r.stdout)).convert("RGB"), session=_S, only_mask=True), float)
        top = m[: m.shape[0] // 2]                      # head/shoulders region decides the framing
        if top.sum() > 0: xs.append(float((top.sum(0) * np.arange(top.shape[1])).sum() / top.sum() / top.shape[1]))
    return round(float(np.median(xs)), 3) if xs else 0.5

if __name__ == "__main__":
    keys = [k for k in C if dur(C[k]["lrf"] or C[k]["mp4"]) >= 1.0]   # sub-second clips are accidental taps
    if not os.path.exists(META_F):
        from collections import Counter
        info = {k: probe(C[k]["mp4"] or C[k]["lrf"]) for k in keys}
        fps = Counter(v[0] for v in info.values()).most_common(1)[0][0]
        json.dump({"format": FORMAT, "fps": fps, "clips": {k: {"fps": v[0], "w": v[1], "h": v[2]} for k, v in info.items()}},
                  open(META_F, "w"), indent=1)
        mixed = sorted({v[0] for v in info.values()})
        print(f"format={FORMAT} fps={fps}" + (f"  (WARNING mixed rates {mixed})" if len(mixed) > 1 else ""), flush=True)
    meta = json.load(open(META_F))
    if meta["format"] == "short" and not os.path.exists(WORK + "/centers.json"):
        cen = {k: (speaker_x(k) if meta["clips"][k]["w"] > meta["clips"][k]["h"] else 0.5) for k in keys}
        json.dump(cen, open(WORK + "/centers.json", "w"), indent=1); print("speaker centres:", cen, flush=True)
    with ThreadPoolExecutor(6) as ex: list(ex.map(audio, keys))
    with ThreadPoolExecutor(4) as ex: list(ex.map(sheet, keys))
    print(f"audio + sheets: {len(keys)} clips", flush=True)
    rawf = WORK + "/el_raw.json"; raw = json.load(open(rawf)) if os.path.exists(rawf) else {}
    for k in keys:
        if k in raw: continue
        try:
            raw[k] = stt(f"{AUD}/{k}.wav"); json.dump(raw, open(rawf, "w"))
            print(k, sum(1 for w in raw[k].get("words", []) if w["type"] == "word"), "words", flush=True)
        except urllib.error.HTTPError as e:
            sys.exit(f"{k}: ElevenLabs HTTP {e.code} {e.read()[:300].decode(errors='replace')}")
    T = convert(raw); json.dump(T, open(WORK + "/t_el.json", "w"))
    with open(WORK + "/transcript.txt", "w", encoding="utf8") as f:
        for k in sorted(T):
            if not T[k]: continue
            f.write(f"== {k}\n")
            for s in T[k]: f.write(f"  {s['s']:6.2f}-{s['e']:6.2f} [{s['spk']}] {s['t']}\n")
    print("transcript ->", WORK + "/transcript.txt")

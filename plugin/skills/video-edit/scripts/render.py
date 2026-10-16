# Renders every cut in plan.json: reframe (shorts) + zoom + grade baked, H.264 (best available encoder, see enc.py) + PCM dialogue in a .mov.
#   PREVIEW=1 python render.py   -> small preview cuts (DJI .LRF files when present: ~2 min for a 10 min vlog)
#   python render.py             -> full-quality cuts (4K vlog ~30 min; 1080x1920 short a few minutes)
# Output goes to the local cache (common.CACHE).
# Unchanged cuts are skipped (each .mov has a .sig of its plan entry), so re-renders after tweaks are fast.
import json, os, sys, subprocess, wave
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import grades, enc
from common import WORK, CACHE, PREVIEW, FPS, FPS_STR, SHORT, RW, RH, TAG, RAW_AUDIO, src_video, src_audio

OUT = f"{CACHE}/segments_{TAG}"; os.makedirs(OUT, exist_ok=True)
AUD = CACHE + "/a48"; NPY = CACHE + "/npy"
CEN = json.load(open(WORK + "/centers.json")) if os.path.exists(WORK + "/centers.json") else {}
for d in (AUD, NPY): os.makedirs(d, exist_ok=True)
P = json.load(open(WORK + "/plan.json")); SR = 48000
SUF = "_" + TAG

def clip_audio(c):
    """dialogue clean-up once per clip: rumble cut, light denoise, compression, -16 LUFS"""
    f = f"{AUD}/{c}{'_raw' if RAW_AUDIO else ''}.wav"
    if not os.path.exists(f) and RAW_AUDIO:          # untouched: decode only
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src_audio(c), "-vn", "-ac", "2", "-ar", str(SR),
                        "-c:a", "pcm_s16le", f], check=True)
    if not os.path.exists(f):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src_audio(c), "-vn", "-ac", "2", "-ar", str(SR), "-af",
                        "highpass=f=85,lowpass=f=15000,afftdn=nr=8:nf=-40,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2,"
                        "loudnorm=I=-16:TP=-1.5:LRA=9", "-c:a", "pcm_s16le", f], check=True)
    w = wave.open(f)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768

def zoom_vf(s):
    z, cx, cy = s["z"], s["cx"], s["cy"]
    zp = lambda e: f"zoompan=z='{e}':x='(iw-iw/zoom)*{cx}':y='(ih-ih/zoom)*{cy}':d=1:s={RW}x{RH}:fps={FPS_STR}"
    if z in ("n", "w"): return f"scale={RW}:{RH}:flags=lanczos" if (PREVIEW or SHORT) else None
    if z in ("p", "pp", "m", "t"):
        k = {"p": 1.12, "pp": 1.25, "m": 1.15, "t": 1.32}[z]
        return f"crop=trunc(iw/{k}/2)*2:trunc(ih/{k}/2)*2:(iw-iw/{k})*{cx}:(ih-ih/{k})*{cy},scale={RW}:{RH}:flags=lanczos"
    if z == "push": return zp(f"1+0.07*on/{max(1, s['n'])}")
    if z.startswith("snap@"):
        T = float(z[5:]) / s["sp"] * FPS
        return zp(f"if(lt(on,{T:.1f}),1.0,1.0+0.3*min(1,(on-{T:.1f})/4))")
    raise ValueError(z)

def trans_vf(s, n):
    """zoom-blur transition: 6 frames zooming in from 1.3x (tin) / out to 1.3x (tout), blurred at the seam"""
    tin, tout = s.get("tin"), s.get("tout")
    if not (tin or tout): return []
    L = 6; parts = []
    if tin: parts.append(f"0.3*pow(max(0,1-on/{L}),2)")
    if tout: parts.append(f"0.3*pow(max(0,(on-{n - L})/{L}),2)")
    z = "1+" + "+".join(parts)
    out = [] if (PREVIEW or SHORT or zoom_vf(s)) else [f"scale={RW}:{RH}"]
    out.append(f"zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={RW}x{RH}:fps={FPS_STR}")
    sig = max(2, round(RW / 1280 * 7)); en = []
    if tin: en.append("lt(n,3)")
    if tout: en.append(f"gte(n,{n - 3})")
    out.append(f"gblur=sigma={sig}:steps=2:enable='{'+'.join(en)}'")
    return out

def render(i):
    s = P["segs"][i]; out = f"{OUT}/s{i:03d}.mov"; sigf = out[:-4] + ".sig"
    sig = json.dumps({**{k: s.get(k) for k in ("c", "a", "b", "n", "z", "sp", "vo", "g", "au", "cx", "cy", "rx", "ov", "tin", "tout")}, "fps": FPS_STR, "raw_audio": RAW_AUDIO}, sort_keys=True)
    npy = f"{NPY}/s{i:03d}{SUF}.npy"
    if all(map(os.path.exists, (out, sigf, npy))) and open(sigf).read() == sig: return i, "skip"
    n = s["n"]; v0 = s["a"] + s["vo"]; vf = []; vc = s["c"]
    if s.get("ov"): vc, v0 = s["ov"]                # voice-over: picture from another clip
    if s["sp"] != 1.0: vf += [f"setpts=(PTS-STARTPTS)/{s['sp']}", f"fps={FPS_STR}"]
    if SHORT:   # 9:16 column centred on the speaker (no-op for footage that is already vertical)
        rx = s.get("rx") if s.get("rx") is not None else CEN.get(vc, 0.5)
        vf.append(f"crop=trunc(min(iw\\,ih*9/16)/2)*2:ih:max(0\\,min(iw-ow\\,{rx}*iw-ow/2)):0")
    zv = zoom_vf(s)
    if zv: vf.append(zv)
    vf.append(grades.chain(s["g"]))
    vf += trans_vf(s, n)
    vf += ["tpad=stop=8:stop_mode=clone", "format=yuv420p"]   # tpad: never a frame short
    tmpv = out[:-4] + "_v.mp4"
    q = ("22", "24", "26") if PREVIEW else ("17", "19", "21")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-hwaccel", "auto", "-ss", f"{v0:.3f}", "-i", src_video(vc),
                        "-t", f"{n / FPS * s['sp'] + 0.5:.3f}", "-map", "0:v:0", "-vf", ",".join(vf), "-frames:v", str(n),
                        "-r", FPS_STR, *enc.quality_args(int(q[0])), "-an", tmpv], capture_output=True, text=True)
    if r.returncode: return i, "VIDEO FAIL " + r.stderr[-400:]
    ns = int(round(n / FPS * SR))
    if s["au"] == "none":
        a = np.zeros((ns, 2), np.float32)
    else:
        A = clip_audio(s["c"]); st = int(s["a"] * SR)
        if s["sp"] != 1.0: a = A[(st + np.arange(ns) * s["sp"]).astype(int).clip(0, len(A) - 1)]
        else:
            a = A[st:st + ns]
            if len(a) < ns: a = np.vstack([a, np.zeros((ns - len(a), 2), np.float32)])
        a = a * (0.55 if s["au"] == "amb" else 1.0)
        f = int(0.008 * SR); ramp = np.linspace(0, 1, f)[:, None]; a[:f] *= ramp; a[-f:] *= ramp[::-1]
    np.save(npy, a.astype(np.float32))
    wf = out[:-4] + "_a.wav"
    with wave.open(wf, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmpv, "-i", wf, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "pcm_s16le", out], capture_output=True, text=True)
    os.remove(tmpv); os.remove(wf)
    if r.returncode: return i, "MUX FAIL " + r.stderr[-300:]
    open(sigf, "w").write(sig); return i, "ok"

if __name__ == "__main__":
    ids = [int(x) for x in sys.argv[1:]] or list(range(len(P["segs"])))
    for c in sorted({P["segs"][i]["c"] for i in ids if P["segs"][i]["au"] != "none"}): clip_audio(c)
    bad = 0
    with ThreadPoolExecutor(3 if not PREVIEW else 6) as ex:
        for i, msg in ex.map(render, ids):
            if msg not in ("ok", "skip"): bad += 1
            print(i, msg, flush=True)
    print("RENDER DONE", "with errors" if bad else "")

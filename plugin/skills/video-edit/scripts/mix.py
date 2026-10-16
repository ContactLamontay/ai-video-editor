# Audio: dialogue (from rendered cuts) + music cues ducked under speech + SFX -> loudness-normalised master.
#   PREVIEW=1 python mix.py  /  python mix.py   (uses the matching render's dialogue)
import json, os, subprocess, wave
import numpy as np
from common import WORK, CACHE, FPS, TAG, RAW_AUDIO
P = json.load(open(WORK + "/plan.json")); SR = 48000; SUF = "_" + TAG
N = int(round(P["total"] / FPS * SR))

def load(f):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
def save(f, a):
    with wave.open(f, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
db = lambda x: 10 ** (x / 20)

dia = np.zeros((N, 2), np.float32)
for i, s in enumerate(P["segs"]):
    a = np.load(f"{CACHE}/npy/s{i:03d}{SUF}.npy"); st = int(round(s["rec"] / FPS * SR)); dia[st:st + len(a)] += a[:N - st]

# speech envelope -> ducking (~60 ms attack, ~450 ms release)
hop = 480; m = N // hop
rms = np.sqrt((dia[:m * hop].mean(1).reshape(m, hop) ** 2).mean(1) + 1e-12)
speech = (20 * np.log10(rms) > -40).astype(np.float32); env = np.zeros_like(speech); g = 0.0
att, rel = 1 - np.exp(-1 / 6), 1 - np.exp(-1 / 45)
for k in range(m): g += (speech[k] - g) * (att if speech[k] > g else rel); env[k] = g
env = np.pad(np.repeat(env, hop), (0, N - m * hop), mode="edge")

music = np.zeros((N, 2), np.float32)
for c in P["cues"]:
    src = load(c["f"]); t0, t1 = int(c["tl0"] * SR), min(N, int(c["tl1"] * SR)); L = t1 - t0
    out = np.zeros((L, 2), np.float32); pos, cur = 0, int(round(c["file0"] * SR))
    while pos < L:
        if cur < 0: k = min(-cur, L - pos); pos += k; cur += k; continue
        k = min(len(src) - cur, L - pos)
        if k <= 0: cur = int(8 * SR); continue            # loop (skipping the intro) if the cue outlasts the song
        out[pos:pos + k] += src[cur:cur + k]; pos += k; cur += k
    fi, fo = int(c["fi"] * SR), int(c["fo"] * SR)
    if c["file0"] >= 0: out[:fi] *= np.linspace(0, 1, fi)[:, None]
    out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    music[t0:t1] += out * db(c["db"]) * db(-c["duck"] * env[t0:t1])[:, None]

sfx = np.zeros((N, 2), np.float32)
for e in (e for e in P["events"] if e["type"] == "sfx"):
    a = load(e["f"])
    if e.get("trim"): a = a[int(e["trim"][0] * SR):int(e["trim"][1] * SR)]
    a = a[:int(6 * SR)]; f = int(0.25 * SR)
    if len(a) > f: a[-f:] *= np.linspace(1, 0, f)[:, None]
    a = a / (np.abs(a).max() + 1e-9) * db(e["db"]); st = int(e["tl"] * SR); a = a[:N - st]; sfx[st:st + len(a)] += a

save(CACHE + "/mix_raw.wav", dia + music + sfx)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", CACHE + "/mix_raw.wav"]
               + ([] if RAW_AUDIO else ["-af", "loudnorm=I=-14:TP=-1.2:LRA=11,alimiter=limit=0.89"])
               + ["-ar", str(SR), "-c:a", "pcm_s16le", CACHE + "/master_mix.wav"], check=True)
print("mix done", round(N / SR, 1), "s ->", CACHE + "/master_mix.wav")

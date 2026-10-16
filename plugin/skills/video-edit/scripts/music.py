# Tempo, beat period/phase and drop times for music tracks, so montage cuts land on the beat.
#   python music.py                      all tracks in CONTENT/Music (quick survey + energy profile)
#   python music.py "Invincible" "Feeling Alright"   only matching tracks, with refined drops
import sys, glob, os, subprocess, numpy as np
from common import MUSIC

def load(f, sr=22050):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.float32), sr

def analyse(f):
    a, sr = load(f); hop = 256; fps = sr / hop; n = len(a) // hop
    e = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))
    lp = np.convolve(a, np.ones(40) / 40, "same")[:n * hop].reshape(n, hop); el = np.sqrt((lp ** 2).mean(1))
    on = np.maximum(np.diff(np.log(e + 1e-5)), 0)
    seg = on[:int(fps * 90)] - on[:int(fps * 90)].mean(); ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70); L = lo + np.argmax(ac[lo:hi])
    y0, y1, y2 = ac[L - 1], ac[L], ac[L + 1]; period = (L + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) / fps
    ph = np.arange(0, period, 1 / fps)
    score = [on[np.round(((np.arange(0, len(on) / fps - period, period) + p) * fps)).astype(int)].sum() for p in ph]
    phase = ph[int(np.argmax(score))]
    # drops: biggest 1 s rises in low-band energy, refined to the sharpest onset nearby
    k = int(fps); sm = np.convolve(el, np.ones(k) / k, "same"); jump = sm[k:] - sm[:-k]
    onl = np.maximum(np.diff(np.log(el + 1e-5)), 0); drops = []
    for i in np.argsort(jump)[::-1]:
        t = (i + k / 2) / fps
        if all(abs(t - d) > 8 for d in drops):
            i0, i1 = max(0, int((t - 1) * fps)), min(len(onl), int((t + 1) * fps))
            if i1 <= i0: continue
            drops.append(round((i0 + np.argmax(onl[i0:i1])) / fps, 2))
        if len(drops) == 4: break
    w = int(2 * fps); prof = "".join(" .:-=+*#%@"[min(9, max(0, int((20 * np.log10(e[j:j + w].mean() + 1e-6) + 40) / 3.5)))] for j in range(0, n, w))
    return len(a) / sr, 60 / period, period, phase, sorted(drops), prof

if __name__ == "__main__":
    files = sorted(glob.glob(MUSIC + "*.mp3") + glob.glob(MUSIC + "*.wav"))
    if sys.argv[1:]: files = [f for f in files if any(q.lower() in os.path.basename(f).lower() for q in sys.argv[1:])]
    for f in files:
        L, bpm, per, ph, drops, prof = analyse(f)
        print(f"{os.path.basename(f)[:60]}\n   len={L:.0f}s bpm={bpm:.1f} period={per:.4f} phase={ph:.3f} drops={drops}\n   energy/2s: {prof}")

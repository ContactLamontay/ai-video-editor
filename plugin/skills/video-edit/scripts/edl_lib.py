# Cut-list engine. A vlog's edl.py does `from edl_lib import *`, sets GRADE, lists cuts/captions/sfx/music
# in story order, then calls build(). Output: WORK/plan.json (consumed by render/captions/mix/master).
#
#   T(clip, a, b, ...)   talk cut. a/b are rough word times; snapped to word edges from the ElevenLabs
#                        transcript, and any flagged word (slurs etc.) inside is cut out automatically.
#   V(clip, a, b=None, beats=None, period=None, sp=1.0, ...)  b-roll / montage shot. With beats+period the
#                        length is n beats and cuts are placed on the exact beat grid (no drift).
#   cap(clip, t, dur, kind, text)  caption anchored to a source moment. kinds: stamp, cap, claude, big, sub, card
#   sfx(clip, t, file, db)         sound effect anchored to a source moment (file name inside Sound FX/)
#   cue(start, end, file, sync=(segname, file_time) | file_t=..., db, duck)  music cue between named cuts
#                        ("name" = start of that cut, "name>" = its end). sync puts file_time (a drop) at the
#                        start of segname.
# over=(clip, t) on T(): voice-over - the talk audio/captions play over b-roll picture from that clip starting at t
#                        (jump-cut parts advance through the b-roll in step). g= picks the b-roll's grade.
# rx (shorts only): horizontal centre 0..1 of the 9:16 crop on landscape footage; default = auto speaker centre.
# tin="zoom" on T()/V(): section transition - the previous cut zooms/blurs out, this one zooms/blurs in, with a whoosh
#                        (set TRANSITION_SFX / TRANSITION_DB in edl.py; None = silent).
# Zoom codes (z): n none, p 1.12 punch, pp 1.25 punch, push slow 7% push-in, snap@T comedy zoom at T s into the cut.
# Shorts framings (auto-cycled when z is omitted): w wide 1.0, m medium 1.15, t tight 1.32.
#   emph("word", ..., style="serif"|"green"|"red") accents those words in the shorts captions.
# Events (cap/sfx) bind to the most recent cut of that clip, so reusing a line in the hook is safe.
import json, os, re
from common import WORK, MUSIC, SFX, FPS, SHORT

TR = json.load(open(WORK + "/t_el.json"))
WORDS = {k: [w for s in v for w in s["w"] if not w[2].strip().startswith("(")] for k, v in TR.items()}
# words that must never make the cut (slurs). Extend as needed.
BAD = re.compile(r"(nigg\w*|niga\w*|nigs?|neeg\w*|retard\w*|fag\w*|rape\w*|raped|tranny|spic|chink\w*|kike)")
def is_bad(w): return bool(BAD.fullmatch(w.lower().strip(" .,!?'\"-")))

GRADE = {}          # clip -> look ("home", "out", "car", "gym", "eve"); set in edl.py
DEFAULT_GRADE = "home"
S, EV, CUES, MARK, REMOVED, EMPH = [], [], [], {}, [], {}
PAD0, PAD1 = (0.05, 0.09) if SHORT else (0.08, 0.14)   # air before/after a kept phrase
TRANSITION_SFX = None   # e.g. "whoosh.mp3" from the SFX folder; TRANSITION_DB = -13
GAP = 0.35                                            # shorts: any pause longer than this inside a cut is removed

def _g(c): return GRADE.get(c, DEFAULT_GRADE)

def snap(c, a, b):
    w = WORDS.get(c, [])
    first = [x for x in w if x[0] >= a - 0.25]
    last = [x for x in w if x[0] <= b + 0.05]
    if not first or not last: return a, b
    i0, i1 = w.index(first[0]), w.index(last[-1])
    # keep going through words that are clearly part of the same phrase (avoids clipping the last word)
    while i1 + 1 < len(w) and w[i1 + 1][0] <= b + 0.4 and w[i1 + 1][0] - w[i1][1] < 0.25 and not is_bad(w[i1 + 1][2]):
        i1 += 1
    s = w[i0][0] - PAD0
    if i0 > 0: s = max(s, w[i0 - 1][1] + 0.03)
    e = w[i1][1] + PAD1
    if i1 + 1 < len(w): e = min(e, w[i1 + 1][0] - 0.04)
    return round(max(0, s), 3), round(e, 3)

def T(c, a, b, z=None, au="d", vo=0.0, cx=0.5, cy=0.42, name=None, hard_start=None, hard_end=None, rx=None, over=None, g=None, tin=None):
    s, e = snap(c, a, b)
    if hard_end: e = min(e, hard_end)
    if hard_start: s = max(s, hard_start)
    w = WORDS.get(c, []); parts = [[s, e]]
    for i, x in enumerate(w):
        if not is_bad(x[2]) or x[1] <= s or x[0] >= e: continue
        pe = w[i - 1][1] if i > 0 else 0; nx = w[i + 1][0] if i + 1 < len(w) else x[1] + 1
        cut0 = max(pe + 0.06, x[0] - 0.04) if pe < x[0] else x[0] - 0.02
        cut1 = min(nx - 0.05, x[1] + 0.05) if nx > x[1] else x[1] + 0.02
        cur = parts[-1]; parts.append([cut1, cur[1]]); cur[1] = cut0
        REMOVED.append((c, x[0], x[2].strip()))
    if SHORT:   # jump-cut out every pause inside the phrase (dead space is the #1 thing in short-form)
        out = []
        for ps, pe_ in parts:
            ws = [x for x in w if x[0] >= ps - 0.01 and x[1] <= pe_ + 0.01]
            cur = ps
            for x, y in zip(ws, ws[1:]):
                if y[0] - x[1] > GAP:
                    out.append([cur, min(x[1] + PAD1, y[0] - 0.05)]); cur = max(y[0] - PAD0, x[1] + 0.05)
            out.append([cur, pe_])
        parts = out
    parts = [p for p in parts if p[1] - p[0] >= (0.18 if SHORT else 0.3)]
    for j, (ps, pe_) in enumerate(parts):
        ov = [over[0], round(over[1] + ps - parts[0][0], 3)] if over else None
        zz = z if j == 0 else (None if SHORT else ("p" if z in (None, "n") else "n"))
        if ov and zz is None: zz = "n"
        S.append(dict(c=c, a=round(ps, 3), b=round(pe_, 3), z=zz, au=au, vo=vo, sp=1.0, cx=cx, cy=cy if not ov else 0.5, rx=rx,
                      kind="talk", g=g or (_g(over[0]) if ov else _g(c)), ov=ov, tin=tin if j == 0 else None))
    if name and parts: MARK[name] = len(S) - len(parts) if not name.endswith("end") else len(S) - 1

def V(c, a, b=None, beats=None, period=None, sp=1.0, z="push", au="none", cx=0.5, cy=0.5, name=None, g=None, rx=None, tin=None):
    assert b is not None or (beats and period), "V needs b or beats+period"
    S.append(dict(c=c, a=a, b=b, beats=beats, period=period, z=z, au=au, vo=0.0, sp=sp, cx=cx, cy=cy, rx=rx, kind="broll", g=g or _g(c), tin=tin))
    if name: MARK[name] = len(S) - 1

def emph(*words, style="serif"):
    """caption accent for these words: "serif" (Georgia bold italic), "green", "red", "yellow" (shorts word captions)"""
    for w in words: EMPH[w.lower()] = style

def cap(c, t, dur, kind, text): EV.append(dict(type="cap", c=c, t=t, dur=dur, kind=kind, text=text, k=len(S)))
def sfx(c, t, f, db=-8.0, trim=None): EV.append(dict(type="sfx", c=c, t=t, f=SFX + f, db=db, trim=trim, k=len(S)))
def cue(start, end, f, sync=None, file_t=0.0, db=-18.0, duck=11.0, fade_in=1.0, fade_out=1.5):
    CUES.append(dict(start=start, end=end, f=MUSIC + f, sync=sync, file_t=file_t, db=db, duck=duck, fi=fade_in, fo=fade_out))

def _at(c, t, k):
    for s in reversed(S[:k]):
        if s["c"] == c and s["a"] - 0.05 <= t <= s["b"] + 0.05:
            return s["rec"] / FPS + (min(max(t, s["a"]), s["b"]) - s["a"]) / s["sp"]
    near = [(min(abs(t - s["a"]), abs(t - s["b"])), s) for s in S[:k] if s["c"] == c]
    if near and min(near, key=lambda x: x[0])[0] <= 0.6:
        s = min(near, key=lambda x: x[0])[1]
        return s["rec"] / FPS + (min(max(t, s["a"]), s["b"]) - s["a"]) / s["sp"]
    print(f"WARN anchor {c}@{t} is not inside any cut - event dropped"); return None

def build(review=False):
    # touching/overlapping cuts from the same clip: no repeated words, no punch-in change mid-word
    for p, n in zip(S, S[1:]):
        same = p["c"] == n["c"] and p["kind"] == n["kind"] == "talk" and p["vo"] == n["vo"] == 0 and p.get("ov") == n.get("ov") is None
        if same and n["a"] - 0.05 < p["b"] and n["a"] > p["a"]: p["b"] = round(n["a"], 3)
        if same and abs(n["a"] - p["b"]) < 0.02 and not str(n["z"]).startswith("snap"):
            n["z"] = "n" if str(p["z"]).startswith("snap") else p["z"]
    # timing (frames); beat runs keep an exact cumulative grid
    rec, anchor = 0, None
    for i, s in enumerate(S):
        if s.get("beats"):
            prev = S[i - 1] if i else None
            if anchor is None or not (prev and prev.get("beats") and prev["period"] == s["period"]):
                anchor = [rec, 0.0]
            anchor[1] += s["beats"] * s["period"]
            n = int(round(anchor[0] / FPS * FPS + anchor[1] * FPS)) - rec
            s["b"] = round(s["a"] + n / FPS * s["sp"], 3)
        else:
            anchor = None; n = int(round((s["b"] - s["a"]) / s["sp"] * FPS))
        s["n"], s["rec"] = n, rec; rec += n
    # shorts: every cut gets a different framing (wide / medium / tight + small sideways shift) - the energy of the style
    if SHORT:
        cycle, k, last = ["m", "t", "w", "t", "m", "w"], 0, None
        for i, s in enumerate(S):
            if s["z"] is None and s["kind"] == "talk":
                while cycle[k % len(cycle)] == last: k += 1
                s["z"] = cycle[k % len(cycle)]; k += 1
                s["cx"] = round(0.5 + (-0.06, 0.0, 0.06)[i % 3], 3)
                if s["cy"] == 0.42: s["cy"] = 0.22    # selfie framing: face sits high, so zoom toward the top
            last = s["z"]
    # vlogs: alternate punch-ins on consecutive talk cuts of the same clip (jump-cut energy)
    prev, flip = None, False
    for s in S:
        if s["z"] is None:
            flip = (not flip) if (s["kind"] == "talk" and prev and prev["c"] == s["c"] and prev["kind"] == "talk") else False
            s["z"] = "p" if flip else "n"
        prev = s
    for p, n in zip(S, S[1:]):        # transitions: the outgoing cut zooms out into the incoming one
        p["tout"] = n.get("tin")
    events = []
    import edl_lib as _me
    for s in S:
        if s.get("tin") and _me.TRANSITION_SFX and s["rec"] > 0:
            events.append(dict(type="sfx", c=s["c"], t=s["a"], f=SFX + _me.TRANSITION_SFX, db=_me.TRANSITION_DB, trim=None, k=0,
                               tl=round(max(0, s["rec"] / FPS - 0.25), 3)))
    for e in EV:
        tl = _at(e["c"], e["t"], e["k"])
        if tl is not None: events.append({**e, "tl": round(tl, 3)})
    def segt(name):
        s = S[MARK[name.rstrip(">")]]; return (s["rec"] + (s["n"] if name.endswith(">") else 0)) / FPS
    cues = []
    for c in CUES:
        st, en = segt(c["start"]), segt(c["end"])
        f0 = c["sync"][1] - (segt(c["sync"][0]) - st) if c["sync"] else c["file_t"]
        cues.append(dict(f=c["f"], tl0=round(st, 3), tl1=round(en, 3), file0=round(f0, 3), db=c["db"], duck=c["duck"], fi=c["fi"], fo=c["fo"]))
    json.dump(dict(fps=FPS, total=rec, segs=S, events=events, cues=cues, emph=EMPH), open(WORK + "/plan.json", "w"), indent=1)
    m, sec = divmod(rec / FPS, 60)
    print(f"cuts={len(S)} runtime={int(m)}:{sec:05.2f} captions={sum(e['type'] == 'cap' for e in events)} sfx={sum(e['type'] == 'sfx' for e in events)} music cues={len(cues)}")
    for c in cues: print(f"  {c['tl0']:7.1f}-{c['tl1']:7.1f}  file@{c['file0']:6.2f}  {os.path.basename(c['f'])[:50]}")
    if review or os.environ.get("REVIEW"):
        for i, x in enumerate(S):
            txt = " ".join(w[2].strip() for w in WORDS.get(x["c"], []) if x["a"] <= w[0] < x["b"]) if x["kind"] == "talk" else f"[b-roll {x['b'] - x['a']:.1f}s src]"
            print(f"{i:3d} {x['rec'] / FPS:6.1f} {x['c']} {x['a']:7.2f}-{x['b']:7.2f} {str(x['z']):10s} {txt}")
    print("REMOVED WORDS:", REMOVED)

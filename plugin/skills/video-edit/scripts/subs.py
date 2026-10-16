# Word captions from ElevenLabs word timings mapped through plan.json -> .ass file burned in by master.py (libass).
# Shorts (default for FORMAT=short), clean UGC look:
#   small clean white Segoe UI Semibold, natural case, 2-4 words per line, centred mid-frame, soft shadow, no outline
#   karaoke; accent words in Georgia Bold Italic (edl: emph("word", "serif")), numbers/money auto green, emph(..., "red").
# Vlogs: set WORDCAPS=1 for the same captions at the bottom of a 16:9 frame.
#   python subs.py   -> WORK/words.ass + WORK/words_timeline.json (word timings in edit time, for the review screen)
import json, os, re, sys
CAPF = "Segoe UI Semibold" if sys.platform == "win32" else "Avenir Next Demi Bold"   # caption font
from common import WORK, FPS, SHORT, FW, FH

T = json.load(open(WORK + "/t_el.json")); P = json.load(open(WORK + "/plan.json"))
from edl_lib import is_bad                          # never caption a word the cut removed
EMPH = {k.lower(): v for k, v in P.get("emph", {}).items()}
COL = {"green": "&H0058E05B&", "red": "&H004B4BFF&", "yellow": "&H0000D4FF&"}   # ASS = &HBBGGRR

words = []
for s in P["segs"]:
    if s["kind"] != "talk" or s["au"] == "none": continue
    t0 = s["rec"] / FPS; t1 = (s["rec"] + s["n"]) / FPS
    for w in (w for seg in T.get(s["c"], []) for w in seg["w"]):
        txt = w[2].strip()
        if txt.startswith("(") or is_bad(txt) or not (s["a"] <= w[0] < s["b"]): continue
        st = t0 + (w[0] - s["a"]) / s["sp"]; en = min(t1, t0 + (w[1] - s["a"]) / s["sp"])
        if en > st: words.append({"text": txt, "start": round(st, 3), "end": round(en, 3)})
json.dump(words, open(WORK + "/words_timeline.json", "w"), indent=0)

def bare(t): return re.sub(r"[{}\\]", "", t).strip(",;:.\"'").replace("...", "")
def style(t):
    k = bare(t).lower().strip("?!")
    if k in EMPH: return EMPH[k]
    if re.search(r"\d", t) or t.startswith("$"): return "green"
    return None
def fmt(t):
    b = bare(t); st = style(t)
    if st == "serif": return "{\\fnGeorgia\\b1\\i1\\fscx108\\fscy108}" + b + "{\\fn" + CAPF + "\\b0\\i0\\fscx100\\fscy100}"
    if st in COL: return f"{{\\c{COL[st]}}}{b}{{\\c&H00FFFFFF&}}"
    return b

MAXW, MAXC = (4, 22) if SHORT else (5, 32)
chunks, cur = [], []
for w in words:
    long_ = sum(len(x["text"]) + 1 for x in cur) + len(w["text"]) > MAXC
    if cur and (len(cur) == MAXW or long_ or w["start"] - cur[-1]["end"] > 0.3 or re.search(r"[.?!,]$", cur[-1]["text"])):
        chunks.append(cur); cur = []
    cur.append(w)
if cur: chunks.append(cur)

def ts(t):
    h, r = divmod(max(0.0, t), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

ev = []
pos = f"{{\\pos({FW // 2},{int(FH * 0.56)})}}" if SHORT else ""
for ci, ch in enumerate(chunks):
    a = ch[0]["start"]; b = min(chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else 1e9, ch[-1]["end"] + 0.3)
    line = " ".join(fmt(x["text"]) for x in ch)
    ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{pos}{{\\fad(40,0)}}{line}")

size, align, margin = (66, 5, 0) if SHORT else (110, 2, 170)
head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {FW}
PlayResY: {FH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{CAPF},{size},&H00FFFFFF,&H00FFFFFF,&H50000000,&H78000000,0,0,0,0,100,100,0,0,1,1.2,2.5,{align},60,60,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(WORK + "/words.ass", "w", encoding="utf8").write(head + "\n".join(ev) + "\n")
print(f"words={len(words)} lines={len(chunks)} -> {WORK}/words.ass")

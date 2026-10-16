# Print word-level timings so cut boundaries can be picked precisely.
#   python words.py 0047            whole clip
#   python words.py 0047:5-25 0048  time window
import json, sys
from common import WORK
T = json.load(open(WORK + "/t_el.json"))
for arg in sys.argv[1:]:
    k, _, rng = arg.partition(":")
    lo, hi = (map(float, rng.split("-")) if rng else (0, 1e9))
    ws = [w for s in T.get(k, []) for w in s["w"] if lo <= w[0] <= hi]
    print(f"== {k}: " + " ".join(f"{w[2].strip()}@{w[0]:.2f}-{w[1]:.2f}" for w in ws))

# per-location looks: punchy, clean, slightly cinematic
COMMON = "unsharp=5:5:0.45:5:5:0.0,vignette=angle=PI/7.5:mode=forward"
G = {
 "home": "eq=contrast=1.07:saturation=1.10:gamma=0.98,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.03,curves=all='0/0.02 0.25/0.22 0.75/0.79 1/0.98'",
 "out":  "eq=contrast=1.10:saturation=1.28:gamma=0.97,colorbalance=rs=-0.04:gs=0.0:bs=0.05:rh=0.04:gh=0.01:bh=-0.04,curves=all='0/0.02 0.25/0.21 0.75/0.80 1/0.97'",
 "car":  "eq=contrast=1.08:saturation=1.15:gamma=0.98,colorbalance=bs=0.03:rh=0.02:bh=-0.02,curves=all='0/0.02 0.25/0.22 0.75/0.79 1/0.98'",
 "gym":  "hqdn3d=1.5:1.5:4:4,eq=contrast=1.14:saturation=1.08:gamma=1.22:brightness=0.015,colorbalance=rs=-0.04:bs=0.06:rh=0.05:bh=-0.03,curves=all='0/0.03 0.25/0.22 0.75/0.80 1/0.97'",
 "eve":  "eq=contrast=1.08:saturation=1.02:gamma=1.04,colorbalance=rs=-0.03:bs=0.03:rm=-0.03:bm=0.02:rh=-0.02:bh=0.02,curves=all='0/0.02 0.25/0.22 0.75/0.79 1/0.98'",
}
def chain(g): return G[g] + "," + COMMON

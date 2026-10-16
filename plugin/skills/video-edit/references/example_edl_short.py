# 9:16 UGC ad, worked example. Copy the patterns, not the times - clip names and times here are illustrative.
# Project folder holds: IMG_2041.mov (creator talking to camera, landscape) and two B-roll clips
# (product_closeup.mp4 = the product in use, problem_shot.mp4 = the "before" moment).
# Prep first with FORMAT=short, then run with VLOG_DIR set and PYTHONPATH = the skill's scripts/ folder:
#   REVIEW=1 python "<project>/Edit/_work/edl.py"
# Pick whole sentences: in short mode every pause inside them is cut and every cut gets a new framing automatically.
from edl_lib import *

GRADE.update({"IMG_2041": "home", "product_closeup": "home", "problem_shot": "eve"})

T("IMG_2041", 41.20, 42.90, name="start")                 # hook (0-2 s): call out the audience
T("IMG_2041", 3.10, 5.60, over=("problem_shot", 1.0))     # pain point (2-3 s), voice over the "before" shot
cap("IMG_2041", 3.4, 2.2, "chip", "Old way > Problem > Product")
T("IMG_2041", 6.00, 11.50, over=("product_closeup", 2.0)) # show the product (4-6 s): voice-over on the close-up
T("IMG_2041", 12.40, 17.75)                               # USPs, on camera
T("IMG_2041", 30.00, 33.40, name="end")                   # CTA: the current offer
emph("finally", style="serif")                            # accent words in the captions
emph("never", style="red")
cue("start", "end>", "upbeat-bed.mp3", file_t=0.0, db=-24, fade_out=0.8)
build(review=True)

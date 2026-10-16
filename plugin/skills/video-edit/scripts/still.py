# Spot-check frames of the latest preview (or the final) as one contact image (cheap visual QA).
#   PREVIEW=1 python still.py out.jpg 3.0 20.5 100 381      (edit-time seconds)
import sys, glob, os, subprocess
from PIL import Image
from common import ED, NAME, FINISHED, PREVIEW, SHORT
if PREVIEW:
    f = max(glob.glob(f"{ED}/Previews/{NAME}_preview_r*.mp4"), key=os.path.getmtime)
else:
    f = f"{FINISHED}/{NAME} - {'Short' if SHORT else 'Final'}.mp4"
tw, th = (270, 480) if SHORT else (640, 360)
cols = 4 if SHORT else 2
ims = []
for t in sys.argv[2:]:
    p = sys.argv[1] + f".{t}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", f, "-frames:v", "1", "-vf", f"scale={tw}:{th}", p], check=True)
    ims.append(Image.open(p))
sheet = Image.new("RGB", (tw * cols, th * ((len(ims) + cols - 1) // cols)))
for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
sheet.save(sys.argv[1], quality=85); print(sys.argv[1], "from", f)

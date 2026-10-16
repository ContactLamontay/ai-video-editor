# Picks the fastest H.264 encoder this computer has: NVIDIA (nvenc), AMD (amf), Intel (qsv), Apple (videotoolbox),
# else software x264. Each candidate is test-encoded once per run. VIDEO_ENCODER=libx264 forces one.
import functools, os, subprocess, sys

CANDIDATES = ["h264_videotoolbox"] if sys.platform == "darwin" else ["h264_nvenc", "h264_amf", "h264_qsv"]

@functools.lru_cache(None)
def name():
    forced = os.environ.get("VIDEO_ENCODER")
    if forced: return forced
    for c in CANDIDATES:
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=640x360:d=0.2", "-c:v", c, "-f", "null", "-"],
                           capture_output=True)
        if r.returncode == 0: return c
    return "libx264"

def quality_args(q):
    """constant-quality encode; q is x264-CRF-like (17 = near-lossless master, 26 = small preview)"""
    e = name()
    if e == "h264_nvenc": return ["-c:v", e, "-preset", "p5", "-rc", "vbr", "-cq", str(q), "-b:v", "0"]
    if e == "h264_amf": return ["-c:v", e, "-quality", "quality", "-rc", "cqp", "-qp_i", str(q), "-qp_p", str(q + 2), "-qp_b", str(q + 4)]
    if e == "h264_qsv": return ["-c:v", e, "-global_quality", str(q)]
    if e == "h264_videotoolbox": return ["-c:v", e, "-q:v", str(int(100 - q * 1.5))]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", str(q)]

def bitrate_args(b, maxrate):
    """target-bitrate encode for the delivered file"""
    e = name()
    if e == "h264_amf": return ["-c:v", e, "-quality", "quality", "-rc", "vbr_peak", "-b:v", b, "-maxrate", maxrate]
    if e == "libx264": return ["-c:v", e, "-preset", "medium", "-b:v", b, "-maxrate", maxrate, "-bufsize", maxrate]
    return ["-c:v", e, "-b:v", b, "-maxrate", maxrate, "-bufsize", maxrate]

if __name__ == "__main__":
    print(name())

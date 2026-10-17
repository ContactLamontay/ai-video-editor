"""Edit Review - a local review screen for video edits.

Serves one project folder on 127.0.0.1 only. Watch a preview, press N to leave a note at the exact
moment, flip to the original footage, then copy the notes for the AI or approve the cut.

Sidecar files, all next to the video (e.g. Previews/Ad1_v1.mp4):
  Ad1_v1.review.json  written by this app: notes + status (the AI reads it)
  Ad1_v1.edits.json   optional, written by the AI: timeline tracks/segments (+ source clip per segment)
  Ad1_v1.words.json   optional, written by the AI: word timings [{"text","start","end"}] or [[start,end,text]]

Usage:  python server.py "C:\\path\\to\\project" [--video Previews\\Ad1_v1.mp4] [--port 8765] [--no-open]
The always-on "hub" is this server rooted at the projects folder (projects_dir) on port 8770 (see open_review.py),
so every edited video can be picked from one tab.
Stdlib only; ffmpeg on PATH is used to make browser-playable proxies of original footage.
"""
import argparse, hashlib, json, mimetypes, os, re, shutil, subprocess, sys, threading, time, urllib.parse, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
SKIP_DIRS = {".review_cache", "node_modules", ".git", "__pycache__"}
MIME = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm", ".mkv": "video/x-matroska",
        ".lrf": "video/mp4", ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml"}
ROOT = "."
_proxy_locks, _proxy_guard = {}, threading.Lock()
# open_review.py asks an already-open tab to switch videos instead of opening a new one
STATE = {"last_ping": 0.0, "focus": None}


def safe_path(rel):
    """Resolve a project-relative path, refusing anything outside the project root."""
    p = os.path.realpath(os.path.join(ROOT, urllib.parse.unquote(rel).replace("/", os.sep)))
    if os.path.commonpath([p, ROOT]) != ROOT:
        raise PermissionError(rel)
    return p


def rel_of(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sidecar(video_path, kind):
    return os.path.splitext(video_path)[0] + f".{kind}.json"


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def probe(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,width,height,r_frame_rate:format=duration",
                              "-of", "json", path], capture_output=True, text=True, timeout=30).stdout
        j = json.loads(out); s = (j.get("streams") or [{}])[0]
        num, den = (s.get("r_frame_rate") or "30/1").split("/")
        return {"codec": s.get("codec_name"), "width": s.get("width"), "height": s.get("height"),
                "fps": round(float(num) / float(den or 1), 3), "duration": float(j.get("format", {}).get("duration") or 0)}
    except Exception:
        return {}


def project_of(p):
    """Project label for a video: its folder relative to ROOT, minus trailing Previews/Edit folders."""
    parts = rel_of(os.path.dirname(p)).split("/")
    while len(parts) > 1 and parts[-1].lower() in ("previews", "edit"):
        parts.pop()
    return "/".join(parts) if parts != ["."] else os.path.basename(ROOT)


def list_videos():
    """Edited videos only: previews the AI made (they have an edit list or review file) and anything in a Finished folder."""
    vids = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        finished = "finished" in rel_of(d).lower().split("/")
        for f in files:
            if os.path.splitext(f)[1].lower() in VIDEO_EXT:
                p = os.path.join(d, f)
                has_review, has_edits = os.path.exists(sidecar(p, "review")), os.path.exists(sidecar(p, "edits"))
                if not (has_review or has_edits or finished):
                    continue
                rv = read_json(sidecar(p, "review"), {}) or {}
                vids.append({"path": rel_of(p), "project": project_of(p), "finished": finished, "mtime": os.path.getmtime(p), "size": os.path.getsize(p),
                             "has_review": has_review, "has_edits": has_edits,
                             "status": rv.get("status"), "open_notes": sum(1 for n in rv.get("notes", []) if n.get("status") != "done")})
    vids.sort(key=lambda v: -v["mtime"])
    return vids[:500]


def ancestors(video_rel):
    """The video's folder and each parent up to ROOT (nearest first)."""
    d = os.path.dirname(safe_path(video_rel))
    while True:
        yield d
        if d == ROOT or os.path.dirname(d) == d:
            return
        d = os.path.dirname(d)


def locate(source, video_rel):
    """Find a segment's source clip: as a path relative to the video's project (any parent folder), else by file name, nearest folder first."""
    rel = source.replace("\\", "/")
    for d in ancestors(video_rel):
        p = os.path.realpath(os.path.join(d, rel.replace("/", os.sep)))
        if os.path.isfile(p) and os.path.commonpath([p, ROOT]) == ROOT:
            return p
    name, searched = rel.split("/")[-1].lower(), set()
    for top in ancestors(video_rel):
        for d, dirs, files in os.walk(top):
            if d in searched:
                dirs[:] = []; continue
            searched.add(d)
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            for f in files:
                if f.lower() == name:
                    return os.path.join(d, f)
    return None


def make_proxy(src):
    """Browser-safe H.264 proxy of an original clip (HEVC 10-bit etc.), cached under .review_cache."""
    st = os.stat(src)
    key = hashlib.sha1(f"{src}|{st.st_size}|{st.st_mtime}".encode()).hexdigest()[:16]
    cache = os.path.join(ROOT, ".review_cache"); os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, key + ".mp4")
    with _proxy_guard:
        lock = _proxy_locks.setdefault(key, threading.Lock())
    with lock:
        if not os.path.exists(out):
            tmp = out + ".part.mp4"
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0?",
                   "-vf", "scale='if(gt(iw,ih),-2,540)':'if(gt(iw,ih),540,-2)',format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
                   "-crf", "26", "-g", "15", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", tmp]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr[-400:])
            os.replace(tmp, out)
    return out


def claude_listening(video_rel=None):
    """True if a wait_for_review.py heartbeat is fresh in the video's project (any folder from the video up to ROOT)."""
    dirs = ancestors(video_rel) if video_rel else [ROOT]
    for d in dirs:
        try:
            if time.time() - os.path.getmtime(os.path.join(d, ".review_cache", "claude_listening")) < 8:
                return True
        except OSError:
            pass
    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "EditReview/1.0"

    def log_message(self, fmt, *args):  # keep the console quiet except for errors
        if args and str(args[1])[:1] in "45":
            sys.stderr.write("%s\n" % (fmt % args))

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, mime=None):
        size = os.path.getsize(path)
        mime = mime or MIME.get(os.path.splitext(path)[1].lower()) or mimetypes.guess_type(path)[0] or "application/octet-stream"
        start, end, code = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m and size:
            if m.group(1):
                start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else size - 1
            else:  # suffix range: last N bytes
                start = max(0, size - int(m.group(2))); end = size - 1
            if start >= size:
                self.send_response(416); self.send_header("Content-Range", f"bytes */{size}"); self.end_headers(); return
            end = min(end, size - 1); code = 206
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-store" if mime.startswith(("text/", "application/json")) else "private, max-age=60")
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(path, "rb") as f:
            f.seek(start); left = end - start + 1
            try:
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk); left -= len(chunk)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                pass  # the player seeked away; normal

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                return self.send_file(os.path.join(APP_DIR, "index.html"))
            if u.path == "/api/config":
                return self.send_json({"root": ROOT, "project": os.path.basename(ROOT), "initial": self.server.initial_video})
            if u.path == "/api/listening":  # is an AI session waiting on this review (wait_for_review.py heartbeat)?
                return self.send_json({"listening": claude_listening(q.get("v", [None])[0])})
            if u.path == "/api/ping":  # the open tab checks in every few seconds; also tells it which video to switch to
                STATE["last_ping"] = time.time()
                return self.send_json({"listening": claude_listening(q.get("v", [None])[0]), "focus": STATE["focus"]})
            if u.path == "/api/status":  # for open_review.py: is a tab open right now?
                return self.send_json({"app": "edit-review", "root": ROOT, "tab_open": time.time() - STATE["last_ping"] < 7})
            if u.path == "/api/videos":
                return self.send_json(list_videos())
            if u.path == "/api/review":
                v = safe_path(q["v"][0])
                return self.send_json({"path": rel_of(v), "info": probe(v), "review": read_json(sidecar(v, "review")),
                                       "edits": read_json(sidecar(v, "edits")), "words": read_json(sidecar(v, "words"))})
            if u.path == "/api/locate":  # find a segment's source clip for the Original footage toggle
                p = locate(q["name"][0], q["v"][0])
                return self.send_json({"path": rel_of(p)}) if p else self.send_json({"error": "not found"}, 404)
            if u.path.startswith("/media/"):
                p = safe_path(u.path[len("/media/"):])
                return self.send_file(p) if os.path.isfile(p) else self.send_error(404)
            if u.path.startswith("/proxy/"):
                p = safe_path(u.path[len("/proxy/"):])
                if not os.path.isfile(p):
                    return self.send_error(404)
                return self.send_file(make_proxy(p), "video/mp4")
            self.send_error(404)
        except PermissionError:
            self.send_error(403)
        except (KeyError, IndexError):
            self.send_error(400)
        except Exception as e:  # surface ffmpeg/IO problems to the page
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
            return self.send_error(403)  # only this page may write
        try:
            if u.path == "/api/focus":  # from open_review.py: switch the open tab to this video
                v = safe_path(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")["v"])
                STATE["focus"] = {"v": rel_of(v), "id": time.time()}
                return self.send_json({"ok": True, "focus": STATE["focus"]})
            if u.path == "/api/review":
                v = safe_path(q["v"][0])
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                data["video"] = rel_of(v); data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                write_json_atomic(sidecar(v, "review"), data)
                return self.send_json({"ok": True, "saved": data["updated"], "file": rel_of(sidecar(v, "review"))})
            self.send_error(404)
        except PermissionError:
            self.send_error(403)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)


def main():
    global ROOT
    ap = argparse.ArgumentParser(description="Edit Review - timestamped notes on video edits")
    ap.add_argument("root", nargs="?", default=os.getcwd(), help="project folder to serve")
    ap.add_argument("--video", help="video to open first (path relative to root, or absolute inside it)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true", help="don't open a browser tab")
    ap.add_argument("--exact-port", action="store_true", help="fail if --port is busy instead of trying the next one")
    a = ap.parse_args()
    ROOT = os.path.realpath(a.root)
    initial = None
    if a.video:
        vp = os.path.realpath(a.video if os.path.isabs(a.video) else os.path.join(ROOT, a.video))
        initial = rel_of(vp) if os.path.commonpath([vp, ROOT]) == ROOT and os.path.isfile(vp) else None
    if not shutil.which("ffmpeg"):
        print("note: ffmpeg not on PATH - the Original footage toggle needs it for HEVC clips")
    srv = None
    for port in range(a.port, a.port + (1 if a.exact_port else 20)):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler); break
        except OSError:
            continue
    if not srv:
        sys.exit("no free port")
    srv.daemon_threads = True
    srv.initial_video = initial
    url = f"http://127.0.0.1:{srv.server_port}/" + (f"?v={urllib.parse.quote(initial)}" if initial else "")
    print(f"Edit Review serving {ROOT}\n  {url}\n  (Ctrl+C to stop)", flush=True)
    if not a.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

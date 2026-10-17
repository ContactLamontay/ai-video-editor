"""Open the Edit Review hub - one always-on review screen for every edited video in the projects folder.

  python open_review.py                 open the screen (starts the hub if it isn't running)
  python open_review.py <video>         open the screen on that video; if a tab is already open it just
                                        switches that tab to the video instead of opening a new one
  python open_review.py --serve-only    make sure the hub is running, open nothing (e.g. at login)

<video> can be absolute or relative to the projects folder (projects_dir in ~/.ai-video-editor/config.json).
"""
import json, os, subprocess, sys, time, urllib.parse, urllib.request, webbrowser

APP_DIR = os.path.dirname(os.path.abspath(__file__))
_CFG_F = os.path.join(os.path.expanduser("~"), ".ai-video-editor", "config.json")
_CFG = json.load(open(_CFG_F, encoding="utf-8-sig")) if os.path.exists(_CFG_F) else {}
CONTENT = os.path.realpath(_CFG.get("projects_dir") or os.path.join(os.path.expanduser("~"), "Video Edits"))
os.makedirs(CONTENT, exist_ok=True)
PORT = 8770   # not 8760, so it never collides with a personal review hub on the same machine
BASE = f"http://127.0.0.1:{PORT}"


def get(path, data=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.load(r)


def status():
    try:
        s = get("/api/status")
        return s if s.get("app") == "edit-review" and os.path.realpath(s.get("root", "")) == CONTENT else None
    except Exception:
        return None


def ensure_hub():
    if status():
        return True
    py = sys.executable
    pyw = os.path.join(os.path.dirname(py), "pythonw.exe")  # no console window on Windows
    exe = pyw if os.path.exists(pyw) else py
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    extra = {"creationflags": flags} if os.name == "nt" else {"start_new_session": True}   # outlive this command
    subprocess.Popen([exe, os.path.join(APP_DIR, "server.py"), CONTENT, "--port", str(PORT), "--no-open", "--exact-port"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, **extra)
    for _ in range(40):
        time.sleep(0.25)
        if status():
            return True
    return False


def main():
    args = sys.argv[1:]
    if not ensure_hub():
        sys.exit(f"Edit Review hub didn't start on port {PORT} (is another program using it?)")
    if "--serve-only" in args:
        return
    video = None
    if args:
        p = os.path.realpath(args[0] if os.path.isabs(args[0]) else os.path.join(CONTENT, args[0]))
        if os.path.commonpath([p, CONTENT]) != CONTENT or not os.path.isfile(p):
            sys.exit(f"Not a video inside {CONTENT}: {args[0]}")
        video = os.path.relpath(p, CONTENT).replace(os.sep, "/")
    if status().get("tab_open"):
        if video:
            get("/api/focus", {"v": video})
            print(f"Switched the open Edit Review tab to {video}")
        else:
            print(f"Edit Review is already open: {BASE}/")
        return
    url = BASE + "/" + (f"?v={urllib.parse.quote(video)}" if video else "")
    webbrowser.open(url)
    print(f"Opened {url}")


if __name__ == "__main__":
    main()

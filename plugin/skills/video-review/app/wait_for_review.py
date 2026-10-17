"""Wait for the editor to finish a review round, then print his notes and exit.

The AI runs this in the background right after opening the review screen. When the editor clicks
"Request changes" or "Approve and render final", this exits and prints everything the AI needs,
so the notes reach it without any copy/paste. While it runs, the review screen shows
"AI is listening" (heartbeat file in <project>/.review_cache/).

Usage:  python wait_for_review.py "C:\\path\\to\\project" [--timeout-hours 12]
"""
import argparse, json, os, time

SKIP = {".review_cache", "node_modules", ".git", "__pycache__"}


def review_files(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith(".")]
        for f in files:
            if f.endswith(".review.json"):
                yield os.path.join(d, f)


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def fmt(t):
    m = int(t // 60)
    return f"{m}:{t - m * 60:05.2f}"


def submissions(rv):
    return [h for h in (rv or {}).get("history", []) if h.get("status") in ("changes_requested", "approved")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--timeout-hours", type=float, default=12)
    a = ap.parse_args()
    root = os.path.realpath(a.root)
    beat = os.path.join(root, ".review_cache", "claude_listening")
    os.makedirs(os.path.dirname(beat), exist_ok=True)

    seen = {p: len(submissions(read(p))) for p in review_files(root)}
    deadline = time.time() + a.timeout_hours * 3600
    print(f"Waiting for review in {root} ...", flush=True)
    try:
        while time.time() < deadline:
            with open(beat, "w") as f:
                f.write(str(os.getpid()))
            for p in review_files(root):
                rv = read(p)
                subs = submissions(rv)
                if len(subs) > seen.get(p, 0):
                    time.sleep(1.0)  # let the page's debounced save land, then re-read
                    rv = read(p) or rv
                    report(root, p, rv)
                    return
                seen.setdefault(p, len(subs))
            time.sleep(1.5)
        print("Timed out waiting for review.")
    finally:
        try:
            os.remove(beat)
        except OSError:
            pass


def report(root, path, rv):
    rel = os.path.relpath(path, root)
    status = rv.get("status")
    open_notes = [n for n in rv.get("notes", []) if n.get("status") != "done"]
    general = [n for n in open_notes if n.get("general") or n.get("t") is None]
    timed = sorted((n for n in open_notes if n not in general), key=lambda n: n["t"])
    print(f"REVIEW SUBMITTED: {status}")
    print(f"Video: {rv.get('video')}  (round {rv.get('round', 1)})")
    print(f"Notes file: {rel}")
    if status == "approved":
        print("The editor approved this cut - render the final." + (f" ({len(open_notes)} note(s) still open, see below.)" if open_notes else ""))
    else:
        print(f"The editor requested changes - apply these {len(open_notes)} note(s) and render the next preview round.")
    i = 0
    for n in general:
        i += 1; print(f"{i}. [General - whole video] {n['text']}  (id {n['id']})")
    for n in timed:
        i += 1; seg = f" ({n['seg']})" if n.get("seg") else ""
        print(f"{i}. [{fmt(n['t'])}]{seg} {n['text']}  (id {n['id']})")


if __name__ == "__main__":
    main()

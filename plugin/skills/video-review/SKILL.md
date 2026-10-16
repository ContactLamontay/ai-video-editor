---
name: video-review
description: Review gate for every video edit - render a fast PREVIEW (never the final first), write its edit list and word timings next to it, open it in the local "Edit Review" screen where the editor watches, flips to original footage, and presses N to leave notes at exact timestamps, then read the notes from the .review.json file and apply them. Use whenever an edit is ready to look at, when the editor says "let me see it", "show me a preview", "open the review screen", "I left notes", "check my notes", "apply my notes", or "approved / render the final", and before any final render.
---

# Video review gate

The editor reviews every cut before the final render. The loop:

1. **Render a preview, not the final.** Small and fast: H.264 MP4, short side 540-720 px, same frame rate and length
   as the edit, in `Previews/` inside the project, named `<edit>_preview_r<round>.mp4`. The `video-edit` scripts
   do this and the next step automatically.
2. **Sidecars** next to the preview (same base name), so the review screen can show the edit:
   - `<name>.edits.json` - the timeline (format below). Every picture segment gets a human label and, when it comes
     from a camera clip, `source` (path relative to the project folder) + `src_in` (seconds into that clip). That
     powers the **Original footage** toggle.
   - `<name>.words.json` - word timings of the preview's audio: `[{"text","start","end"}, ...]` in preview time.
3. **Open the review screen** (keeps running in the background). The app is `app/server.py` next to this file:
   ```
   python "<this skill's folder>/app/server.py" "<project folder>" --video "Edit/Previews/<name>.mp4"
   ```
   (`python3` on Mac.) Run it in the background. It prints its URL (default http://127.0.0.1:8765, next free port if
   busy) and opens the browser. Tell the editor the URL and the keys: **N** note, **Space** play, **J/L** +/-5 s,
   **Left/Right** frame, **O** original footage, **[ / ]** jump between notes.
4. **Wait for the editor.** They either paste notes ("Copy notes for the AI" / "Request changes") or say they're
   done. Either way, **read `<name>.review.json`** - it is the source of truth.
5. **Apply the notes.** Each note has `t` (seconds in the preview), `seg` (the segment label under the playhead),
   `text`, and `status` (`open`/`done`). Map `t` through `.edits.json` to the clip/source moment. Work through every
   `open` note; when one is handled, set its `status` to `"done"` and add `"resolution": "<what changed>"` in the same
   file. Then render the next round's preview, carry `round` forward (+1), set `status` back to `"in_review"`, reopen.
6. **Only when `status` is `"approved"`** (the editor clicked **Approve and render final**, or said so) render the
   final at full quality to `output_dir`. Never render the final before approval.

## File formats

`<name>.edits.json` (written by the AI):
```json
{
  "fps": 30,
  "tracks": [
    {"name": "Picture", "kind": "video", "items": [
      {"start": 0.0, "end": 3.17, "label": "01 hook", "source": "IMG_2041.mov", "src_in": 41.2}
    ]},
    {"name": "Graphics", "kind": "graphics", "items": [{"start": 12.47, "end": 14.63, "label": "Flat pillow > Neck ache"}]},
    {"name": "Dialogue", "kind": "audio", "items": [{"start": 0.0, "end": 31.17, "label": "Dialogue mix"}]},
    {"name": "Music", "kind": "music", "items": []}
  ]
}
```
`kind` is one of `video`, `aroll`, `broll`, `graphics`, `captions`, `audio`, `music`, `sfx`, `other` (only colours
the timeline). Times are seconds on the preview. With no `captions` track the screen builds one from `words.json`.

`<name>.review.json` (written by the review screen; the AI may update `status`/`resolution` on notes):
```json
{"version": 1, "status": "in_review | changes_requested | approved", "round": 1,
 "notes": [{"id": "k3j9x2a", "t": 3.24, "seg": "02a hook", "text": "music too loud here", "status": "open", "created": "..."}],
 "history": [{"at": "...", "status": "changes_requested", "notes": 3}], "video": "Edit/Previews/x.mp4", "updated": "..."}
```

## Notes

- The server is stdlib Python, binds 127.0.0.1 only, and only reads/writes inside the project folder. HEVC/10-bit
  camera clips are turned into small H.264 proxies on first use (cached in `<project>/.review_cache/`, safe to delete).
- Don't overwrite a preview the editor has open; render the next round to a new name.
- Apply the brand file (`brand_file` in `~/.ai-video-editor/config.json`) and `video-edit/references/style.md`
  before the editor has to note it.

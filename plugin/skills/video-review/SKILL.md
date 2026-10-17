---
name: video-review
description: Review gate for every video edit - render a fast PREVIEW (never the final first), write its edit list and word timings next to it, open it in the local "Edit Review" hub where the editor watches, flips to original footage, and presses N to leave notes at exact timestamps (G for a general note), then pick up the notes automatically when they click Request changes / Approve, and apply them. Use whenever an edit is ready to look at, when the editor says "let me see it", "show me a preview", "open the review screen", "I left notes", "check my notes", "apply my notes", or "approved / render the final", and before any final render.
---

# Video review gate

The editor reviews every cut before the final render. The app is in `app/` next to this file (`python` on Windows,
`python3` on Mac). The loop:

1. **Render a preview, not the final.** Small and fast: H.264 MP4, short side 540-720 px, same frame rate and length
   as the edit, in `Edit/Previews/` inside the project, named `<edit>_preview_r<round>.mp4`. The `video-edit` scripts
   do this and the next step automatically.
2. **Sidecars** next to the preview (same base name), so the review screen can show the edit:
   - `<name>.edits.json` - the timeline (format below). Every picture segment gets a human label and, when it comes
     from a camera clip, `source` (path relative to the project folder) + `src_in` (seconds into that clip). That
     powers the **Original footage** toggle, and it's what lists the video in the hub's picker.
   - `<name>.words.json` - word timings of the preview's audio: `[{"text","start","end"}, ...]` in preview time.
3. **Open it in the review hub** - one always-on screen for every edited video in `projects_dir`
   (http://127.0.0.1:8770). Run in the foreground (returns in a second):
   ```
   python "<this skill's folder>/app/open_review.py" "<full path to the preview .mp4>"
   ```
   It starts the hub if needed; if the editor already has the tab open, it switches that tab to the new preview
   instead of opening another. The preview must be inside `projects_dir`. Tell the editor the keys: **N** note at
   this moment, **G** general note for the whole video, **Space** play, **J/L** +/-5 s, **Left/Right** frame,
   **O** original footage, **[ / ]** jump between notes. They can open the hub themselves any time
   (`/ai-video-editor:review` in Claude, or "open the review screen").
4. **Listen for the editor's submit.** Right after opening the screen (and after every new round), start the
   listener **in the background** if you can run background commands that notify you when they finish:
   ```
   python "<this skill's folder>/app/wait_for_review.py" "<project folder>"
   ```
   While it runs the screen shows a green "AI is listening" dot. When the editor clicks **Request changes** or
   **Approve and render final**, it exits and prints the status and every open note - start on them right away, no
   copy/paste needed. If you can't run it in the background, skip it: the buttons then copy the notes, and the
   editor pastes them in. Either way, **read `<name>.review.json`** - it is the source of truth.
5. **Apply the notes.** Each note has `t` (seconds in the preview), `seg` (the segment label under the playhead),
   `text`, and `status` (`open`/`done`). **General notes** have `"general": true` and `t: null` - they're about the
   whole video (pacing, music level, vibe), so apply them across the edit. Map timed notes' `t` through
   `.edits.json` to the clip/source moment. Work through every `open` note; when one is handled, set its `status` to
   `"done"` and add `"resolution": "<what changed>"` in the same file. Then render the next round's preview, carry
   `round` forward (+1), set `status` back to `"in_review"`, reopen it, and start the listener again.
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
    {"name": "Graphics", "kind": "graphics", "items": [{"start": 12.47, "end": 14.63, "label": "Old way > Problem"}]},
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
 "notes": [{"id": "k3j9x2a", "t": 3.24, "seg": "02a hook", "text": "music too loud here", "status": "open", "created": "..."},
           {"id": "p8w2m1q", "t": null, "general": true, "text": "a bit faster overall", "status": "open", "created": "..."}],
 "history": [{"at": "...", "status": "changes_requested", "notes": 3}], "video": "Edit/Previews/x.mp4", "updated": "..."}
```

## Notes

- The server is stdlib Python, binds 127.0.0.1 only, and only reads/writes inside `projects_dir`. HEVC/10-bit camera
  clips are turned into small H.264 proxies on first use (cached in `<project>/.review_cache/`, safe to delete).
- Don't overwrite a preview the editor has open; render the next round to a new name.
- Apply the brand file (`brand_file` in `~/.ai-video-editor/config.json`) and `video-edit/references/style.md`
  before the editor has to note it.

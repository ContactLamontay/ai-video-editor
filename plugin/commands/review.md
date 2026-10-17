---
description: Open the Edit Review screen (every edited video, one tab)
---

Open the Edit Review hub, no rendering or edits: run
`python "${CLAUDE_PLUGIN_ROOT}/skills/video-review/app/open_review.py" $ARGUMENTS` (`python3` on Mac) in the foreground.
With no argument it opens the screen; with a video path it opens or switches the tab to that video. If the user names
a video loosely ("the latest pillow ad"), find the newest matching `*_preview_r*.mp4` with an `.edits.json` next to it
inside `projects_dir` (from `~/.ai-video-editor/config.json`). Reply in one line with what happened and the URL
`http://127.0.0.1:8770`.

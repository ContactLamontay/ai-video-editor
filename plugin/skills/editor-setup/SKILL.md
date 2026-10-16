---
name: editor-setup
description: Set up or re-check a computer for the AI video editor (Python, FFmpeg, Google Drive footage folder, brand file, ElevenLabs key). Use when the editor asks to set up, install, "set me up", "is everything working", when ~/.ai-video-editor/config.json is missing, or when an edit script fails because ffmpeg, Python, a package, the footage folder or the key is missing.
---

# Editor setup

Get this computer ready for the AI video editor. Keep it friendly and non-technical: editors aren't developers.

1. **Check first.** If Python works, run the checker in this skill's folder:
   `python "<this skill's folder>/doctor.py"` (`python3` on Mac). If it prints `READY`, tell the editor they're set
   and suggest a first request, like "Edit the testimonial clips from the March shoot into a 20-second Reel". Stop.
2. **Otherwise** explain in one or two plain sentences what's missing, then give them the setup command in its own
   code block. It asks questions (folders, key), so **they run it in a terminal, not you**:
   - Windows (PowerShell):
     `powershell -NoProfile -ExecutionPolicy Bypass -File "<this skill's folder, as a C:\ path>\setup-windows.ps1"`
   - Mac (Terminal): `bash "<this skill's folder>/setup-mac.sh"`
   Use the real absolute path of this skill's folder.
3. **Before they run it** they need:
   - **Google Drive for Desktop** installed and signed in with the company Google account
     (https://www.google.com/drive/download/), so the footage shows up as a folder.
   - The **brand file** (`brand.md`) they were given. Easiest: saved in the footage folder on Drive, where the setup
     finds it by itself.
   - The **ElevenLabs API key** from whoever manages the account. Never ask them to paste the key into chat - the
     script asks for it with hidden typing.
4. **After** they say it finished, run the checker again and help fix any `FAIL` line. Tell them to restart Claude /
   Codex once so new installs are picked up.

The script is safe to re-run: it keeps previous answers as defaults (use this to change folders, the brand file or
the key later).

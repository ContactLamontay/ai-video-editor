---
name: editor-setup
description: Set up or re-check a computer for the AI video editor - installs Python, FFmpeg and Google Drive for Desktop, finds the footage folder in Google Drive by itself, reads the ElevenLabs key from the Drive settings file, checks everything. Use when the user asks to set up, install, "set me up", "is everything working", when ~/.ai-video-editor/config.json is missing or incomplete, or when an edit script fails because ffmpeg, Python, a package, the footage folder or the key is missing.
---

# Editor setup

The person using this is usually a business owner, not a developer: do the work for them, keep messages short and
plain, and never show them paths, JSON or terminal output unless something breaks.

## How it finds everything (nothing to type)
Whoever manages the system has put two files in an **AI video editor** folder at the top of the footage in the
company Google Drive (or loose in the top footage folder):
- `brand.md` - the brand rules. The setup searches Google Drive for it; **the folder above the AI video editor folder
  (or the folder holding brand.md, if it's loose) becomes the footage folder**. Where finished videos go is asked on the first video (the `video-edit` skill).
- `ai-video-editor.json` - `{"elevenlabs_api_key": "...", "music_dir": "...", "sfx_dir": "..."}`
  (folders relative to that folder). Only the key is required.

## Steps
1. **Check first.** Windows: `python "<this skill's folder>/doctor.py"`. Mac: only if `~/.ai-video-editor/bin/python3`
   exists, run `~/.ai-video-editor/bin/python3 "<this skill's folder>/doctor.py"` (never the system `python3` - on a
   fresh Mac it pops an Apple install dialog); otherwise skip to step 2. `READY` means
   done: tell them they're set and suggest a first request ("Make a 20-second Reel from the newest testimonial
   footage"). Stop.
2. **Run the setup yourself, no questions asked** (tell them it takes a few minutes, mostly waiting; run it in the
   background or with a long timeout):
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "<this skill's folder, C:\ path>\setup-windows.ps1" -Auto`
   - Mac: `bash "<this skill's folder>/setup-mac.sh" --auto`
   If Windows asks for permission to install something, tell them to click **Yes**. On a Mac, Python and FFmpeg
   download into their user folder with no password.
3. **Handle what it prints**, then run it again until it prints `READY`:
   - `NEED: google-drive-signin` - the Google Drive window is open (or the Drive icon near the clock / in the menu bar).
     Ask them to sign in with their **company Google account** and tell you when their Google Drive shows up in File
     Explorer / Finder. Drive can take a minute to appear after signing in.
   - `NEED: google-drive-install` (Mac) - the setup has downloaded Google Drive and opened its installer on screen.
     Tell them: click **Continue**, then **Install**, and type the password they use to unlock their Mac. That's the
     only password in the whole setup (Apple requires it for any app installer). When it says it succeeded, run
     setup again - it then opens Google Drive for the sign-in.
   - `NEED: brand-file` - signed in with the right Google account? Drive may still be loading the folder list - wait
     a minute and run again. If it still fails, tell them to contact whoever set up the system: `brand.md` needs to be
     in the top footage folder of their Google Drive.
   - `NEED: elevenlabs-key` - the settings file next to `brand.md` is missing or has no key; same contact.
   - `NEED: winget` / `NEED: python` - give them the fix it prints in plain words.
4. **When it prints `READY`**, tell them to **quit and reopen the Claude / Codex app once** (so newly installed
   programs are found), then just ask for a video.

Never ask for the ElevenLabs key in chat. If they want to set it up by hand instead, the same scripts without
`-Auto` / `--auto` ask each question with the found values filled in; they run those in a terminal themselves.

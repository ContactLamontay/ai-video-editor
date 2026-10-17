---
name: editor-setup
description: Set up or re-check a computer for the AI video editor - installs Python, FFmpeg and Google Drive for Desktop, finds the footage folder in Google Drive by its name, picks up the brand rules and ElevenLabs key from the files the user was sent, checks everything. Use when the user asks to set up, install, "set me up", "is everything working", when ~/.ai-video-editor/config.json is missing or incomplete, or when an edit script fails because ffmpeg, Python, a package, the footage folder or the key is missing.
---

# Editor setup

The person using this is usually a business owner, not a developer: do the work for them, keep messages short and
plain, and never show them paths, JSON or terminal output unless something breaks.

## What the setup needs
- **The name of their footage folder** in Google Drive (e.g. "Bracelet") - the one question you ask. The setup finds
  it by name in My Drive and every shared drive they're in, so they don't need a path.
- **Two files they were sent** (usually by email): `brand.md` (brand rules) and `ai-video-editor.json` (ElevenLabs
  key). They just need to be saved in **Downloads** (or Desktop / Documents). The setup keeps a private copy on this
  computer, so they can delete the downloads afterwards. (Alternatively the two files can sit in an "AI video editor"
  folder in Google Drive; the setup finds those too.)
- Where finished videos go is asked later, on their first video (the `video-edit` skill).

## Steps
1. **Check first.** Windows: `python "<this skill's folder>/doctor.py"`. Mac: only if `~/.ai-video-editor/bin/python3`
   exists, run `~/.ai-video-editor/bin/python3 "<this skill's folder>/doctor.py"` (never the system `python3` - on a
   fresh Mac it pops an Apple install dialog); otherwise skip to step 2. `READY` means done: tell them they're set and
   suggest a first request ("Make a 20-second Reel from the newest testimonial footage"). Stop.
2. **Ask one thing, in one message:** "Which folder in your Google Drive has your footage? Just the name is fine. And
   have you saved the two files you were sent (brand.md and ai-video-editor.json) to your Downloads?" If they haven't
   saved the files, tell them to open the email and download both attachments.
3. **Run the setup yourself** with that name (tell them it takes a few minutes, mostly waiting; run it in the
   background or with a long timeout):
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "<this skill's folder, C:\ path>\setup-windows.ps1" -Auto -Footage "<name>"`
   - Mac: `bash "<this skill's folder>/setup-mac.sh" --auto --footage "<name>"`
   If Windows asks for permission to install something, tell them to click **Yes**. On a Mac, Python and FFmpeg
   download into their user folder with no password. If the Mac asks whether Claude / Codex may access the Downloads
   folder or Google Drive, they click **Allow**.
4. **Handle what it prints**, then run it again (same name) until it prints `READY`:
   - `NEED: google-drive-signin` - the Google Drive window is open (or the Drive icon near the clock / in the menu bar).
     Ask them to sign in with their **company Google account** and tell you when their Google Drive shows up in File
     Explorer / Finder. Drive can take a minute to appear after signing in.
   - `NEED: google-drive-install` (Mac) - the setup has downloaded Google Drive and opened its installer on screen.
     Tell them: click **Continue**, then **Install**, and type the password they use to unlock their Mac. That's the
     only password in the whole setup (Apple requires it for any app installer). When it says it succeeded, run
     setup again - it then opens Google Drive for the sign-in.
   - `NEED: footage-choose` - several folders have that name; read them the options (as listed) and run again with
     the full path of the one they pick.
   - `NEED: footage-not-found` - check the spelling with them. If Drive was just signed in, wait a minute (it's still
     loading the folder list). If the folder is under **Shared with me** in drive.google.com (not in a shared drive or
     their My Drive), it isn't on their computer until they add a shortcut, once: drive.google.com -> **Shared with
     me** -> right-click the folder -> **Organize** -> **Add shortcut** -> **My Drive** -> **Add**. Then run again.
   - `NEED: footage-folder` - you didn't pass a name; ask for it (step 2).
   - `NEED: brand-file` / `NEED: elevenlabs-key` - the two files aren't in Downloads yet: they open the email they were
     sent and download both attachments. If they never got them, they contact whoever set up the system.
   - `NEED: winget` / `NEED: python` - give them the fix it prints in plain words.
5. **When it prints `READY`**, tell them to **quit and reopen the Claude / Codex app once** (so newly installed
   programs are found), then just ask for a video. They can delete the two downloaded files now if they like.

**Updated brand rules or a new key:** they save the new file(s) to Downloads and say "update my settings" - run the
setup again; a newer download replaces the stored copy.

Never ask for the ElevenLabs key in chat. If they want to set it up by hand instead, the same scripts without
`-Auto` / `--auto` ask each question with the found values filled in; they run those in a terminal themselves.

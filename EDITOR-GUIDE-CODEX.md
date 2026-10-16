# AI Video Editor - setup guide (Codex)

About 15 minutes, once per computer. Works on Windows and Mac.

## Before you start
- A **ChatGPT plan that includes Codex**, and the **Codex app or CLI** installed and signed in.
- **Google Drive for Desktop** (https://www.google.com/drive/download/), signed in with your company Google account.
  Check you can see the footage folder in File Explorer / Finder.
- **Git** installed (https://git-scm.com/downloads).
- The **ElevenLabs API key** from your manager. You'll paste it into the setup script, never into a chat.

## 1. Download and install
In a terminal (PowerShell on Windows, Terminal on Mac):

```
git clone https://github.com/ContactLamontay/ai-video-editor.git "$HOME/ai-video-editor"
```

Then the installer. Windows:
```
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\ai-video-editor\codex\install-codex.ps1"
```
Mac:
```
bash "$HOME/ai-video-editor/codex/install-codex.sh"
```

It installs the editing skills into Codex, then asks to run the one-time setup: say yes and answer the questions.
It installs Python and FFmpeg, finds your Google Drive footage folder and the brand file, and asks for the
ElevenLabs key (typing is hidden). When it says **Done**, restart Codex.

## 2. Edit
Open Codex in your projects folder (the setup asked where; default `Video Edits` in your home folder) and ask, for
example:
- "Find B-roll of the product being unboxed"
- "Edit the testimonial clips from the March shoot into a 20-second Reel ad"

Codex runs in a sandbox. When it asks to use the internet (for transcription) or to write files in your projects
or output folder, approve it.

Codex makes a **preview** and opens the **Edit Review** screen in your browser. Press **N** to leave a note at the
exact moment, then click **Copy notes for the AI** and paste them back into Codex. When you're happy, click
**Approve and render final**.

## Updates
```
git -C "$HOME/ai-video-editor" pull
```
Then run the installer again (it skips the setup if you're already set up).

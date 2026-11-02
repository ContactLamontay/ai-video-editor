# AI Video Editor - setup guide (Codex)

About 15 minutes, once per computer. Works on Windows and Mac.

## Before you start
- A **ChatGPT plan that includes Codex**, and the **Codex app or CLI** installed and signed in.
- Your footage in **one folder**: either a normal folder on your computer (e.g. `Videos\Instagram`), or a Google
  Drive folder (then install **Google Drive for Desktop**, https://www.google.com/drive/download/, and sign in).
- **Git** (https://git-scm.com/downloads), or skip it and use the zip below.
- An **ElevenLabs API key** (for transcription): from your manager, or your own free account at elevenlabs.io ->
  Developers -> API keys. You'll paste it into the setup script, never into a chat.

## 1. Download and install
In a terminal (PowerShell on Windows, Terminal on Mac):

```
git clone https://github.com/ContactLamontay/ai-video-editor.git "$HOME/ai-video-editor"
```

No Git? Download https://github.com/ContactLamontay/ai-video-editor/archive/refs/heads/main.zip, unzip it, and
rename the folder to `ai-video-editor` in your home folder (`C:\Users\<you>` on Windows, your home folder on a Mac).

Then the installer. Windows:
```
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\ai-video-editor\codex\install-codex.ps1"
```
Mac:
```
bash "$HOME/ai-video-editor/codex/install-codex.sh"
```

It installs the editing skills into Codex, then asks to run the one-time setup: say yes and answer the questions.
It installs Python and FFmpeg, asks where your footage is (**1** = Google Drive, **2** = a folder on this computer),
finds the folder, and asks for the ElevenLabs key (typing is hidden). With no brand file, it makes a blank
**"My editing style"** file (`~/.ai-video-editor/brand.md`): fill it in, or just tell Codex what you like while you
edit and it adds it for you. When it says **Done**, restart Codex.

## 2. Edit
Open Codex in your projects folder (the setup asked where; default `Video Edits` in your home folder) and ask, for
example:
- "Edit my newest clip into a 30-second Reel with captions"
- "Find B-roll of the beach"

Codex runs in a sandbox. When it asks to use the internet (for transcription) or to write files in your projects
or output folder, approve it.

Codex makes a **preview** and opens the **Edit Review** screen in your browser. Press **N** to leave a note at the
exact moment, then click **Copy notes for the AI** and paste them back into Codex. When you're happy, click
**Approve and render final**.

## Updates
```
git -C "$HOME/ai-video-editor" pull
```
Then run the installer again (it skips the setup if you're already set up). Zip install: download the zip again,
replace the folder, and run the installer again.

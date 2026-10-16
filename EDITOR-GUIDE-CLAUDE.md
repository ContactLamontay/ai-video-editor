# AI Video Editor - setup guide (Claude)

About 15 minutes, once per computer. Works on Windows and Mac.

## Before you start
- A **Claude plan with Claude Code** and the **Claude desktop app**, installed and signed in.
- **Google Drive for Desktop** (https://www.google.com/drive/download/), signed in with your company Google account.
  Check you can see the footage folder in File Explorer / Finder.
- The **ElevenLabs API key** from your manager. You'll paste it into the setup script, never into a chat.

## 1. Install the plugin
In the Claude app, open a new session in the Code tab and run these one at a time:

```
/plugin marketplace add ContactLamontay/ai-video-editor
```
```
/plugin install ai-video-editor@ai-video-editor
```

## 2. Run the setup
Start a **new** session. Claude tells you setup is needed and gives you one command to copy. Paste it into a terminal
(PowerShell on Windows, Terminal on Mac) and answer the questions. It installs Python and FFmpeg, finds your Google
Drive footage folder and the brand file, and asks for the ElevenLabs key (typing is hidden). When it says
**All set**, restart the Claude app.

Nothing happened? Type `/ai-video-editor:setup`.

## 3. Edit
Just ask, for example:
- "Find B-roll of the product being unboxed"
- "Edit the testimonial clips from the March shoot into a 20-second Reel ad"
- "Make 3 versions of this ad with different hooks"

Claude makes a **preview** and opens the **Edit Review** screen in your browser. Press **N** to leave a note at
the exact moment, then click **Copy notes for the AI** or **Request changes**. When you're happy, click
**Approve and render final**.

## Updates
Run `/plugin marketplace update ai-video-editor` and restart the app.

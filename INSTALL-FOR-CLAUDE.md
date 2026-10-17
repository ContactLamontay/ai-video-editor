# Installing the AI video editor without Git (instructions for Claude)

Use this when the user can't or won't install Git (on a Mac, Git needs Apple's large Command Line Developer Tools),
or when they were sent `ai-video-editor.zip`. They're not a developer: do every step yourself, keep messages short,
and don't show them JSON or paths unless something breaks.

1. **Get the files** - one of:
   - **From GitHub, no Git needed** (the repo is public):
     `curl -fsSL -o ~/Downloads/ai-video-editor-main.zip https://github.com/ContactLamontay/ai-video-editor/archive/refs/heads/main.zip`
     (Windows: `Invoke-WebRequest -Uri <same URL> -OutFile "$env:USERPROFILE\Downloads\ai-video-editor-main.zip"`)
   - **From the zip they were sent:** `~/Downloads/ai-video-editor*.zip`, or a folder Safari already unzipped
     (`~/Downloads/ai-video-editor*/` containing `.claude-plugin/marketplace.json`). If the Mac asks whether Claude may
     access Downloads, they click **Allow**.
2. **Put it in a permanent place:** `~/.ai-video-editor/plugin-source/` (Windows: `%USERPROFILE%\.ai-video-editor\plugin-source\`).
   Remove any old copy there first. Unzip with `ditto -x -k <zip> <tmp>` on Mac (or `unzip`), `Expand-Archive` on
   Windows, then move the inner folder's contents (`ai-video-editor/` or `ai-video-editor-main/`) so that
   `~/.ai-video-editor/plugin-source/.claude-plugin/marketplace.json` exists. Delete the zip.
3. **Register it in the user's Claude settings** - `~/.claude/settings.json` (create it if missing; keep every
   setting already there). If an `ai-video-editor` marketplace entry already exists (e.g. a GitHub one that needs
   Git), **replace** it with this:
   ```json
   {
     "extraKnownMarketplaces": {
       "ai-video-editor": { "source": { "source": "directory", "path": "<absolute path to plugin-source>" } }
     },
     "enabledPlugins": { "ai-video-editor@ai-video-editor": true }
   }
   ```
   Use the real absolute path (e.g. `/Users/anna/.ai-video-editor/plugin-source`), not `~`.
4. **Tell them:** "Quit and reopen the Claude app, start a new session in the Code tab, and say *set me up*." If the
   old GitHub version is still listed in **Plugins**, they uninstall it there and install **ai-video-editor** again
   (it now comes from the folder). The plugin's setup takes over from there (it asks for the name of their footage
   folder). Their settings, brand file and key are kept.

**Updating later:** the user says "update the video editor". Repeat steps 1-2 (download the newest zip from GitHub,
replace the folder), leave the settings as they are, and have them quit and reopen Claude. If the old version still
shows, they update or reinstall **ai-video-editor** from the **Plugins** screen.

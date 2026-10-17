# Installing the AI video editor from the zip (instructions for Claude)

The user was sent `ai-video-editor.zip` (usually by email) and asked you to install it. They're not a developer:
do every step yourself, keep messages short, and don't show them JSON or paths unless something breaks. No GitHub
account and no Git are needed for this route.

1. **Find it in Downloads.** Either `~/Downloads/ai-video-editor*.zip`, or a folder Safari already unzipped
   (`~/Downloads/ai-video-editor*/` containing `.claude-plugin/marketplace.json`). On Windows: `%USERPROFILE%\Downloads`.
   If the Mac asks whether Claude may access Downloads, they click **Allow**. Not there: ask them to save the zip
   attachment to Downloads.
2. **Put it in a permanent place:** `~/.ai-video-editor/plugin-source/` (Windows: `%USERPROFILE%\.ai-video-editor\plugin-source\`).
   Remove any old copy there first. Unzip with `ditto -x -k <zip> <tmp>` on Mac (or `unzip`), `Expand-Archive` on
   Windows, then move the inner `ai-video-editor` folder's contents so that
   `~/.ai-video-editor/plugin-source/.claude-plugin/marketplace.json` exists.
3. **Register it in the user's Claude settings** - `~/.claude/settings.json` (create it if missing; keep every
   setting already there; if an `ai-video-editor` entry already exists, replace it):
   ```json
   {
     "extraKnownMarketplaces": {
       "ai-video-editor": { "source": { "source": "directory", "path": "<absolute path to plugin-source>" } }
     },
     "enabledPlugins": { "ai-video-editor@ai-video-editor": true }
   }
   ```
   Use the real absolute path (e.g. `/Users/anna/.ai-video-editor/plugin-source`), not `~`.
4. **Tell them:** "Quit and reopen the Claude app, start a new session in the Code tab, and say *set me up*." The
   plugin loads on startup and its setup takes over from there (it will ask for the name of their footage folder).
   They can delete the zip from Downloads afterwards.

**Updating later:** the user saves the new zip to Downloads and says "update the video editor". Repeat steps 1-2
(replace the folder), leave the settings as they are, and have them quit and reopen Claude. If the old version still
shows, they open **Plugins** in the Claude app and update / reinstall **ai-video-editor** there.

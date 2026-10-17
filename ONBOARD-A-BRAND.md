# Onboarding a new brand (for Josh)

Goal: the brand's people do nothing but sign in to Google Drive and say "set me up".

1. **Brand file.** Get their decks / brand guide / product docs. Ask Claude: "read these and write a brand file from
   `brands/TEMPLATE.md`". Check the approved claims and claims-to-avoid yourself; that's the part that can get the
   brand in trouble. Keep your copy in `Content/Clients/brand-files/<brand>-brand.md`, **not in this repo** (anyone
   can read the repo).
2. **Two files in their Google Drive** (no sorting or moving footage). Find the **top folder that holds their
   footage folders**, make a folder called **AI video editor** inside it, and upload into that:
   - `brand.md` - the brand file, renamed.
   - `ai-video-editor.json` - copy `Content/Clients/brand-files/ai-video-editor.json`, paste the brand's ElevenLabs
     key into it. Optional: `"music_dir"` / `"sfx_dir"` (folder names inside that top folder). Leave out
     `"output_dir"`: Claude asks each person where finished videos should go on their first video.
   The setup searches their Drive for `brand.md` (up to 5 folders deep); the folder *above* `AI video editor`
   becomes the footage library. (`brand.md` loose in the top footage folder works too.)
   Only one `brand.md` in their Drive, please.
3. **Their AI.** Claude: every Team seat includes Claude Code; they need the Claude desktop app. Codex: a ChatGPT plan
   with Codex.
4. **Plugin into their Claude org.** Ask the org **Owner** to add this in the admin console's Claude Code managed
   settings (then it installs itself for everyone):
   ```json
   {
     "extraKnownMarketplaces": {
       "ai-video-editor": { "source": { "source": "github", "repo": "ContactLamontay/ai-video-editor" } }
     },
     "enabledPlugins": { "ai-video-editor@ai-video-editor": true }
   }
   ```
   No Owner available: each person types the two `/plugin` commands from `EDITOR-GUIDE-CLAUDE.md` once.
5. **Tell each person:** "Open the Claude app, Code tab, and say *set me up*. Click Yes if Windows asks, and sign in
   to Google Drive with your company account when its window opens. Then restart Claude." Claude does the rest.
6. **First edit together.** Have them make one real video. Fix anything that's off in their brand file (edit
   `brand.md` in their Drive - everyone gets the change on the next edit).

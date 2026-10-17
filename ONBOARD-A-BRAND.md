# Onboarding a new brand (for Josh)

Goal: the brand's people do nothing but save two email attachments, say "set me up", name their footage folder, and
sign in to Google Drive.

1. **Brand file.** Get their decks / brand guide / product docs. Ask Claude: "read these and write a brand file from
   `brands/TEMPLATE.md`". Check the approved claims and claims-to-avoid yourself; that's the part that can get the
   brand in trouble. Keep your copy in `Content/Clients/brand-files/<brand>-brand.md`, **not in this repo** (anyone
   can read the repo).
2. **Two files, sent by email** (nothing goes in their Google Drive, nothing gets sorted or moved):
   - `brand.md` - the brand file, renamed.
   - `ai-video-editor.json` - copy `Content/Clients/brand-files/ai-video-editor.json` and paste the brand's
     ElevenLabs key into it (create the key with Speech to Text access only, plus a credit limit). Optional:
     `"music_dir"` / `"sfx_dir"` (folder names inside their footage folder). Leave out `"output_dir"`: Claude asks
     each person where finished videos should go on their first video.
   Email both as attachments to each person who'll use it. Setup picks them up from Downloads and keeps a private
   copy. (Alternative: put both in an "AI video editor" folder at the top of their footage in Google Drive - setup
   finds them there too, but everyone with access to that folder can see the key.)
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
5. **Tell each person:** "Save the two attachments to Downloads. Open the Claude app, Code tab, and say *set me up* -
   tell it the name of your footage folder. Click Yes / type your Mac password when the Google Drive installer asks,
   and sign in with your company account. Then restart Claude." Claude does the rest.
6. **First edit together.** Have them make one real video. To change the brand rules later, email the new `brand.md`;
   they save it to Downloads and tell Claude "update my settings".

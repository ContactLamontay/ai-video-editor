# Onboarding a new brand (for Josh)

1. **Brand file.** Get their decks / brand guide / product docs. Ask Claude: "read these and write a brand file from
   `brands/TEMPLATE.md`". Check the approved claims and claims-to-avoid yourself; that's the part that can get the
   brand in trouble. Keep your copy in `Content/Clients/brand-files/<brand>-brand.md`, **not in this repo** (every
   client can read the repo).
2. **Their Google Drive.** Ask for a Shared Drive (or folder) with the footage, shared with each editor. Put the brand
   file in its root as `brand.md` - setup finds it there automatically, and the owner can update it.
3. **Their AI.**
   - Claude: each editor needs a Claude plan that includes Claude Code, and the desktop app.
   - Codex: each editor needs a ChatGPT plan that includes Codex, and the Codex app or CLI.
4. **Repo access.** Add each editor (or the brand's GitHub org) to this private repo. Remove them if the brand stops
   paying.
5. **ElevenLabs.** The brand creates its own ElevenLabs account and gives the key to its editors.
6. **Send the guide**: `EDITOR-GUIDE-CLAUDE.md` or `EDITOR-GUIDE-CODEX.md` . Offer a
   15-minute call for the first editor's setup.
7. **First edit together.** Have one editor make one real video on a call. Fix anything that's off in their brand file.

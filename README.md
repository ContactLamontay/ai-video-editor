# ai-video-editor

## Setting this up? (AI assistants, read this first)

If a user shared this link and asked you to set it up, they are a video editor, not a developer. Keep it short and
plain, and don't clone or modify this repo for them unless the steps below say so.

**They have the zip file instead of this link** (no Git needed - also the way to install or update from GitHub without Git): follow
[INSTALL-FOR-CLAUDE.md](INSTALL-FOR-CLAUDE.md).

**In Claude (desktop app Code tab, or Claude Code):** you can't run `/plugin` commands yourself. Ask the user to type
these two commands, one at a time (adding a GitHub marketplace needs Git; on a Mac without it, run
`xcode-select --install` and have them click Install - or use the zip route above):

```
/plugin marketplace add ContactLamontay/ai-video-editor
```
```
/plugin install ai-video-editor@ai-video-editor
```

Then ask them to **start a new session**. The plugin checks the computer when the session starts and offers to run
the one-time setup itself (Python, FFmpeg, Google Drive, footage folder, brand file, ElevenLabs key).

**In Codex:** run `git clone https://github.com/ContactLamontay/ai-video-editor.git "$HOME/ai-video-editor"` (ask
first), then ask the user to run the installer themselves in a terminal, because it asks questions:
- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\ai-video-editor\codex\install-codex.ps1"`
- Mac: `bash "$HOME/ai-video-editor/codex/install-codex.sh"`

**Both:** the setup needs the two files the user was sent (`brand.md` and `ai-video-editor.json`, with the ElevenLabs
key) saved in Downloads, and the name of their footage folder in Google Drive. Never ask for the key in chat.

Editor guides: [Claude](EDITOR-GUIDE-CLAUDE.md) · [Codex](EDITOR-GUIDE-CODEX.md)

---

## About this repo

Josh's AI video editing system, packaged for brand teams. One engine, two front ends: **Claude Code** (plugin) and
**OpenAI Codex** (skills + AGENTS.md). Both use the same skill folders, so a fix lands in both.

```
.claude-plugin/marketplace.json     Claude marketplace "ai-video-editor" -> plugin/
plugin/
  .claude-plugin/plugin.json
  skills/video-edit/                edit engine (scripts/), style guide + example (references/)
  skills/video-review/              local review screen (app/)
  skills/editor-setup/              setup-windows.ps1, setup-mac.sh, doctor.py - shared by Claude and Codex
  commands/setup.md                 Claude: /ai-video-editor:setup
  hooks/                            Claude: on session start, hands out the setup command if not set up
codex/
  AGENTS.md                         block added to ~/.codex/AGENTS.md (setup check + when to use the skills)
  install-codex.ps1 / .sh           copy skills to ~/.agents/skills, add AGENTS block, offer to run setup
brands/TEMPLATE.md                  brand file template (real brand files live outside this repo)
EDITOR-GUIDE-CLAUDE.md / -CODEX.md  send the matching one to editors
ONBOARD-A-BRAND.md                  your checklist for a new client
```

## How brands differ
Only two files, which you email to the brand's people: `brand.md` (brand rules) and `ai-video-editor.json`
(ElevenLabs key, optional folders). Setup picks them up from Downloads and keeps a private copy; the footage folder is
found in Google Drive by the name the person gives ("Bracelet"). Claude runs the whole setup itself (`-Auto` /
`--auto`). This repo holds no brand data, so all clients share it. Keep your copies in `Content/Clients/brand-files/`.
See ONBOARD-A-BRAND.md.

## Publish
1. Working copy: C:/Users/Josh/Projects/ai-video-editor (kept out of iCloud).
2. Public GitHub repo: https://github.com/ContactLamontay/ai-video-editor

## Ship an update
Change files, bump `version` in `plugin/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, push.
Claude editors: `/plugin marketplace update ai-video-editor`. Codex editors: `git pull` + rerun the installer.

## Per-editor settings
`~/.ai-video-editor/config.json` (written by setup, never committed): `footage_dir`, `projects_dir`, `output_dir`,
`music_dir`, `sfx_dir`, `brand_file`, `elevenlabs_api_key`. Footage index: `~/.ai-video-editor/library/`.
Brand fonts: `~/.ai-video-editor/fonts/`.

## Renaming the product
"ai-video-editor" is a placeholder. To rename: find-and-replace `ai-video-editor` and `AI Video Editor` across the
repo (config folder, plugin and marketplace names, AGENTS markers, guides).

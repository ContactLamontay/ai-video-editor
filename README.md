# ai-video-editor

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
Only the **brand file**. Each brand's `brand.md` sits in the root of its Google Drive footage folder; the setup
script records its path (`brand_file` in `~/.ai-video-editor/config.json`) and every edit reads it. This repo holds
no brand data, so all clients can share it. Keep your brand files in `Content/Clients/brand-files/`.

## Publish
1. Working copy: C:/Users/Josh/Projects/ai-video-editor (kept out of iCloud).
2. Private GitHub repo: https://github.com/ContactLamontay/ai-video-editor

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

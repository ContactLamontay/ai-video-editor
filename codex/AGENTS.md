<!-- ai-video-editor:start -->
## AI video editor

This computer has the AI video editor skills installed in `~/.agents/skills`: `video-edit`, `video-review` and
`editor-setup`.

- For any request to edit, cut, re-cut or render a video, ad, reel, TikTok or short, find B-roll, or review an edit,
  use those skills. Read the skill's SKILL.md before running anything.
- At the start of every video task, check that `~/.ai-video-editor/config.json` exists. If it doesn't, follow the
  `editor-setup` skill first: explain what's needed and give the editor the setup command to run themselves. Never ask
  for the ElevenLabs API key in chat.
- Editing needs internet (transcription) and writes to the editor's project and output folders. If the sandbox
  blocks either, ask the editor to approve it instead of working around it.
- Editors aren't developers: keep replies plain and short, and say roughly how long each wait is.
<!-- ai-video-editor:end -->

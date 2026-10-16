#!/bin/bash
# AI Video Editor - install (or update) the skills for OpenAI Codex on a Mac.
#   bash "<repo>/codex/install-codex.sh"
# Copies the skills to ~/.agents/skills, adds the editor block to ~/.codex/AGENTS.md, then offers to run the setup.
# Re-run after `git pull` to update.
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DST="$HOME/.agents/skills"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
AGENTS="$CODEX_HOME/AGENTS.md"
mkdir -p "$DST" "$CODEX_HOME"

for s in "$REPO"/plugin/skills/*/; do
  name="$(basename "$s")"; rm -rf "$DST/$name"; cp -R "$s" "$DST/$name"; echo "skill installed: $DST/$name"
done

touch "$AGENTS"
/usr/bin/python3 - "$AGENTS" "$REPO/codex/AGENTS.md" <<'EOF'
import re, sys
path, block = sys.argv[1], open(sys.argv[2]).read().strip()
text = open(path).read()
pat = re.compile(r"<!-- ai-video-editor:start -->.*?<!-- ai-video-editor:end -->", re.S)
text = pat.sub(lambda m: block, text) if pat.search(text) else (text.rstrip() + "\n\n" + block + "\n").lstrip()
open(path, "w").write(text)
EOF
echo "instructions added: $AGENTS"

SETUP="$DST/editor-setup/setup-mac.sh"
if [ -f "$HOME/.ai-video-editor/config.json" ]; then
  read -r -p $'\nThis Mac is already set up. Run the setup again anyway? [y/N] ' a; a="${a:-n}"
else
  read -r -p $'\nRun the one-time setup now (Python, FFmpeg, footage folder, ElevenLabs key)? [Y/n] ' a; a="${a:-y}"
fi
case "$a" in
  [yY]*) bash "$SETUP" ;;
  *) echo "Skipped. Run it later with:"; echo "  bash \"$SETUP\"" ;;
esac
printf "\n\033[32mDone. Restart Codex, then ask it to edit a video.\033[0m\n"

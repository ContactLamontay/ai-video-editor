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
# perl ships with every Mac (the system python3 doesn't work until Apple's developer tools are installed)
BLOCK="$(cat "$REPO/codex/AGENTS.md")" perl -0777 -i -pe '
  my $b = $ENV{BLOCK}; $b =~ s/\s+\z//;
  if (/<!-- ai-video-editor:start -->.*?<!-- ai-video-editor:end -->/s) { s//$b/s }
  else { s/\s+\z//; $_ = ($_ eq "" ? "" : "$_\n\n") . "$b\n" }
' "$AGENTS"
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

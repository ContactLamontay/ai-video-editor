#!/bin/bash
# SessionStart hook (Claude Code): if this computer isn't set up for the AI video editor yet, tell Claude to offer
# to set it up - Claude runs the no-questions setup itself. Silent once everything is in place.
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CFG="$HOME/.ai-video-editor/config.json"
export PATH="$HOME/.ai-video-editor/bin:$PATH"   # Mac setup puts python3/ffmpeg here
# On a Mac, never call the system python3: without Apple's developer tools it pops an install dialog
PYS="python3 python"; [ "$(uname -s)" = "Darwin" ] && PYS="$HOME/.ai-video-editor/bin/python3"

missing=""
command -v ffmpeg >/dev/null 2>&1 || missing="$missing ffmpeg,"
PY=""
for p in $PYS; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import PIL, numpy" >/dev/null 2>&1; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  missing="$missing python,"
  [ -f "$CFG" ] || missing="$missing settings,"
elif ! "$PY" -c "import json,sys,os; c=json.load(open(sys.argv[1],encoding='utf-8-sig')); sys.exit(0 if c.get('elevenlabs_api_key') and os.path.isdir(c.get('footage_dir') or '') else 1)" "$CFG" >/dev/null 2>&1; then
  missing="$missing settings,"
fi
[ -z "$missing" ] && exit 0
missing="${missing%,}"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    WIN_ROOT="$(cygpath -w "$ROOT" 2>/dev/null || echo "$ROOT")"
    CMD="powershell -NoProfile -ExecutionPolicy Bypass -File \"$WIN_ROOT\\skills\\editor-setup\\setup-windows.ps1\" -Auto" ;;
  *)
    CMD="bash \"$ROOT/skills/editor-setup/setup-mac.sh\" --auto" ;;
esac

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
CTX="AI video editor plugin: this computer is NOT set up yet (missing:$missing). At the start of your first reply, before anything else, tell the user in one or two plain sentences that the video editor needs a quick one-time setup on this computer (about 10 minutes, mostly waiting) and offer to do it for them now. If they agree (or they ask you to set up / edit a video), run the setup yourself: $CMD  - it asks no questions (run it in the background or with a long timeout; installs can take several minutes). Then follow the editor-setup skill: it explains each 'NEED:' line the script prints (e.g. signing in to Google Drive) - pass those to the user in plain words, wait for them, and run the setup again until it prints READY. Never ask for the ElevenLabs key in chat."
MSG="AI video editor: this computer needs a quick one-time setup. Just say 'set me up' and Claude will do it."

printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$MSG")" "$(json_escape "$CTX")"

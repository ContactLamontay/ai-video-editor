#!/bin/bash
# SessionStart hook (Claude Code): if this computer isn't set up for the AI video editor yet, tell the editor and hand
# Claude the exact setup command for this OS. Silent once everything is in place.
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CFG="$HOME/.ai-video-editor/config.json"

missing=""
[ -f "$CFG" ] || missing="$missing settings,"
command -v ffmpeg >/dev/null 2>&1 || missing="$missing ffmpeg,"
PY=""
for p in python3 python; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import PIL, numpy" >/dev/null 2>&1; then PY="$p"; break; fi
done
[ -n "$PY" ] || missing="$missing python,"
[ -z "$missing" ] && exit 0
missing="${missing%,}"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    WIN_ROOT="$(cygpath -w "$ROOT" 2>/dev/null || echo "$ROOT")"
    CMD="powershell -NoProfile -ExecutionPolicy Bypass -File \"$WIN_ROOT\\skills\\editor-setup\\setup-windows.ps1\""
    WHERE="PowerShell or the Terminal panel" ;;
  *)
    CMD="bash \"$ROOT/skills/editor-setup/setup-mac.sh\""
    WHERE="Terminal" ;;
esac

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
CTX="AI video editor plugin: this computer is NOT set up yet (missing:$missing). At the start of your first reply, before anything else, tell the user in plain language that the video editor needs a one-time setup (about 10 minutes: installs Python + FFmpeg, finds their Google Drive footage folder and brand file, and asks for the ElevenLabs key) and give them this exact command to paste into $WHERE, in its own code block: $CMD . Say it is interactive and they should run it themselves, not you. Before running it they need Google Drive for Desktop installed and signed in with the company Google account (https://www.google.com/drive/download/). Never ask them to paste the API key into chat - the script asks for it. After they run it, they should restart the Claude app. Follow the editor-setup skill for details and to re-check."
MSG="AI video editor: one-time setup needed on this computer. Ask Claude 'set me up' or run /ai-video-editor:setup."

printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$MSG")" "$(json_escape "$CTX")"

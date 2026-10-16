#!/bin/bash
# AI Video Editor - one-time setup for a Mac editing computer.
# Run it in Terminal (it asks a few questions):
#   bash "<this file>"
# Safe to re-run: it skips what's already installed and keeps your previous answers as defaults.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG_DIR="$HOME/.ai-video-editor"
CFG_FILE="$CFG_DIR/config.json"

say() { printf "\n\033[36m== %s\033[0m\n" "$1"; }
old() { [ -f "$CFG_FILE" ] && /usr/bin/python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2]) or '')" "$CFG_FILE" "$1" 2>/dev/null || true; }
ask() {  # ask "question" "default"  -> answer in $REPLY
  local q="$1" d="$2"
  if [ -n "$d" ]; then read -r -p "$q [$d]: " REPLY; else read -r -p "$q: " REPLY; fi
  REPLY="${REPLY:-$d}"; REPLY="${REPLY%\"}"; REPLY="${REPLY#\"}"; REPLY="${REPLY/#\~/$HOME}"
}

printf "\033[32mAI Video Editor setup\033[0m\n"
[ -f "$CFG_FILE" ] && echo "Found your previous settings - press Enter to keep them."

say "Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$b" ] && eval "$("$b" shellenv)"; done
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Installing Homebrew (it will ask for your Mac password)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$b" ] && eval "$("$b" shellenv)"; done
  SHELLRC="$HOME/.zprofile"; grep -q "brew shellenv" "$SHELLRC" 2>/dev/null || echo "eval \"\$($(command -v brew) shellenv)\"" >> "$SHELLRC"
fi

say "Python + FFmpeg"
command -v ffmpeg >/dev/null 2>&1 || brew install ffmpeg
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then brew install python@3.12; fi
PY="$(command -v python3)"
echo "Using $PY"

say "Python packages"
"$PY" -m pip install --user --upgrade --quiet --break-system-packages -r "$HERE/requirements.txt" 2>/dev/null \
  || "$PY" -m pip install --user --upgrade --quiet -r "$HERE/requirements.txt"
echo "Optional: auto-framing for vertical videos (rembg, ~200 MB)..."
"$PY" -m pip install --user --quiet --break-system-packages "rembg[cpu]" 2>/dev/null || echo "rembg skipped (vertical crops will centre instead)."

say "Google Drive footage library"
GD="$(ls -d "$HOME"/Library/CloudStorage/GoogleDrive-* 2>/dev/null | head -1 || true)"
DEF_FOOTAGE="$(old footage_dir)"
if [ -n "$GD" ]; then
  echo "Google Drive found at $GD"
  if [ -d "$GD/Shared drives" ]; then echo "Shared drives:"; ls -d "$GD/Shared drives"/*/ 2>/dev/null | sed 's/^/   /'; fi
  [ -z "$DEF_FOOTAGE" ] && DEF_FOOTAGE="$GD/Shared drives"
else
  echo "Google Drive for Desktop isn't running on this Mac."
  echo "Install it from https://www.google.com/drive/download/ and sign in with your company Google account,"
  echo "then run this setup again. (Or type the footage folder path below if it lives somewhere else.)"
fi
while true; do
  ask "Folder with your footage / B-roll (drag the folder in from Finder)" "$DEF_FOOTAGE"
  FOOTAGE="${REPLY%/}"; FOOTAGE="${FOOTAGE% }"; FOOTAGE="${FOOTAGE//\\ / }"
  [ -d "$FOOTAGE" ] && break; echo "Can't find that folder - try again."
done

say "Folders"
D="$(old projects_dir)"; ask "Where to keep edit projects on this Mac" "${D:-$HOME/Video Edits}"; PROJECTS="$REPLY"
D="$(old output_dir)"; ask "Where finished videos go (a Google Drive folder works)" "${D:-$PROJECTS/Finished}"; OUTPUT="$REPLY"
ask "Music folder (licensed tracks) - Enter to skip" "$(old music_dir)"; MUSIC="$REPLY"
ask "Sound effects folder - Enter to skip" "$(old sfx_dir)"; SFX="$REPLY"

say "Brand rules"
DEF_BRAND="$(old brand_file)"; [ -z "$DEF_BRAND" ] && [ -f "$FOOTAGE/brand.md" ] && DEF_BRAND="$FOOTAGE/brand.md"
while true; do
  ask "Brand rules file (the brand.md you were given) - Enter to skip for now" "$DEF_BRAND"; BRAND="$REPLY"
  { [ -z "$BRAND" ] || [ -f "$BRAND" ]; } && break; echo "Can't find that file - try again."; DEF_BRAND=""
done
mkdir -p "$PROJECTS" "$OUTPUT"

say "ElevenLabs (transcription)"
read -r -s -p "Paste the ElevenLabs API key (typing is hidden; Enter keeps the current one): " KEY; echo
[ -z "$KEY" ] && KEY="$(old elevenlabs_api_key)"

mkdir -p "$CFG_DIR"
FOOTAGE="$FOOTAGE" PROJECTS="$PROJECTS" OUTPUT="$OUTPUT" MUSIC="$MUSIC" SFX="$SFX" BRAND="$BRAND" KEY="$KEY" "$PY" - "$CFG_FILE" <<'EOF'
import json, os, sys
e = os.environ
json.dump({"footage_dir": e["FOOTAGE"], "projects_dir": e["PROJECTS"], "output_dir": e["OUTPUT"],
           "music_dir": e["MUSIC"], "sfx_dir": e["SFX"], "brand_file": e["BRAND"], "elevenlabs_api_key": e["KEY"]}, open(sys.argv[1], "w"), indent=2)
EOF
chmod 600 "$CFG_FILE"
echo "Saved settings to $CFG_FILE"

say "Checking everything"
if "$PY" "$HERE/doctor.py"; then
  printf "\n\033[32mAll set. Restart Claude / Codex, then ask it to edit a video.\033[0m\n"
fi

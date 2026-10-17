#!/bin/bash
# AI Video Editor - one-time setup for a Mac.
#   bash "<this file>"          asks a few questions (defaults filled in)
#   bash "<this file>" --auto   asks nothing - the AI runs this one
# Installs FFmpeg (and Python if needed) with Homebrew, finds the footage folder by searching Google Drive for
# brand.md, reads ai-video-editor.json next to it (ElevenLabs key, folders), checks everything.
# In --auto mode, "NEED: ..." lines say what only the user can do (e.g. install Homebrew, sign in to Google Drive);
# exit code 2. Safe to re-run: it skips what's already done and keeps previous settings.
HERE="$(cd "$(dirname "$0")" && pwd)"
AUTO=""; [ "$1" = "--auto" ] && AUTO="--auto"
say() { printf "\n\033[36m== %s\033[0m\n" "$1"; }
need() { echo "NEED: $1"; exit 2; }

printf "\033[32mAI Video Editor setup\033[0m\n"

say "Homebrew"
for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$b" ] && eval "$("$b" shellenv)"; done
if ! command -v brew >/dev/null 2>&1; then
  INSTALL='/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  # Homebrew's installer needs the Mac password, so in --auto mode the user has to run it themselves
  [ -n "$AUTO" ] && need "homebrew: paste this into the Terminal app and enter your Mac password when asked: $INSTALL - then run setup again"
  echo "Installing Homebrew (it will ask for your Mac password)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$b" ] && eval "$("$b" shellenv)"; done
fi
command -v brew >/dev/null 2>&1 || need "homebrew: the Homebrew install didn't finish - run setup again"
grep -q "brew shellenv" "$HOME/.zprofile" 2>/dev/null || echo "eval \"\$($(command -v brew) shellenv)\"" >> "$HOME/.zprofile"

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

say "Google Drive"
mounted() { ls -d "$HOME"/Library/CloudStorage/GoogleDrive-*/ >/dev/null 2>&1; }
if ! mounted; then
  if [ ! -d "/Applications/Google Drive.app" ]; then
    # the Google Drive installer asks for the Mac password, so in --auto mode the user runs it
    [ -n "$AUTO" ] && need "google-drive-install: download Google Drive for Desktop from https://www.google.com/drive/download/, install it, sign in with the company Google account, then run setup again"
    brew install --cask google-drive
  fi
  open -a "Google Drive" 2>/dev/null
  for i in $(seq 1 20); do mounted && break; sleep 3; done
  if ! mounted; then
    [ -n "$AUTO" ] && need "google-drive-signin: sign in with the company Google account in the Google Drive window (or the Drive icon in the menu bar), wait until Google Drive appears in Finder's sidebar, then run setup again"
    read -r -p "Sign in to Google Drive with your company Google account, then press Enter when it shows up in Finder... "
  fi
fi
mounted && echo "Google Drive OK"

say "Settings"
"$PY" "$HERE/configure.py" $AUTO; CFG_EXIT=$?

say "Checking everything"
if "$PY" "$HERE/doctor.py" && [ "$CFG_EXIT" = 0 ]; then
  printf "\n\033[32mREADY. Restart Claude / Codex once, then ask it to edit a video.\033[0m\n"
  exit 0
fi
exit 2

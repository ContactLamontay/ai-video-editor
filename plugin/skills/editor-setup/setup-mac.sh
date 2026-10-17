#!/bin/bash
# AI Video Editor - one-time setup for a Mac. No Homebrew, no admin rights for the tools: Python and FFmpeg are
# downloaded into ~/.ai-video-editor (no password). Only Google Drive for Desktop needs the Mac password, because
# Apple requires it for any app installer.
#   bash "<this file>"          asks a few questions (defaults filled in)
#   bash "<this file>" --auto   asks nothing - the AI runs this one
#   bash "<this file>" --auto --footage "Bracelet"   the footage folder's name in Google Drive (asked once by the AI)
# Finds the footage folder by name in Google Drive, picks up brand.md + ai-video-editor.json (ElevenLabs key) from
# Downloads (e.g. an email attachment), checks everything. In --auto mode, "NEED: ..." lines say what only the user can do (install Google
# Drive with their password, sign in); exit code 2. Safe to re-run: it skips what's already done.
HERE="$(cd "$(dirname "$0")" && pwd)"
AUTO=""; FOOTAGE=""
while [ $# -gt 0 ]; do case "$1" in --auto) AUTO="--auto" ;; --footage) FOOTAGE="$2"; shift ;; esac; shift; done
BASE="$HOME/.ai-video-editor"; BIN="$BASE/bin"; VENV="$BASE/venv"; DL="$BASE/downloads"
mkdir -p "$BIN" "$DL"
export PATH="$BIN:$HOME/.local/bin:$PATH"
say() { printf "\n\033[36m== %s\033[0m\n" "$1"; }
need() { echo "NEED: $1"; exit 2; }
fetch() { curl -fsSL --retry 3 --retry-delay 2 -o "$2" "$1"; }

printf "\033[32mAI Video Editor setup\033[0m\n"
case "$(uname -m)" in arm64) ARCH=arm64 ;; *) ARCH=amd64 ;; esac

say "Python"
if [ ! -x "$VENV/bin/python" ]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "Downloading uv (Python installer)..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh >/dev/null 2>&1
  fi
  command -v uv >/dev/null 2>&1 || need "python: couldn't download Python (no internet?) - check the connection and run setup again"
  echo "Downloading Python 3.12..."
  uv venv --quiet --python 3.12 "$VENV" || need "python: Python download failed - run setup again"
fi
ln -sf "$VENV/bin/python" "$BIN/python3"; ln -sf "$VENV/bin/python" "$BIN/python"
PY="$BIN/python3"
echo "Using $PY ($("$PY" --version 2>&1))"

say "FFmpeg"
for tool in ffmpeg ffprobe; do
  if ! "$BIN/$tool" -version >/dev/null 2>&1; then
    echo "Downloading $tool..."
    fetch "https://ffmpeg.martin-riedl.de/redirect/latest/macos/$ARCH/release/$tool.zip" "$DL/$tool.zip" \
      || need "ffmpeg: couldn't download $tool - check the internet connection and run setup again"
    unzip -o -q "$DL/$tool.zip" -d "$BIN" && rm -f "$DL/$tool.zip"
    chmod +x "$BIN/$tool"; xattr -d com.apple.quarantine "$BIN/$tool" 2>/dev/null
    "$BIN/$tool" -version >/dev/null 2>&1 || codesign --force -s - "$BIN/$tool" 2>/dev/null   # ad-hoc sign if macOS refuses it
  fi
  "$BIN/$tool" -version >/dev/null 2>&1 || need "ffmpeg: $tool was downloaded but macOS won't run it - tell whoever set this up"
done
echo "ffmpeg OK"

say "Python packages"
uv pip install --quiet --python "$VENV/bin/python" -r "$HERE/requirements.txt" || need "python: installing Python packages failed - run setup again"
echo "Optional: auto-framing for vertical videos (rembg, ~200 MB)..."
uv pip install --quiet --python "$VENV/bin/python" "rembg[cpu]" 2>/dev/null || echo "rembg skipped (vertical crops will centre instead)."

# make python3 / ffmpeg from ~/.ai-video-editor/bin the ones Claude / Codex find after a restart
for rc in "$HOME/.zprofile" "$HOME/.zshrc" "$HOME/.bash_profile"; do
  grep -q ".ai-video-editor/bin" "$rc" 2>/dev/null || printf '\n# AI video editor\nexport PATH="$HOME/.ai-video-editor/bin:$PATH"\n' >> "$rc"
done

say "Google Drive"
mounted() { ls -d "$HOME"/Library/CloudStorage/GoogleDrive-*/ >/dev/null 2>&1; }
if ! mounted; then
  if [ ! -d "/Applications/Google Drive.app" ]; then
    echo "Downloading Google Drive for Desktop (~140 MB)..."
    fetch "https://dl.google.com/drive-file-stream/GoogleDrive.dmg" "$DL/GoogleDrive.dmg" \
      || need "google-drive-install: couldn't download Google Drive - check the internet connection and run setup again"
    MNT="$(hdiutil attach -nobrowse -noverify "$DL/GoogleDrive.dmg" | awk -F'\t' '/\/Volumes\//{print $NF}' | tail -1)"
    PKG="$(ls "$MNT"/*.pkg 2>/dev/null | head -1)"
    [ -n "$PKG" ] && cp "$PKG" "$DL/GoogleDrive.pkg"
    hdiutil detach -quiet "$MNT" 2>/dev/null
    [ -f "$DL/GoogleDrive.pkg" ] || need "google-drive-install: download Google Drive for Desktop from https://www.google.com/drive/download/, install it, then run setup again"
    open "$DL/GoogleDrive.pkg"
    MSG="google-drive-install: the Google Drive installer is now open on screen - click Continue, then Install, and type the Mac password (the one used to unlock this Mac). When it says the installation was successful, run setup again"
    [ -n "$AUTO" ] && need "$MSG"
    read -r -p "Install Google Drive in the window that opened (it asks for your Mac password), then press Enter... "
  fi
  open -a "Google Drive" 2>/dev/null
  for i in $(seq 1 20); do mounted && break; sleep 3; done
  if ! mounted; then
    MSG="google-drive-signin: sign in with the company Google account in the Google Drive window (or click the Drive icon in the menu bar at the top of the screen). If the Mac asks to allow Google Drive in System Settings, click Allow. Wait until Google Drive shows up in Finder's sidebar, then run setup again"
    [ -n "$AUTO" ] && need "$MSG"
    read -r -p "Sign in to Google Drive with your company Google account, then press Enter when it shows up in Finder... "
  fi
fi
mounted && echo "Google Drive OK"
rm -f "$DL/GoogleDrive.dmg"

say "Settings"
if [ -n "$FOOTAGE" ]; then "$PY" "$HERE/configure.py" $AUTO --footage "$FOOTAGE"; else "$PY" "$HERE/configure.py" $AUTO; fi; CFG_EXIT=$?

say "Checking everything"
if "$PY" "$HERE/doctor.py" && [ "$CFG_EXIT" = 0 ]; then
  rm -f "$DL/GoogleDrive.pkg"
  printf "\n\033[32mREADY. Quit and reopen Claude / Codex once, then ask it to edit a video.\033[0m\n"
  exit 0
fi
exit 2

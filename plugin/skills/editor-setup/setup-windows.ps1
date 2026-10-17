# AI Video Editor - one-time setup for a Windows computer.
#   powershell -NoProfile -ExecutionPolicy Bypass -File "<this file>"          asks a few questions (defaults filled in)
#   powershell -NoProfile -ExecutionPolicy Bypass -File "<this file>" -Auto    asks nothing - the AI runs this one
#   ... -Auto -Footage "Bracelet"     the footage folder's name in Google Drive (asked once by the AI)
# Installs Python, FFmpeg and Google Drive for Desktop if missing, finds the footage folder by name in Google Drive,
# picks up brand.md + ai-video-editor.json (ElevenLabs key) from Downloads (e.g. an email attachment), checks everything.
# In -Auto mode, "NEED: ..." lines say what only the user can do (e.g. sign in to Google Drive); exit code 2.
# Safe to re-run: it skips what's already done and keeps previous settings.
param([switch]$Auto, [string]$Footage = "")
$ErrorActionPreference = "Continue"   # not Stop: in Windows PowerShell, pip/winget writing to stderr would abort the script
$ProgressPreference = "SilentlyContinue"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Say($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function RefreshPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function WingetInstall($id, $extra) {
    $a = @("install", "-e", "--id", $id, "--accept-source-agreements", "--accept-package-agreements", "--disable-interactivity") + $extra
    & winget @a | Out-Host
}
function PyVersionOk($exe) {
    try { return ((& $exe -c "import sys; print(sys.version_info >= (3, 10))" 2>$null) -eq "True") } catch { return $false }
}
function FindPython {
    if (Have "py") {
        try { $p = (& py -3 -c "import sys; print(sys.executable)" 2>$null); if ($p -and (PyVersionOk $p)) { return $p } } catch {}
    }
    $c = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
    foreach ($f in $c) { if (PyVersionOk $f.FullName) { return $f.FullName } }
    $g = Get-Command python -ErrorAction SilentlyContinue
    if ($g -and ($g.Source -notlike "*WindowsApps*") -and (PyVersionOk $g.Source)) { return $g.Source }
    return $null
}
function DriveMounted {
    [bool](Get-PSDrive -PSProvider FileSystem | Where-Object { (Test-Path (Join-Path $_.Root "My Drive")) -or (Test-Path (Join-Path $_.Root "Shared drives")) })
}
function DriveExe {
    $p = Get-ChildItem "$env:ProgramFiles\Google\Drive File Stream\*\GoogleDriveFS.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if ($p) { return $p.FullName }; return $null
}

Write-Host "AI Video Editor setup" -ForegroundColor Green
if (-not (Have "winget")) {
    Write-Host "NEED: winget: install 'App Installer' from the Microsoft Store (https://apps.microsoft.com/detail/9NBLGGH4NNS1), then run setup again"
    exit 2
}

Say "Python"
$py = FindPython
if (-not $py) { WingetInstall "Python.Python.3.12" @("--scope", "user"); RefreshPath; $py = FindPython }
if (-not $py) { Write-Host "NEED: python: the Python install didn't finish - install Python 3.12 from python.org, then run setup again"; exit 2 }
Write-Host "Using $py"
# make plain 'python' point at the real Python (not the Microsoft Store shortcut) for the AI's commands
$g = Get-Command python -ErrorAction SilentlyContinue
if (-not $g -or $g.Source -like "*WindowsApps*") {
    $pyDir = Split-Path $py
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    [Environment]::SetEnvironmentVariable("Path", "$pyDir;$pyDir\Scripts;$userPath", "User")
    RefreshPath
    Write-Host "Added Python to your PATH."
}

Say "FFmpeg"
if (-not (Have "ffmpeg")) { WingetInstall "Gyan.FFmpeg" @(); RefreshPath }
if (Have "ffmpeg") { Write-Host "ffmpeg OK" } else { Write-Host "FFmpeg installed - it works after the Claude / Codex app restarts." }

Say "Python packages"
& $py -m pip install --user --upgrade --quiet --disable-pip-version-check -r (Join-Path $Here "requirements.txt")
Write-Host "Optional: auto-framing for vertical videos (rembg, ~200 MB)..."
& $py -m pip install --user --quiet --disable-pip-version-check "rembg[cpu]" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "rembg skipped (vertical crops will centre instead)." }

Say "Google Drive"
if (-not (DriveMounted)) {
    if (-not (DriveExe)) {
        Write-Host "Installing Google Drive for Desktop (Windows may ask for permission)..."
        WingetInstall "Google.GoogleDrive" @()
    }
    $exe = DriveExe
    if ($exe) { Start-Process $exe | Out-Null }
    # give an existing sign-in a moment to mount the drive
    for ($i = 0; $i -lt 20 -and -not (DriveMounted); $i++) { Start-Sleep -Seconds 3 }
    if (-not (DriveMounted)) {
        if ($Auto) {
            Write-Host "NEED: google-drive-signin: Google Drive for Desktop is installed. Sign in with the company Google account in the Google Drive window (or click the Drive icon near the clock), wait until the G: drive appears in File Explorer, then run setup again"
            exit 2
        }
        Write-Host "Sign in to Google Drive with your company Google account in the window that opened." -ForegroundColor Yellow
        Read-Host "When the G: drive shows up in File Explorer, press Enter"
    }
}
if (DriveMounted) { Write-Host "Google Drive OK" }

Say "Settings"
$cfgArgs = @((Join-Path $Here "configure.py")); if ($Auto) { $cfgArgs += "--auto" }; if ($Footage) { $cfgArgs += @("--footage", $Footage) }
& $py @cfgArgs
$cfgExit = $LASTEXITCODE

Say "Checking everything"
& $py (Join-Path $Here "doctor.py")
if ($LASTEXITCODE -eq 0 -and $cfgExit -eq 0) {
    Write-Host "`nREADY. Restart Claude / Codex once, then ask it to edit a video." -ForegroundColor Green
    exit 0
}
exit 2

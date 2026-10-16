# AI Video Editor - one-time setup for a Windows editing computer.
# Run it in a terminal (it asks a few questions):
#   powershell -NoProfile -ExecutionPolicy Bypass -File "<this file>"
# Safe to re-run: it skips what's already installed and keeps your previous answers as defaults.
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$CfgDir = Join-Path $HOME ".ai-video-editor"
$CfgFile = Join-Path $CfgDir "config.json"

function Say($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function RefreshPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Ask($question, $default) {
    $suffix = ""
    if ($default) { $suffix = " [$default]" }
    $a = Read-Host "$question$suffix"
    if ([string]::IsNullOrWhiteSpace($a)) { return $default }
    return $a.Trim().Trim('"')
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

Write-Host "AI Video Editor setup" -ForegroundColor Green
$old = @{}
if (Test-Path $CfgFile) {
    (Get-Content $CfgFile -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $old[$_.Name] = $_.Value }
    Write-Host "Found your previous settings - press Enter to keep them."
}

if (-not (Have "winget")) {
    Write-Host "winget is missing. Install 'App Installer' from the Microsoft Store, then run this again." -ForegroundColor Red
    exit 1
}

Say "Python"
$py = FindPython
if (-not $py) {
    winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
    RefreshPath; $py = FindPython
}
if (-not $py) { Write-Host "Python install failed - install Python 3.12 from python.org, then run this again." -ForegroundColor Red; exit 1 }
Write-Host "Using $py"
# make plain 'python' point at the real Python (not the Microsoft Store shortcut) for Claude's commands
$g = Get-Command python -ErrorAction SilentlyContinue
if (-not $g -or $g.Source -like "*WindowsApps*") {
    $pyDir = Split-Path $py
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    [Environment]::SetEnvironmentVariable("Path", "$pyDir;$pyDir\Scripts;$userPath", "User")
    RefreshPath
    Write-Host "Added Python to your PATH."
}

Say "FFmpeg"
if (-not (Have "ffmpeg")) {
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    RefreshPath
}
if (-not (Have "ffmpeg")) { Write-Host "FFmpeg installed but not visible yet - close this window and run setup again." -ForegroundColor Yellow }
else { Write-Host "ffmpeg OK" }

Say "Python packages"
& $py -m pip install --user --upgrade --quiet -r (Join-Path $Here "requirements.txt")
Write-Host "Optional: auto-framing for vertical videos (rembg, ~200 MB)..."
try { & $py -m pip install --user --quiet "rembg[cpu]" } catch { Write-Host "rembg skipped (vertical crops will centre instead)." -ForegroundColor Yellow }

Say "Google Drive footage library"
$drive = Get-PSDrive -PSProvider FileSystem | Where-Object { (Test-Path (Join-Path $_.Root "Shared drives")) -or (Test-Path (Join-Path $_.Root "My Drive")) } | Select-Object -First 1
if ($drive) {
    Write-Host "Google Drive found at $($drive.Root)"
    $sd = Join-Path $drive.Root "Shared drives"
    if (Test-Path $sd) { Write-Host "Shared drives:"; Get-ChildItem $sd -Directory | ForEach-Object { Write-Host "   $($_.FullName)" } }
    $defFootage = $old["footage_dir"]; if (-not $defFootage) { $defFootage = $sd }
} else {
    Write-Host "Google Drive for Desktop isn't running on this computer." -ForegroundColor Yellow
    Write-Host "Install it from https://www.google.com/drive/download/ and sign in with your company Google account,"
    Write-Host "then run this setup again. (Or type the footage folder path below if it lives somewhere else.)"
    $defFootage = $old["footage_dir"]
}
do {
    $footage = Ask "Folder with your footage / B-roll" $defFootage
    if (-not $footage -or -not (Test-Path $footage)) { Write-Host "Can't find that folder - try again (copy the path from File Explorer)." -ForegroundColor Yellow; $footage = $null }
} until ($footage)

Say "Folders"
$defProj = $old["projects_dir"]; if (-not $defProj) { $defProj = Join-Path $HOME "Video Edits" }
$projects = Ask "Where to keep edit projects on this computer" $defProj
$defOut = $old["output_dir"]; if (-not $defOut) { $defOut = Join-Path $projects "Finished" }
$output = Ask "Where finished videos go (a Google Drive folder works)" $defOut
$music = Ask "Music folder (licensed tracks) - Enter to skip" $old["music_dir"]
$sfx = Ask "Sound effects folder - Enter to skip" $old["sfx_dir"]

Say "Brand rules"
$defBrand = $old["brand_file"]
if (-not $defBrand -and (Test-Path (Join-Path $footage "brand.md"))) { $defBrand = Join-Path $footage "brand.md" }
do {
    $brand = Ask "Brand rules file (the brand.md you were given)" $defBrand
    if ($brand -and -not (Test-Path $brand -PathType Leaf)) { Write-Host "Can't find that file - try again, or press Enter to skip for now." -ForegroundColor Yellow; $defBrand = $null; $brand = "?" }
} until ($brand -ne "?")
New-Item -ItemType Directory -Force -Path $projects, $output | Out-Null

Say "ElevenLabs (transcription)"
$sec = Read-Host "Paste the ElevenLabs API key (typing is hidden; Enter keeps the current one)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
$key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
if ([string]::IsNullOrWhiteSpace($key)) { $key = $old["elevenlabs_api_key"] }

$cfg = [ordered]@{
    footage_dir = $footage; projects_dir = $projects; output_dir = $output
    music_dir = $music; sfx_dir = $sfx; brand_file = $brand; elevenlabs_api_key = $key
}
New-Item -ItemType Directory -Force -Path $CfgDir | Out-Null
[IO.File]::WriteAllText($CfgFile, ($cfg | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))
Write-Host "Saved settings to $CfgFile"

Say "Checking everything"
& $py (Join-Path $Here "doctor.py")
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nAll set. Restart Claude / Codex, then ask it to edit a video." -ForegroundColor Green
}

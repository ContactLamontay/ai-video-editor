# AI Video Editor - install (or update) the skills for OpenAI Codex on Windows.
#   powershell -NoProfile -ExecutionPolicy Bypass -File "<repo>\codex\install-codex.ps1"
# Copies the skills to ~/.agents/skills, adds the editor block to ~/.codex/AGENTS.md, then offers to run the setup.
# Re-run after `git pull` to update.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillsSrc = Join-Path $Repo "plugin\skills"
$SkillsDst = Join-Path $HOME ".agents\skills"
$CodexHome = $env:CODEX_HOME; if (-not $CodexHome) { $CodexHome = Join-Path $HOME ".codex" }
$AgentsFile = Join-Path $CodexHome "AGENTS.md"
$Block = (Get-Content (Join-Path $Repo "codex\AGENTS.md") -Raw).Trim()

New-Item -ItemType Directory -Force -Path $SkillsDst, $CodexHome | Out-Null
foreach ($s in Get-ChildItem $SkillsSrc -Directory) {
    $dst = Join-Path $SkillsDst $s.Name
    if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
    Copy-Item $s.FullName $dst -Recurse
    Write-Host "skill installed: $dst"
}

$text = ""
if (Test-Path $AgentsFile) { $text = Get-Content $AgentsFile -Raw }
$pattern = "(?s)<!-- ai-video-editor:start -->.*?<!-- ai-video-editor:end -->"
if ($text -match $pattern) { $text = [regex]::Replace($text, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $Block }) }
else { $text = ($text.TrimEnd() + "`n`n" + $Block + "`n").TrimStart() }
[IO.File]::WriteAllText($AgentsFile, $text, (New-Object Text.UTF8Encoding $false))
Write-Host "instructions added: $AgentsFile"

$cfg = Join-Path $HOME ".ai-video-editor\config.json"
$a = "y"
if (Test-Path $cfg) { $a = Read-Host "`nThis computer is already set up. Run the setup again anyway? [y/N]" }
else { $r = Read-Host "`nRun the one-time setup now (Python, FFmpeg, footage folder, ElevenLabs key)? [Y/n]"; if ($r -match "^[nN]") { $a = "n" } }
if ($a -match "^[yY]") {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $SkillsDst "editor-setup\setup-windows.ps1")
} else {
    Write-Host "Skipped. Run it later with:"
    Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $SkillsDst 'editor-setup\setup-windows.ps1')`""
}
Write-Host "`nDone. Restart Codex, then ask it to edit a video." -ForegroundColor Green

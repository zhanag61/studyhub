# Run the project-pinned tool without changing PATH or the website environment.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$executable = Join-Path $projectRoot '.tools/speckit/venv/Scripts/specify.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw 'Spec Kit 尚未安装；请先运行 .\scripts\setup-speckit.ps1。'
}
Push-Location -LiteralPath $projectRoot
try {
    if ($args.Count -eq 0) { & $executable version }
    else { & $executable @args }
    $toolExitCode = $LASTEXITCODE
}
finally { Pop-Location }
exit $toolExitCode

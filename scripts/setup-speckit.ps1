# Install development tooling only. Initialization is a separate reviewed action.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$basePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
$toolEnvironment = Join-Path $projectRoot '.tools/speckit/venv'
$toolPython = Join-Path $toolEnvironment 'Scripts/python.exe'
$lockFile = Join-Path $projectRoot 'tools/speckit/requirements-windows.txt'
if (-not (Test-Path -LiteralPath $basePython)) {
    throw '请先按 README 在此项目建立 .venv；安装工具会使用同一 Python 版本。'
}
if (-not (Test-Path -LiteralPath $toolPython)) {
    & $basePython -m venv $toolEnvironment
    if ($LASTEXITCODE -ne 0) { throw '工具虚拟环境创建未完成。' }
}
& $toolPython -m pip --version
if ($LASTEXITCODE -ne 0) {
    & $toolPython -m ensurepip --upgrade --default-pip
    if ($LASTEXITCODE -ne 0) { throw '工具环境 pip 初始化失败。' }
}
& $toolPython -m pip install --disable-pip-version-check -r $lockFile
if ($LASTEXITCODE -ne 0) { throw 'Spec Kit 安装失败；未执行项目初始化。' }
& $toolPython -m pip check
if ($LASTEXITCODE -ne 0) { throw '工具依赖检查失败。' }
& (Join-Path $toolEnvironment 'Scripts/specify.exe') version
if ($LASTEXITCODE -ne 0) { throw 'Spec Kit 版本检查失败。' }

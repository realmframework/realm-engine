param(
    [switch]$RequireInstaller
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$Version = (uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])").Trim()
$DistAppDir = Join-Path $Root "dist\REALM Engine"
$ExePath = Join-Path $DistAppDir "REALM Engine.exe"
$ZipPath = Join-Path $Root "dist\REALM-Engine-$Version-windows-x64-portable.zip"
$SetupPath = Join-Path $Root "dist\REALM-Engine-$Version-windows-x64-setup.exe"
$IconOut = Join-Path $Root "packaging\icons\realm-engine.ico"

Write-Host "==> Generating high-DPI Windows .ico (16-256px) from logo-512.png"
New-Item -ItemType Directory -Path (Split-Path $IconOut) -Force | Out-Null
uv run python -c "from pathlib import Path; from PIL import Image; img = Image.open(Path('features/ui/static/logo-512.png')).convert('RGBA'); img.save(Path('packaging/icons/realm-engine.ico'), format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not generate multi-size ICO; falling back to favicon.ico"
}

Write-Host "==> Building REALM Engine ($Version, Windows x64) with PyInstaller"
uv run --group desktop pyinstaller --noconfirm --clean "$Root\packaging\realm-engine.spec"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}
if (-not (Test-Path $ExePath)) {
    throw "Expected built executable not found: $ExePath"
}

Write-Host "==> Running headless smoke test on built Windows executable"
$SmokeDir = Join-Path ([System.IO.Path]::GetTempPath()) ("realm-smoke-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $SmokeDir | Out-Null
try {
    $proc = Start-Process -FilePath $ExePath -ArgumentList @("--smoke-test", "--data-dir", $SmokeDir) -Wait -PassThru -NoNewWindow
    if ($proc.ExitCode -ne 0) {
        foreach ($logCand in @((Join-Path $SmokeDir "logs\realm-engine.log"), (Join-Path $SmokeDir "realm-engine.log"))) {
            if (Test-Path $logCand) {
                Write-Host "--- Smoke test diagnostic log ($logCand) ---"
                Get-Content $logCand
            }
        }
        throw "Smoke test exited with code $($proc.ExitCode)"
    }
    $WelcomePath = Join-Path $SmokeDir "knowledge_base\welcome.md"
    if (-not (Test-Path $WelcomePath)) {
        throw "Smoke test did not seed starter vault: $WelcomePath"
    }
    Write-Host "    Smoke test passed (server, /healthz, /, /static/ui.css, WebView2 backend, starter vault)"
} finally {
    Remove-Item -Recurse -Force $SmokeDir -ErrorAction SilentlyContinue
}

Write-Host "==> Creating portable ZIP (with top-level folder): $ZipPath"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path "$DistAppDir" -DestinationPath $ZipPath -CompressionLevel Optimal

$IsccPath = $null
$IsccCmd = Get-Command iscc -ErrorAction SilentlyContinue
if ($IsccCmd) {
    $IsccPath = $IsccCmd.Source
} else {
    $DefaultIscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $DefaultIscc) { $IsccPath = $DefaultIscc }
}

if ($IsccPath) {
    Write-Host "==> Building Windows Setup Installer with Inno Setup: $SetupPath"
    if (Test-Path $SetupPath) { Remove-Item -Force $SetupPath }
    & $IsccPath "/DAppVersion=$Version" "$Root\packaging\realm-engine.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }
} elseif ($RequireInstaller) {
    throw "Inno Setup (iscc) was not found and -RequireInstaller was specified."
} else {
    Write-Warning "Inno Setup (iscc) not found; skipped setup.exe build (portable ZIP was created)."
}

Write-Host ""
Write-Host "Build complete:"
Write-Host "  Portable ZIP: $ZipPath"
if (Test-Path $SetupPath) {
    Write-Host "  Setup EXE:    $SetupPath"
}

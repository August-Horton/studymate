# StudyMate Build Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  StudyMate Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Installing Electron with mirror..." -ForegroundColor Yellow
Write-Host ""

$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_CACHE = "D:\studymate\.electron-cache"

npm install electron@29.3.0 --save-dev

if ($LASTEXITCODE -ne 0) {
    Write-Host "Electron installation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/3] Building Electron app..." -ForegroundColor Yellow
Write-Host ""
npm run electron:build:win

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/3] Build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build Success!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Output directory: release" -ForegroundColor White
Write-Host ""
Get-ChildItem release\*.exe | ForEach-Object { Write-Host $_.Name -ForegroundColor Green }
Write-Host ""

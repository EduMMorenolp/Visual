Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup ComfyUI - ModelosIA\Visual" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

Write-Host "[1/5] Verificando estructura de directorios..." -ForegroundColor Yellow
$dirs = @(
    "models\checkpoints", "models\loras", "models\vae", "models\upscale_models",
    "workflows", "scripts", "output", "input", "custom_nodes"
)
foreach ($dir in $dirs) {
    $path = Join-Path $RootDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  Creado: $dir" -ForegroundColor Green
    }
}
Write-Host "  Directorios OK" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] Instalando dependencias de Python para scripts..." -ForegroundColor Yellow
$reqFile = Join-Path $RootDir "scripts\requirements-scripts.txt"
if (Test-Path $reqFile) {
    pip install -r $reqFile 2>&1 | Out-Null
    Write-Host "  Dependencias instaladas" -ForegroundColor Green
} else {
    Write-Host "  No se encontró $reqFile" -ForegroundColor Red
}

Write-Host ""
Write-Host "[3/5] Descargando modelos..." -ForegroundColor Yellow
$dlScript = Join-Path $RootDir "scripts\download_models.py"
if (Test-Path $dlScript) {
    python $dlScript
} else {
    Write-Host "  No se encontró $dlScript" -ForegroundColor Red
}

Write-Host ""
Write-Host "[4/5] Construyendo imagen Docker..." -ForegroundColor Yellow
docker compose build 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Imagen construida correctamente" -ForegroundColor Green
} else {
    Write-Host "  ERROR construyendo imagen" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[5/5] Iniciando contenedor..." -ForegroundColor Yellow
docker compose up -d 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Contenedor iniciado" -ForegroundColor Green
} else {
    Write-Host "  ERROR iniciando contenedor" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup completado!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:        http://localhost:8188" -ForegroundColor White
Write-Host "  UI:         http://localhost:8188 (Web UI)" -ForegroundColor White
Write-Host "  Outputs:    $RootDir\output" -ForegroundColor White
Write-Host "  Modelos:    $RootDir\models\checkpoints" -ForegroundColor White
Write-Host ""
Write-Host "  Para probar generacion:" -ForegroundColor Yellow
Write-Host '    python scripts\generate.py --prompt "tu prompt aqui"' -ForegroundColor Gray
Write-Host ""
Write-Host "  Para usar desde otro modelo:" -ForegroundColor Yellow
Write-Host "    from scripts.generate import generate_image" -ForegroundColor Gray
Write-Host "    img = generate_image('tu prompt', model='sdxl')" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
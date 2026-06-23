param(
    [switch]$NoDataset
)

Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      HealthAnalytics IPS — Setup Windows             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = if (Get-Command "python" -ErrorAction SilentlyContinue) { "python" }
            elseif (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" }
            else { Write-Host "ERROR: Python no está instalado. Instálalo desde https://www.python.org/downloads/" -ForegroundColor Red; exit 1 }

Write-Host "`nPython detectado: $(& $pythonCmd --version)" -ForegroundColor Green

# 2. Virtual environment
$venvPath = Join-Path -Path (Get-Location) -ChildPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "`n▶ Creando entorno virtual..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv
} else {
    Write-Host "`n▶ Entorno virtual ya existe" -ForegroundColor Yellow
}

# 3. Activate and install dependencies
$pip = if ($IsWindows -or $env:OS) { "venv\Scripts\pip.exe" } else { "venv/bin/pip" }
$pythonVenv = if ($IsWindows -or $env:OS) { "venv\Scripts\python.exe" } else { "venv/bin/python" }

Write-Host "`n▶ Instalando dependencias..." -ForegroundColor Yellow
& $pip install --upgrade pip -q
& $pip install -r requirements.txt -q
Write-Host "  ✓ Dependencias instaladas" -ForegroundColor Green

# 4. .env file
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" -Destination ".env"
    Write-Host "▶ Archivo .env creado desde .env.example" -ForegroundColor Yellow
} else {
    Write-Host "▶ Archivo .env ya existe" -ForegroundColor Yellow
}

# 5. Migrations
Write-Host "`n▶ Ejecutando migraciones..." -ForegroundColor Yellow
& $pythonVenv manage.py makemigrations authentication etl analytics ml
& $pythonVenv manage.py migrate
Write-Host "  ✓ Migraciones ejecutadas" -ForegroundColor Green

# 6. Superuser
Write-Host "`n▶ Creando superusuario administrador..." -ForegroundColor Yellow
& $pythonVenv manage.py shell -c "from apps.authentication.models import Usuario; import sys; sys.stdout.write('  → Superusuario ya existe\n') if Usuario.objects.filter(username='admin').exists() else [Usuario.objects.create_superuser('admin', 'admin@healthanalytics.co', 'admin123', rol='administrador'), sys.stdout.write('  → Superusuario creado: admin / admin123\n')]"

# 7. Load dataset
if (-not $NoDataset) {
    $dataset = "datasets\dataset_clinico.xlsx"
    if (Test-Path $dataset) {
        Write-Host "`n▶ Cargando dataset y ejecutando ETL..." -ForegroundColor Yellow
        & $pythonVenv manage.py cargar_dataset --archivo $dataset
    } else {
        Write-Host "`n▶ Dataset no encontrado en $dataset" -ForegroundColor Yellow
        Write-Host "  Copia tu dataset Excel a datasets\dataset_clinico.xlsx" -ForegroundColor Yellow
        Write-Host "  y ejecuta: python manage.py cargar_dataset" -ForegroundColor Yellow
    }
}

# 8. Static files
Write-Host "`n▶ Recopilando archivos estáticos..." -ForegroundColor Yellow
& $pythonVenv manage.py collectstatic --noinput -v 0
Write-Host "  ✓ Archivos estáticos recolectados" -ForegroundColor Green

Write-Host "`n╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✓ Setup completado                                  ║" -ForegroundColor Cyan
Write-Host "║                                                      ║" -ForegroundColor Cyan
Write-Host "║  Ejecuta el servidor:                                ║" -ForegroundColor Cyan
Write-Host "║    .\venv\Scripts\activate                           ║" -ForegroundColor Cyan
Write-Host "║    python manage.py runserver                        ║" -ForegroundColor Cyan
Write-Host "║                                                      ║" -ForegroundColor Cyan
Write-Host "║  URL: http://127.0.0.1:8000                          ║" -ForegroundColor Cyan
Write-Host "║  Admin: http://127.0.0.1:8000/admin                  ║" -ForegroundColor Cyan
Write-Host "║  Usuario: admin / admin123                           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan

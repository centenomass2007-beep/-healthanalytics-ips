#!/usr/bin/env bash
# setup.sh — Configuración inicial del proyecto HealthAnalytics IPS
set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║      HealthAnalytics IPS — Setup Inicial             ║"
echo "╚══════════════════════════════════════════════════════╝"

# 1. Entorno virtual
echo ""
echo "▶ Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# 2. Dependencias
echo "▶ Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 3. Variables de entorno
if [ ! -f .env ]; then
  cp .env.example .env
  echo "▶ Archivo .env creado (revisa y ajusta las variables)"
fi

# 4. Migraciones
echo "▶ Ejecutando migraciones..."
python manage.py makemigrations authentication etl analytics ml
python manage.py migrate

# 5. Superusuario
echo "▶ Creando superusuario administrador..."
python manage.py shell -c "
from apps.authentication.models import Usuario
if not Usuario.objects.filter(username='admin').exists():
    Usuario.objects.create_superuser('admin', 'admin@healthanalytics.co', 'admin123', rol='administrador')
    print('  → Superusuario creado: admin / admin123')
else:
    print('  → Superusuario ya existe')
"

# 6. Cargar dataset (si existe)
DATASET="datasets/dataset_clinico.xlsx"
if [ -f "$DATASET" ]; then
  echo "▶ Cargando dataset y ejecutando ETL..."
  python manage.py cargar_dataset --archivo "$DATASET"
else
  echo "▶ Dataset no encontrado en $DATASET"
  echo "  Copia tu dataset Excel a datasets/dataset_clinico.xlsx"
  echo "  y ejecuta: python manage.py cargar_dataset"
fi

# 7. Archivos estáticos
echo "▶ Recopilando archivos estáticos..."
python manage.py collectstatic --noinput -v 0

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✓ Setup completado                                  ║"
echo "║                                                      ║"
echo "║  Ejecuta el servidor:                                ║"
echo "║    source venv/bin/activate                          ║"
echo "║    python manage.py runserver                        ║"
echo "║                                                      ║"
echo "║  URL: http://127.0.0.1:8000                          ║"
echo "║  Admin: http://127.0.0.1:8000/admin                  ║"
echo "║  Usuario: admin / admin123                           ║"
echo "╚══════════════════════════════════════════════════════╝"

#!/bin/bash
set -e

echo "⏳ Esperando base de datos..."
sleep 2

echo "▶ Ejecutando migraciones..."
python manage.py migrate --noinput

echo "▶ Creando superusuario si no existe..."
python manage.py shell -c "
from apps.authentication.models import Usuario
if not Usuario.objects.filter(username='admin').exists():
    Usuario.objects.create_superuser('admin', 'admin@healthanalytics.co', 'admin123', rol='administrador')
    print('  Superusuario creado: admin / admin123')
"

echo "▶ Cargando dataset inicial si existe..."
if [ -f "datasets/dataset_clinico.xlsx" ]; then
    python manage.py cargar_dataset
fi

echo "✓ Iniciando servidor..."
exec "$@"

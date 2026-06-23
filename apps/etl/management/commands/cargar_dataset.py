"""
Comando Django: python manage.py cargar_dataset
Copia el dataset original al directorio datasets/ y ejecuta el ETL inicial.
"""
import os, shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.etl.etl_engine import ejecutar_etl

class Command(BaseCommand):
    help = 'Carga el dataset clínico inicial y ejecuta el proceso ETL'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', type=str, default=None,
                            help='Ruta al archivo Excel/CSV del dataset')

    def handle(self, *args, **options):
        archivo = options['archivo']
        dest = os.path.join(settings.DATASETS_DIR, 'dataset_clinico.xlsx')
        os.makedirs(settings.DATASETS_DIR, exist_ok=True)

        if archivo and os.path.exists(archivo):
            shutil.copy(archivo, dest)
            self.stdout.write(f'Dataset copiado desde: {archivo}')
        elif not os.path.exists(dest):
            self.stdout.write(self.style.ERROR(
                f'No se encontró dataset en {dest}. '
                'Usa --archivo /ruta/al/dataset.xlsx'
            ))
            return

        self.stdout.write('Ejecutando proceso ETL...')
        historial = ejecutar_etl(dest)
        if historial.estado == 'completado':
            self.stdout.write(self.style.SUCCESS(
                f'ETL completado: {historial.registros_limpios} registros cargados '
                f'en {historial.tiempo_ejecucion_seg}s'
            ))
        else:
            self.stdout.write(self.style.ERROR(f'ETL falló: {historial.errores}'))

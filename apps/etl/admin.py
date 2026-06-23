from django.contrib import admin
from .models import Paciente, HistorialETL

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['id_paciente', 'nombres', 'apellidos', 'edad', 'sexo', 
                    'riesgo_enfermedad', 'es_critico', 'fecha_consulta']
    list_filter = ['riesgo_enfermedad', 'es_critico', 'sexo', 'clasificacion_imc']
    search_fields = ['nombres', 'apellidos', 'diagnostico_preliminar']

@admin.register(HistorialETL)
class HistorialETLAdmin(admin.ModelAdmin):
    list_display = ['fecha_ejecucion', 'usuario', 'registros_entrada', 
                    'registros_limpios', 'estado', 'tiempo_ejecucion_seg']
    list_filter = ['estado']
    readonly_fields = ['log_detalle', 'errores']

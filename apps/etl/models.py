from django.db import models
from apps.authentication.models import Usuario

class Paciente(models.Model):
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    RIESGO_CHOICES = [
        ('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico')
    ]
    ACTIVIDAD_CHOICES = [
        ('sedentario', 'Sedentario'), ('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')
    ]
    IMC_CHOICES = [
        ('bajo_peso', 'Bajo Peso'), ('normal', 'Normal'),
        ('sobrepeso', 'Sobrepeso'), ('obesidad', 'Obesidad')
    ]

    id_paciente      = models.IntegerField(unique=True)
    nombres          = models.CharField(max_length=100)
    apellidos        = models.CharField(max_length=100)
    edad             = models.IntegerField(null=True, blank=True)
    sexo             = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)
    peso             = models.FloatField(null=True, blank=True)
    altura           = models.FloatField(null=True, blank=True)
    imc              = models.FloatField(null=True, blank=True)
    clasificacion_imc= models.CharField(max_length=20, choices=IMC_CHOICES, null=True, blank=True)
    presion_sistolica   = models.IntegerField(null=True, blank=True)
    presion_diastolica  = models.IntegerField(null=True, blank=True)
    frecuencia_cardiaca = models.IntegerField(null=True, blank=True)
    glucosa          = models.FloatField(null=True, blank=True)
    colesterol       = models.FloatField(null=True, blank=True)
    saturacion_oxigeno = models.FloatField(null=True, blank=True)
    temperatura      = models.FloatField(null=True, blank=True)
    antecedentes_familiares = models.BooleanField(default=False)
    fumador          = models.BooleanField(default=False)
    consumo_alcohol  = models.BooleanField(default=False)
    actividad_fisica = models.CharField(max_length=20, choices=ACTIVIDAD_CHOICES, null=True, blank=True)
    diagnostico_preliminar = models.CharField(max_length=200, null=True, blank=True)
    riesgo_enfermedad = models.CharField(max_length=10, choices=RIESGO_CHOICES, null=True, blank=True)
    fecha_consulta   = models.DateField(null=True, blank=True)
    es_critico       = models.BooleanField(default=False)
    fecha_carga      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['id_paciente']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} (ID: {self.id_paciente})"

    def calcular_critico(self):
        """Detecta pacientes críticos según umbrales clínicos."""
        if self.presion_sistolica and self.presion_sistolica > 180:
            return True
        if self.glucosa and self.glucosa > 300:
            return True
        if self.saturacion_oxigeno and self.saturacion_oxigeno < 85:
            return True
        return False


class HistorialETL(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'), ('error', 'Error')
    ]
    usuario          = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_ejecucion  = models.DateTimeField(auto_now_add=True)
    archivo_origen   = models.CharField(max_length=255, blank=True)
    registros_entrada= models.IntegerField(default=0)
    registros_limpios= models.IntegerField(default=0)
    duplicados_eliminados = models.IntegerField(default=0)
    nulos_tratados   = models.IntegerField(default=0)
    tiempo_ejecucion_seg = models.FloatField(default=0)
    estado           = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    log_detalle      = models.TextField(blank=True)
    errores          = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Historial ETL'
        verbose_name_plural = 'Historial ETL'
        ordering = ['-fecha_ejecucion']

    def __str__(self):
        return f"ETL {self.fecha_ejecucion.strftime('%Y-%m-%d %H:%M')} - {self.estado}"

from django.db import models

class EstadisticaClinica(models.Model):
    """Snapshot de estadísticas calculadas en cada análisis."""
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    total_pacientes = models.IntegerField(default=0)
    pacientes_criticos = models.IntegerField(default=0)
    pacientes_hipertensos = models.IntegerField(default=0)
    pacientes_diabeticos = models.IntegerField(default=0)
    pacientes_fumadores = models.IntegerField(default=0)
    promedio_edad = models.FloatField(null=True)
    promedio_imc = models.FloatField(null=True)
    promedio_glucosa = models.FloatField(null=True)
    promedio_colesterol = models.FloatField(null=True)
    riesgo_bajo = models.IntegerField(default=0)
    riesgo_medio = models.IntegerField(default=0)
    riesgo_alto = models.IntegerField(default=0)
    riesgo_critico = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Estadística Clínica'
        ordering = ['-fecha_calculo']

    def __str__(self):
        return f"Estadística {self.fecha_calculo.strftime('%Y-%m-%d %H:%M')}"

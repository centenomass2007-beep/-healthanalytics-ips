from django.db import models

class ModeloML(models.Model):
    ALGORITMO_CHOICES = [
        ('logistic_regression', 'Regresión Logística'),
        ('decision_tree', 'Árbol de Decisión'),
        ('random_forest', 'Random Forest'),
    ]
    nombre = models.CharField(max_length=100)
    algoritmo = models.CharField(max_length=30, choices=ALGORITMO_CHOICES)
    fecha_entrenamiento = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField(null=True)
    precision = models.FloatField(null=True)
    recall = models.FloatField(null=True)
    f1_score = models.FloatField(null=True)
    matriz_confusion = models.JSONField(null=True)
    variables_predictoras = models.JSONField(default=list)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Modelo ML'
        ordering = ['-fecha_entrenamiento']

    def __str__(self):
        return f"{self.nombre} - {self.get_algoritmo_display()} (Acc: {self.accuracy})"


class PrediccionPaciente(models.Model):
    paciente = models.ForeignKey('etl.Paciente', on_delete=models.CASCADE,
                                  related_name='predicciones')
    modelo = models.ForeignKey(ModeloML, on_delete=models.CASCADE)
    probabilidad_riesgo = models.FloatField()
    riesgo_predicho = models.CharField(max_length=10)
    fecha_prediccion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Predicción'
        ordering = ['-fecha_prediccion']

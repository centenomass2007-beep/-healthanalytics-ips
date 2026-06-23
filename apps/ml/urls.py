from django.urls import path
from .views import entrenar, predecir, modelos_lista, predicciones_lista

urlpatterns = [
    path('entrenar/', entrenar, name='ml_entrenar'),
    path('predecir/', predecir, name='ml_predecir'),
    path('modelos/', modelos_lista, name='ml_modelos'),
    path('predicciones/', predicciones_lista, name='ml_predicciones'),
]

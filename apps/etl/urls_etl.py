from django.urls import path
from .views import ejecutar_etl_view, subir_dataset, historial_etl

urlpatterns = [
    path('run/', ejecutar_etl_view, name='etl_run'),
    path('upload/', subir_dataset, name='etl_upload'),
    path('historial/', historial_etl, name='etl_historial'),
]

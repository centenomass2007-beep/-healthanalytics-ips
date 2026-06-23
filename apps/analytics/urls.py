from django.urls import path
from .views import kpis, estadisticas_descriptivas, segmentacion, tendencias, generar_snapshot

urlpatterns = [
    path('kpis/', kpis, name='analytics_kpis'),
    path('estadisticas/', estadisticas_descriptivas, name='analytics_stats'),
    path('segmentacion/', segmentacion, name='analytics_segmentacion'),
    path('tendencias/', tendencias, name='analytics_tendencias'),
    path('snapshot/', generar_snapshot, name='analytics_snapshot'),
]

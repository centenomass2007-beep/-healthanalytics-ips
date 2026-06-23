from django.urls import path
from .views import exportar_csv, exportar_excel, historial_etl_reporte, exportar_pdf

urlpatterns = [
    path('csv/', exportar_csv, name='reporte_csv'),
    path('excel/', exportar_excel, name='reporte_excel'),
    path('pdf/', exportar_pdf, name='reporte_pdf'),
    path('etl/', historial_etl_reporte, name='reporte_etl'),
]

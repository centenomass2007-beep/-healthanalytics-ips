from django.urls import path
from .views import dashboard_kpis

urlpatterns = [
    path('kpis/', dashboard_kpis, name='dashboard_kpis'),
]

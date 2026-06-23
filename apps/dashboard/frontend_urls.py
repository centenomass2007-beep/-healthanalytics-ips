from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='dashboard/index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login_page'),
    path('etl/', TemplateView.as_view(template_name='etl/index.html'), name='etl_page'),
    path('ml/', TemplateView.as_view(template_name='ml/index.html'), name='ml_page'),
    path('pacientes/', TemplateView.as_view(template_name='dashboard/pacientes.html'), name='pacientes_page'),
]

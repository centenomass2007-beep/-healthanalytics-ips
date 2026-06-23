from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PacienteViewSet

router = DefaultRouter()
router.register('', PacienteViewSet, basename='pacientes')
urlpatterns = router.urls

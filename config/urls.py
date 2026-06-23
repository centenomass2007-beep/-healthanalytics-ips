"""
HealthAnalytics IPS — URLs principales
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── API REST ──────────────────────────────────────────────
    path('api/auth/',      include('apps.authentication.urls')),
    path('api/pacientes/', include('apps.etl.urls')),
    path('api/etl/',       include('apps.etl.urls_etl')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/ml/',        include('apps.ml.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/reportes/',  include('apps.reports.urls')),

    # ── Swagger / OpenAPI ─────────────────────────────────────
    path('api/schema/',         SpectacularAPIView.as_view(),          name='schema'),
    path('api/docs/',           SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/',     SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),

    # ── Frontend ──────────────────────────────────────────────
    path('', include('apps.dashboard.frontend_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

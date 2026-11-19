"""
GreenGrid Root URL Configuration.
All API endpoints mounted under /api/v1/.
"""

from pathlib import Path

from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import RedirectView
from django.views.static import serve as static_serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / 'frontend'


def frontend(request, path=''):
    """Serve the single-page web client from /frontend (same origin => session + CSRF just work)."""
    return static_serve(request, path or 'index.html', document_root=FRONTEND_DIR)


urlpatterns = [
    path('', RedirectView.as_view(url='/app/', permanent=False)),
    re_path(r'^app/(?P<path>.*)$', frontend, name='frontend'),
    path('admin/', admin.site.urls),

    # OpenAPI Schema & Interactive Swagger UI Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 routes
    path('api/v1/', include('core.urls')),
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/facilities/', include('facilities.urls')),
    path('api/v1/ingestion/', include('ingestion.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
    path('api/v1/billing/', include('billing.urls')),
    path('api/v1/benchmarking/', include('benchmarking.urls')),
    path('api/v1/recommendations/', include('recommendations.urls')),
    path('api/v1/renewables/', include('renewables.urls')),
]
